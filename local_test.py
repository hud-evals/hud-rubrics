"""Local test script for the SEC EDGAR rubrics environment.

Prerequisites:
1. Set environment variables: EDGAR_IDENTITY, EXA_API_KEY, OPENAI_API_KEY
2. Run the backend: uvicorn environment.server:app --port 8000
3. Run this script: python local_test.py
"""
import asyncio

import hud
from hud.agents import OpenAIChatAgent
from hud.settings import settings
from openai import AsyncOpenAI

from env import env

# Use HUD inference gateway - see all models at https://hud.ai/models
client = AsyncOpenAI(base_url="https://inference.hud.ai", api_key=settings.api_key)


async def test_tools_standalone():
    """Test environment tools directly."""
    print("=== Test 1: Standalone Tools ===")

    async with env:
        print(f"Tools: {[t.name for t in env.as_tools()]}")

        # Test company search
        results = await env.call_tool("search_company", query="AAPL")
        print(f"Company search results: {results}")


async def test_simple_query_manual():
    """Test simple query scenario with manual OpenAI calls."""
    print("\n=== Test 2: Simple Query (Manual Agent Loop) ===")

    task = env(
        "simple-query",
        prompt="What was Apple's total revenue in FY2023 according to their 10-K filing?",
        answer_includes=["383", "billion"],
    )

    async with hud.eval(task) as ctx:
        messages = [{"role": "user", "content": ctx.prompt}]

        while True:
            response = await client.chat.completions.create(
                model="gpt-4o",  # https://hud.ai/models
                messages=messages,
                tools=ctx.as_openai_chat_tools(),
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                break

            messages.append(msg)
            for tc in msg.tool_calls:
                result = await ctx.call_tool(tc)
                messages.append(result)


async def test_analyze_filing_scenario():
    """Test analyze-filing scenario with rubric evaluation."""
    print("\n=== Test 3: Analyze Filing Scenario ===")

    task = env(
        "analyze-filing",
        prompt="Based on Oracle's FY2024 10-K, what were the operating expenses in 2024, broken out by segment? Which segment had the highest and lowest?",
        rubric=[
            {"requirement": "States Cloud Services segment operating expenses", "weight": 10},
            {"requirement": "States Hardware segment operating expenses", "weight": 10},
            {"requirement": "States Services segment operating expenses", "weight": 10},
            {"requirement": "Correctly identifies highest and lowest segments", "weight": 10},
            {"requirement": "References Oracle's FY2024 Form 10-K", "weight": 8},
        ],
    )

    async with hud.eval(task) as ctx:
        agent = OpenAIChatAgent.create(model="gpt-4o")  # https://hud.ai/models
        await agent.run(ctx, max_steps=15)


async def main():
    await test_tools_standalone()
    # Uncomment to run scenarios:
    # await test_simple_query_manual()
    # await test_analyze_filing_scenario()


if __name__ == "__main__":
    asyncio.run(main())

"""Local test script for the SEC EDGAR environment.

Run the backend first: uvicorn environment.server:app --port 8000

Usage:
    python local_test.py --list
    python local_test.py --task oracle_opex
    python local_test.py --task valero_margins --model gpt-4o
    python local_test.py --task exxon_efficient --max-steps 15
"""

import argparse
import asyncio

import hud
from hud.agents import OpenAIChatAgent

from tasks import ALL_TASKS


async def main():
    available = sorted(ALL_TASKS)

    parser = argparse.ArgumentParser(description="Run agent against a SEC EDGAR task")
    parser.add_argument("--task", default="oracle_opex", choices=available)
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument(
        "--list", action="store_true", help="List available tasks and exit"
    )
    args = parser.parse_args()

    if args.list:
        for name in available:
            task = ALL_TASKS[name]
            print(f"  {name:25s}  slug={task.slug}  scenario={task.scenario}")
        return

    task = ALL_TASKS[args.task]

    print(f"=== {args.task} ({args.model}) ===")
    async with hud.eval(task, name=args.task) as ctx:
        agent = OpenAIChatAgent.create(model=args.model)
        await agent.run(ctx, max_steps=args.max_steps)
        print(f"Reward: {ctx.reward}")


if __name__ == "__main__":
    asyncio.run(main())

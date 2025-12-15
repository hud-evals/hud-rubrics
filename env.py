"""SEC EDGAR Rubrics Environment - Financial research with rubric-based evaluation.

This demonstrates:
- @env.tool() for SEC EDGAR research tools
- @env.scenario() for rubric-based evaluation flows
- Integration with SEC EDGAR for filing access
- Web search fallback via Exa API
"""
import logging
import os
import sys
from typing import Any

import httpx
from hud import Environment

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
    force=True,
)
for logger_name in ["httpx", "httpcore"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Backend connection
BACKEND_URL = os.getenv("ENV_SERVER_URL", "http://localhost:8000")
http_client = httpx.AsyncClient(base_url=BACKEND_URL, timeout=60.0)

env = Environment(name="sec-rubrics")


# =============================================================================
# TOOLS
# =============================================================================


@env.tool()
async def search_company(query: str) -> list[dict[str, str]]:
    """Search for a company by ticker symbol or name."""
    resp = await http_client.post("/search_company", json={"query": query})
    resp.raise_for_status()
    return resp.json()


@env.tool()
async def get_filings(
    ticker: str | None = None,
    form_type: str | None = None,
    limit: int = 10,
    cutoff_date: str | None = None,
) -> list[dict[str, Any]]:
    """Get SEC filings for a company or globally.
    
    Args:
        ticker: Optional ticker or CIK. If omitted, returns global recent filings.
        form_type: Optional form filter (e.g., "10-K", "10-Q", "8-K").
        limit: Max number of results.
        cutoff_date: Optional date string (YYYY-MM-DD). Only filings on or after this date.
    """
    resp = await http_client.post(
        "/get_filings",
        json={
            "ticker": ticker,
            "form_type": form_type,
            "limit": limit,
            "cutoff_date": cutoff_date,
        },
    )
    resp.raise_for_status()
    return resp.json()


@env.tool()
async def get_filing_content(filing_url: str) -> str:
    """Get the full text content of a specific SEC filing from its URL."""
    resp = await http_client.post("/get_filing_content", json={"filing_url": filing_url})
    resp.raise_for_status()
    return resp.json().get("content", "")


@env.tool()
async def get_financial_data(ticker: str, accession_number: str) -> dict[str, Any]:
    """Extract financial statements and key metrics from a 10-K or 10-Q filing."""
    resp = await http_client.post(
        "/get_financial_data",
        json={"ticker": ticker, "accession_number": accession_number},
    )
    resp.raise_for_status()
    return resp.json()


@env.tool()
async def get_segment_data(ticker: str, accession_number: str) -> dict[str, Any]:
    """Extract segment-level financial data from a 10-K or 10-Q filing."""
    resp = await http_client.post(
        "/get_segment_data",
        json={"ticker": ticker, "accession_number": accession_number},
    )
    resp.raise_for_status()
    return resp.json()


@env.tool()
async def get_filing_sections(ticker: str, accession_number: str) -> dict[str, Any]:
    """Get specific sections from a 10-K or 10-Q filing (Business, Risk Factors, MD&A)."""
    resp = await http_client.post(
        "/get_filing_sections",
        json={"ticker": ticker, "accession_number": accession_number},
    )
    resp.raise_for_status()
    return resp.json()


@env.tool()
async def web_search(query: str) -> list[dict[str, str]]:
    """Search the web using Exa API (fallback for non-SEC data)."""
    resp = await http_client.post("/web_search", json={"query": query})
    resp.raise_for_status()
    return resp.json()


@env.tool()
async def web_fetch(url: str) -> str:
    """Fetch and extract content from a web URL."""
    resp = await http_client.post("/web_fetch", json={"url": url})
    resp.raise_for_status()
    return resp.json().get("content", "")


@env.tool()
async def answer(final_answer: str) -> str:
    """Submit your final research answer. Call this when you have completed your analysis."""
    await http_client.post("/answer", json={"final_answer": final_answer})
    return f"Answer submitted: {final_answer[:200]}..."


# =============================================================================
# SCENARIOS
# =============================================================================


@env.scenario("analyze-filing")
async def analyze_filing(
    prompt: str,
    rubric: list[dict[str, str | float]],
    system_prompt: str | None = None,
) -> Any:
    """Analyze SEC filings with rubric-based evaluation.
    
    Args:
        prompt: The analysis question/task for the agent.
        rubric: List of rubric items with "requirement" and "weight" keys.
        system_prompt: Optional system prompt for context (included in prompt).
    """
    # Setup: reset state
    await http_client.post("/setup")
    logger.info("Analyze filing scenario started")
    
    # Build the prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    else:
        full_prompt = f"""You are an AI finance research assistant specializing in public company filings analysis.

{prompt}

Use the available tools to search for companies, retrieve SEC filings, extract financial data, and analyze the information. When you have completed your research, call the answer tool with your final response."""
    
    # Yield prompt
    _ = yield full_prompt
    
    # Evaluate: use rubric grading
    resp = await http_client.post("/evaluate", json={"rubric": rubric})
    result = resp.json()
    
    reward = result.get("reward", 0.0)
    info = result.get("info", {})
    
    logger.info("Rubric evaluation: reward=%.2f, report=%s", reward, info.get("report", [])[:2])
    yield reward


@env.scenario("simple-query")
async def simple_query(
    prompt: str,
    answer_includes: str | list[str],
) -> Any:
    """Simple SEC filing query with string matching evaluation.
    
    Args:
        prompt: The research question.
        answer_includes: String or list of strings that must appear in the answer.
    """
    # Setup: reset state
    await http_client.post("/setup")
    logger.info("Simple query scenario: %s", prompt[:100])
    
    # Build the prompt
    full_prompt = f"""You are an AI finance research assistant specializing in public company filings analysis.

{prompt}

Use the available tools to find the answer. When you have completed your research, call the answer tool with your final response."""
    
    # Yield prompt
    _ = yield full_prompt
    
    # Evaluate: check if answer includes required strings
    resp = await http_client.get("/state")
    state = resp.json()
    submitted = state.get("submitted_answer", "")
    
    if not submitted:
        logger.info("No answer submitted")
        yield 0.0
        return
    
    # Normalize for comparison
    submitted_lower = submitted.strip().lower()
    
    # Handle both string and list - check if ANY match
    if isinstance(answer_includes, str):
        candidates = [answer_includes]
    else:
        candidates = answer_includes
    
    # Check if any of the candidate strings are present
    found = any(candidate.lower() in submitted_lower for candidate in candidates)
    reward = 1.0 if found else 0.0
    
    logger.info("Simple query result: found=%s, reward=%.2f", found, reward)
    yield reward


# =============================================================================
# LIFECYCLE
# =============================================================================


@env.initialize
async def init() -> None:
    """Check backend health on startup."""
    resp = await http_client.get("/health")
    resp.raise_for_status()
    logger.info("Backend health check passed")


@env.shutdown
async def cleanup() -> None:
    """Close HTTP client on shutdown."""
    await http_client.aclose()


if __name__ == "__main__":
    env.run(transport="stdio")

"""MCP server for SEC EDGAR research environment."""

from typing import List, Dict, Any, Optional
import httpx
import os
import sys
import logging

from hud.tools.types import EvaluationResult
from hud import Environment

# Configure logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
    force=True,  # Force all loggers to use stderr
)

# Environment instance
env = Environment(name="sec-rubrics")

# Environment server URL (backend)
ENV_SERVER_URL = os.getenv("ENV_SERVER_URL", "http://localhost:8000")

# Shared HTTP client to talk to the environment
http_client = httpx.AsyncClient(
    base_url=ENV_SERVER_URL,
    timeout=60.0,  # Increased timeout for SEC EDGAR operations
    headers={"User-Agent": "HUD-SEC-Rubrics-Controller/1.0"},
)


@env.initialize
async def init():
    # Ensure environment server is reachable
    await http_client.get("/health")


@env.shutdown
async def cleanup():
    await http_client.aclose()


@env.tool()
async def setup() -> str:
    await http_client.post("/setup")
    return "Environment setup complete"


@env.tool()
async def search_company(query: str) -> List[Dict[str, str]]:
    resp = await http_client.post("/search_company", json={"query": query})
    return resp.json()


@env.tool()
async def get_filings(
    ticker: Optional[str] = None,
    form_type: Optional[str] = None,
    limit: int = 10,
    cutoff_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    resp = await http_client.post(
        "/get_filings",
        json={
            "ticker": ticker,
            "form_type": form_type,
            "limit": limit,
            "cutoff_date": cutoff_date,
        },
    )
    return resp.json()


@env.tool()
async def get_filing_content(filing_url: str) -> str:
    resp = await http_client.post("/get_filing_content", json={"filing_url": filing_url})
    data = resp.json()
    return data.get("content", "")


@env.tool()
async def get_financial_data(ticker: str, accession_number: str) -> Any:
    """Extract financial statements and key metrics from a 10-K or 10-Q filing."""
    resp = await http_client.post(
        "/get_financial_data",
        json={
            "ticker": ticker,
            "accession_number": accession_number,
        },
    )
    return resp.json()


@env.tool()
async def get_segment_data(ticker: str, accession_number: str) -> Any:
    """Extract segment-level financial data from a 10-K or 10-Q filing."""
    resp = await http_client.post(
        "/get_segment_data",
        json={
            "ticker": ticker,
            "accession_number": accession_number,
        },
    )
    return resp.json()


@env.tool()
async def answer(final_answer: str) -> str:
    await http_client.post("/answer", json={"final_answer": final_answer})
    return f"Answer submitted: {final_answer}"


@env.tool()
async def evaluate(rubric: list[dict[str, str | float]]) -> EvaluationResult:
    try:
        resp = await http_client.post("/evaluate", json={"rubric": rubric})
        resp.raise_for_status()
        return EvaluationResult(**resp.json())
    except Exception as e:
        logging.error("Evaluation tool error: %s", e)
        return EvaluationResult(
            reward=0.0, done=True, content=f"Evaluation error: {e}", isError=True
        )


@env.tool()
async def get_filing_sections(ticker: str, accession_number: str) -> Any:
    resp = await http_client.post(
        "/get_filing_sections",
        json={
            "ticker": ticker,
            "accession_number": accession_number,
        },
    )
    return resp.json()


@env.tool()
async def web_search(query: str) -> List[Dict[str, str]]:
    resp = await http_client.post("/web_search", json={"query": query})
    return resp.json()


@env.tool()
async def web_fetch(url: str) -> str:
    resp = await http_client.post("/web_fetch", json={"url": url})
    data = resp.json()
    return data.get("content", "")


if __name__ == "__main__":
    env.run()

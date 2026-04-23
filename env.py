"""SEC EDGAR Research Environment.

Provides SEC filing research tools and evaluation scenarios for
testing AI agents on financial analysis tasks.

Demonstrates:
- @env.tool() for agent-facing tools (SEC EDGAR, web search)
- @env.scenario() for evaluation lifecycle (setup -> prompt -> evaluate)
- Multiple evaluation patterns: rubric-graded, exact-lookup, multi-filing, efficiency
"""

import logging
import os
import sys
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional

import httpx
from rubric import Rubric

from hud import Environment
from hud.tools.types import EvaluationResult, SubScore

# Configure logging to stderr (MCP uses stdout for communication)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
    force=True,
)
for logger_name in ["httpx", "httpcore"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Backend configuration
BACKEND_PORT = os.getenv("ENV_SERVER_PORT", "8000")
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"

# HTTP client for backend communication
http_client = httpx.AsyncClient(
    base_url=BACKEND_URL,
    timeout=60.0,
    headers={"User-Agent": "HUD-SEC-Rubrics/1.0"},
)

# Create the environment
env = Environment(name="sec-edgar")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@env.tool()
async def search_company(query: str) -> List[Dict[str, str]]:
    """Search for a company by ticker or name on SEC EDGAR."""
    resp = await http_client.post("/search_company", json={"query": query})
    return resp.json()


@env.tool()
async def get_filings(
    ticker: Optional[str] = None,
    form_type: Optional[str] = None,
    limit: int = 10,
    cutoff_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get filings for a company. Filter by ticker, form_type (10-K, 10-Q, 8-K, DEF 14A), limit, cutoff_date (YYYY-MM-DD)."""
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
    """Get the text content of a specific SEC filing."""
    resp = await http_client.post(
        "/get_filing_content", json={"filing_url": filing_url}
    )
    return resp.json().get("content", "")


@env.tool()
async def get_financial_data(ticker: str, accession_number: str) -> Any:
    """Extract financial statements (income, balance sheet, cash flow) from a 10-K or 10-Q filing."""
    resp = await http_client.post(
        "/get_financial_data",
        json={"ticker": ticker, "accession_number": accession_number},
    )
    return resp.json()


@env.tool()
async def get_segment_data(ticker: str, accession_number: str) -> Any:
    """Extract segment-level financial data from a 10-K or 10-Q filing."""
    resp = await http_client.post(
        "/get_segment_data",
        json={"ticker": ticker, "accession_number": accession_number},
    )
    return resp.json()


@env.tool()
async def get_filing_sections(ticker: str, accession_number: str) -> Any:
    """Get specific sections (business, risk factors, MD&A) from a 10-K or 10-Q filing."""
    resp = await http_client.post(
        "/get_filing_sections",
        json={"ticker": ticker, "accession_number": accession_number},
    )
    return resp.json()


@env.tool()
async def web_search(query: str) -> List[Dict[str, str]]:
    """Search the web for financial information."""
    resp = await http_client.post("/web_search", json={"query": query})
    return resp.json()


@env.tool()
async def web_fetch(url: str) -> str:
    """Fetch and extract content from a web page."""
    resp = await http_client.post("/web_fetch", json={"url": url})
    return resp.json().get("content", "")


@env.tool()
async def answer(final_answer: str) -> str:
    """Submit your final answer to the research question. You must call this when done."""
    await http_client.post("/answer", json={"final_answer": final_answer})
    return f"Answer submitted ({len(final_answer)} chars)"


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@env.scenario("rubric-research")
async def rubric_research(
    prompt: str,
    rubric: list[dict[str, Any]],
) -> AsyncGenerator[Any, None]:
    """Research question evaluated with weighted rubric criteria.

    The rubric package grades the submitted answer against each requirement.
    Returns EvaluationResult with per-criterion SubScores.
    """
    await http_client.post("/setup")

    yield prompt

    # Evaluate phase
    state = (await http_client.get("/get_state")).json()
    submitted = state.get("submitted_answer")

    if not submitted:
        yield EvaluationResult(
            reward=0.0,
            done=True,
            content="No answer submitted. Call the answer tool with your final answer.",
        )
        return

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for rubric grading")

    rubric_obj = Rubric.from_dict(rubric)
    evaluation = await rubric_obj.grade(submitted)
    reward = evaluation.score / 100.0

    subscores = []
    if evaluation.report:
        total_weight = sum(abs(r.weight) for r in evaluation.report if r.weight > 0)
        for r in evaluation.report:
            if total_weight > 0:
                norm_weight = abs(r.weight) / total_weight
            else:
                norm_weight = 1.0 / len(evaluation.report)
            value = 1.0 if r.verdict == "MET" else 0.0
            subscores.append(
                SubScore(
                    name=r.requirement[:60],
                    weight=-norm_weight if r.weight < 0 else norm_weight,
                    value=value,
                )
            )

    yield EvaluationResult(
        reward=reward,
        done=True,
        content=f"Rubric score: {evaluation.score}/100",
        subscores=subscores if subscores else None,
        info={
            "report": [r.model_dump() for r in evaluation.report]
            if evaluation.report
            else [],
            "search_count": state.get("search_count", 0),
            "fetch_count": state.get("fetch_count", 0),
        },
    )


@env.scenario("exact-lookup")
async def exact_lookup(
    prompt: str,
    expected_values: dict[str, str],
    case_sensitive: bool = False,
) -> AsyncGenerator[Any, None]:
    """Simple data extraction with exact-match verification.

    Checks whether each expected value appears in the submitted answer.
    Evaluation: partial credit with per-field SubScores.
    """
    await http_client.post("/setup")

    yield prompt

    state = (await http_client.get("/get_state")).json()
    submitted = state.get("submitted_answer", "")

    if not submitted:
        yield EvaluationResult(
            reward=0.0,
            done=True,
            content="No answer submitted.",
        )
        return

    check_text = submitted if case_sensitive else submitted.lower()
    matched = 0
    n = len(expected_values)
    weight = 1.0 / n if n > 0 else 1.0
    subscores = []

    for field_name, expected in expected_values.items():
        target = expected if case_sensitive else expected.lower()
        found = target in check_text
        if found:
            matched += 1
        subscores.append(
            SubScore(name=field_name, weight=weight, value=1.0 if found else 0.0)
        )

    reward = matched / n if n > 0 else 0.0

    yield EvaluationResult(
        reward=reward,
        done=True,
        content=f"Matched {matched}/{n} expected values",
        subscores=subscores,
    )


@env.scenario("multi-filing-analysis")
async def multi_filing_analysis(
    prompt: str,
    criteria_groups: list[dict[str, Any]],
) -> AsyncGenerator[Any, None]:
    """Multi-filing analysis with grouped criteria producing weighted SubScores.

    criteria_groups: list of {"name": str, "weight": float, "rubric": list[dict]}
    Each group is graded independently via rubric, producing a separate SubScore.
    """
    await http_client.post("/setup")

    yield prompt

    state = (await http_client.get("/get_state")).json()
    submitted = state.get("submitted_answer")

    if not submitted:
        yield EvaluationResult(
            reward=0.0,
            done=True,
            content="No answer submitted.",
        )
        return

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for rubric grading")

    subscores = []
    total_reward = 0.0

    for group in criteria_groups:
        group_name = group["name"]
        group_weight = group["weight"]
        group_rubric = group["rubric"]

        rubric_obj = Rubric.from_dict(group_rubric)
        evaluation = await rubric_obj.grade(submitted)
        group_score = evaluation.score / 100.0

        subscores.append(
            SubScore(name=group_name, weight=group_weight, value=group_score)
        )
        total_reward += group_weight * group_score

    yield EvaluationResult(
        reward=total_reward,
        done=True,
        content=f"Multi-filing score: {total_reward:.2f}",
        subscores=subscores,
    )


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------


@env.initialize
async def init() -> None:
    """Validate required env vars and check backend health on startup."""
    required = ("EDGAR_IDENTITY", "EXA_API_KEY", "OPENAI_API_KEY")
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        logger.warning(f"Missing environment variables: {', '.join(missing)}")
    if len(missing) == len(required):
        raise RuntimeError(f"No environment variables set — need at least one of: {', '.join(required)}")
    (await http_client.get("/health")).raise_for_status()


@env.shutdown
async def cleanup() -> None:
    """Close HTTP client on shutdown."""
    await http_client.aclose()


if __name__ == "__main__":
    env.run(transport="stdio")

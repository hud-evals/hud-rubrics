# SEC EDGAR Rubrics Environment

A HUD environment for SEC filing research with rubric-based evaluation, powered by the SEC EDGAR database and [The LLM Data Company's rubric package](https://github.com/The-LLM-Data-Company/rubric/).

## 1. Deploy to Platform

If you haven't already, connect this repo to hud.ai:

1. Push to GitHub
2. Go to [hud.ai](https://hud.ai) → **New** → **Environment**
3. Connect your GitHub repo
4. Set required environment variables (see Configuration below)
5. Your environment builds automatically on each push

Once deployed, your environment is accessible by its slug (e.g., `my-org/sec-rubrics`).

## 2. Define Tools and Scenarios

Tools are functions agents can call. Scenarios define the evaluation lifecycle.

### Available Tools

| Tool | Description |
|------|-------------|
| `search_company` | Search for a company by ticker or name |
| `get_filings` | Get SEC filings (10-K, 10-Q, 8-K, etc.) |
| `get_filing_content` | Fetch full text content of a filing |
| `get_financial_data` | Extract financial statements from 10-K/10-Q |
| `get_segment_data` | Extract segment-level financial data |
| `get_filing_sections` | Get specific sections (Business, Risk Factors, MD&A) |
| `web_search` | Web search via Exa API (fallback) |
| `web_fetch` | Fetch web content via Exa API |
| `answer` | Submit final research answer |

### Available Scenarios

| Scenario | Description |
|----------|-------------|
| `analyze-filing` | Analyze SEC filings with rubric-based evaluation |
| `simple-query` | Simple SEC query with string matching evaluation |

## 3. Create Tasks from Scenarios

Tasks are scenario instances with specific arguments.

**In Code:**
```python
tasks = [
    env("simple-query",
        prompt="What was Apple's total revenue in FY2023?",
        answer_includes=["383", "billion"]
    ),
    env("analyze-filing",
        prompt="Analyze Valero's refining margins...",
        rubric=[
            {"requirement": "States FY2023 margin", "weight": 10},
            {"requirement": "References 10-K filing", "weight": 10},
        ]
    ),
]
```

**From JSON:**
```json
[
  {
    "env": {"name": "my-org/sec-rubrics"},
    "scenario": "simple-query",
    "args": {
      "prompt": "What was Apple's total revenue in FY2023?",
      "answer_includes": ["383", "billion"]
    }
  }
]
```

**On Platform:**
After deploying, create tasks from your scenarios on hud.ai. Access them by slug:
```python
from hud.datasets import load_tasks
tasks = load_tasks("my-org/sec-rubrics-tasks")
```

## 4. Run Evaluations

Run tasks and see results on hud.ai. You have three options:

**On Platform:**
Run evaluations at scale directly on [hud.ai](https://hud.ai) with parallel execution and automatic tracing.

**CLI:**
```bash
hud eval ./remote_tasks.json --model gpt-4o --remote  # https://hud.ai/models
hud eval my-org/sec-rubrics --model gpt-4o --remote --group 5
```

**Python:**
```python
import hud
from hud.agents import OpenAIChatAgent  # See all models: https://hud.ai/models

async with hud.eval(tasks) as ctx:
    agent = OpenAIChatAgent.create(model="gpt-4o")  # Uses inference.hud.ai
    await agent.run(ctx, max_steps=20)

# Results are automatically traced to hud.ai
```

**With Variants (A/B Testing):**

```python
tasks = [
    env("simple-query", prompt="What was Apple's total revenue in FY2023?", answer_includes=["383", "billion"]),
    env("analyze-filing", prompt="Analyze Tesla's risk factors...", rubric=[...]),
]
variants = {"model": ["gpt-4o-mini", "gpt-4o"]}

async with hud.eval(tasks, variants=variants, group=2) as ctx:
    agent = OpenAIChatAgent.create(model=ctx.variants["model"])
    await agent.run(ctx, max_steps=20)
```

## Configuration

### Required Variables

| Variable | Description |
|----------|-------------|
| `EDGAR_IDENTITY` | Your identity for SEC EDGAR (e.g., `"Your Name your.email@example.com"`) |
| `OPENAI_API_KEY` | For rubric evaluation autograders |

### Optional Variables

| Variable | Description |
|----------|-------------|
| `EXA_API_KEY` | For web search and content fetching |
| `ANTHROPIC_API_KEY` | For Claude-based autograders |
| `HUD_API_KEY` | For HUD inference gateway and tracing |

## Local Development

```bash
# Set environment variables
export EDGAR_IDENTITY="Your Name your.email@example.com"
export EXA_API_KEY=your-exa-key
export OPENAI_API_KEY=your-openai-key

# Run backend
uvicorn environment.server:app --port 8000

# In another terminal, test locally
python local_test.py

# Test with remote tasks
python remote_test.py
```

Or use `hud dev`:
```bash
hud dev . --build
```

> ⚠️ **Local runs one task at a time.** For parallel execution with multiple tasks, push and run remotely:
> ```bash
> hud push
> hud eval ./remote_tasks.json --model gpt-4o --remote --group 5
> ```

## Structure

```
hud-rubrics/
├── env.py              # Environment definition (tools + scenarios)
├── environment/        # Backend service
│   ├── server.py       # FastAPI with SEC EDGAR + Exa integration
│   ├── edgar_utils.py  # SEC EDGAR utilities
│   ├── exa_utils.py    # Exa API utilities
│   └── pyproject.toml  # Backend dependencies
├── server/             # Legacy MCP server (optional)
├── local_test.py       # Local testing examples
├── remote_test.py      # Platform integration examples
├── remote_tasks.json   # Task definitions
├── Dockerfile.hud
├── pyproject.toml
├── .env.example
└── .gitignore
```

## Dependencies

- **edgartools**: Python library for accessing SEC EDGAR data
- **rubric**: LLM Data Company's rubric evaluation package
- **fastapi**: Web framework for the backend
- **httpx**: HTTP client for API calls

## Documentation

Full documentation: [docs.hud.ai](https://docs.hud.ai)

## Acknowledgments

* [EdgarTools](https://github.com/dgunning/edgartools) - Python library to access SEC EDGAR
* [SEC EDGAR MCP](https://github.com/stefanoamorelli/sec-edgar-mcp) - Rich OSS SEC MCP server
* [The LLM Data Company](https://llmdata.com) - Rubric-based evaluation

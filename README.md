# SEC EDGAR Rubrics Environment

An SEC filing research environment powered by the SEC EDGAR database. Agents use EDGAR tools and web search to research companies, then answers are graded with rubric-based evaluation from [The LLM Data Company](https://llmdata.com).

## Quick Start

```bash
uv sync                # install dependencies
hud deploy .           # build and deploy to HUD platform
hud sync tasks <name>  # upload task definitions
```

## Scenarios

| Scenario | Key Args | Description |
|----------|----------|-------------|
| `rubric-research` | `question`, `rubric` | Research a question, graded against a weighted rubric |
| `exact-lookup` | `question`, `expected_fields` | Look up specific values with field-matching (partial credit) |
| `multi-filing-analysis` | `question`, `criteria_groups` | Grouped criteria across multiple filings with weighted sub-scores |

## Configuration

**Build secret (required):**
- `EDGAR_IDENTITY` — your SEC EDGAR identity (format: `"Name email@example.com"`)

**Runtime secrets:**
- `EXA_API_KEY` — for web search/fetch tools
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` — for rubric autograding

## Documentation

To learn more about tasks, evaluations, and running at scale see the [full docs](https://docs.hud.ai).

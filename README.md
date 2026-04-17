# SEC EDGAR Rubrics Environment

An SEC filing research environment powered by the SEC EDGAR database. Agents use EDGAR tools and web search to research companies, then answers are graded with rubric-based evaluation from [The LLM Data Company](https://llmdata.com).

## Setup

```bash
uv sync
cp .env.example .env                # Injected into the deployed container for grading
hud set HUD_API_KEY=your-key-here   # CLI auth, get one at hud.ai/project/api-keys
```

## Deploy & Run

```bash
hud deploy . --build-arg EDGAR_IDENTITY=$EDGAR_IDENTITY   # deploy the environment (once)
hud sync tasks <taskset-name>                              # push tasks to a taskset (fast, re-run on every task change)
hud eval <taskset-name> --remote --full
```

**Iteration loop:** `hud deploy` is the slow step — run it once. After that, edit `tasks.py` and re-run `hud sync tasks` (takes seconds). Only redeploy when `env.py` or the Dockerfile changes.

See [Deploy & Go Remote](https://docs.hud.ai/building/running-at-scale) for deploy flags, secrets, and auto-deploy options.

## Scenarios

| Scenario | Key Args | Description |
|----------|----------|-------------|
| `rubric-research` | `question`, `rubric` | Research a question, graded against a weighted rubric |
| `exact-lookup` | `question`, `expected_fields` | Look up specific values with field-matching (partial credit) |
| `multi-filing-analysis` | `question`, `criteria_groups` | Grouped criteria across multiple filings with weighted sub-scores |

## Configuration

**Build arg (required):**
- `EDGAR_IDENTITY` — your SEC EDGAR identity (format: `"Name email@example.com"`)

**Runtime secrets:**
- `EXA_API_KEY` — for web search/fetch tools
- `OPENAI_API_KEY` — for rubric autograding

## Documentation

To learn more about tasks, evaluations, and running at scale see the [full docs](https://docs.hud.ai).

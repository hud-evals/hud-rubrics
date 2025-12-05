# SEC EDGAR Rubrics Environment

SEC filing research environment powered by the SEC EDGAR database for accessing company filings and financial data, with rubric-based evaluation for structured grading provided by [The LLM Data Company](https://llmdata.com).

## Quick Start

```bash
export EDGAR_IDENTITY="Your Name your.email@example.com"
export EXA_API_KEY="your-exa-key" # optional, for web search
export ANTHROPIC_API_KEY="your-anthropic-key" # only if using an Anthropic model
export OPENAI_API_KEY="your-openai-key"

# Build the Docker image
hud build

# Start hot-reload development server
hud dev

# Run the sample tasks
hud eval tasks.json --max-steps 25
```

## Deploy

When you're ready to use this environment in production:

1. Push your code to GitHub
2. Connect your repo at [hud.ai](https://hud.ai/environments/new)
3. Builds will trigger automatically on each push

## Tools

### SEC EDGAR

- **setup()** - Initialize environment
- **search_company(query)** - Search by ticker or name
- **get_filings(ticker?, form_type?, limit?, cutoff_date?)** - Get SEC filings
- **get_filing_content(filing_url)** - Fetch full filing text
- **get_financial_data(ticker, accession_number)** - Extract financial statements
- **get_segment_data(ticker, accession_number)** - Extract segment-level data
- **get_filing_sections(ticker, accession_number)** - Extract specific sections

### Web Search (Optional)

- **web_search(query)** - Search via Exa API
- **web_fetch(url)** - Fetch web content

### Evaluation

- **answer(final_answer)** - Submit research answer
- **evaluate(rubric)** - Grade answer using weighted rubric

## Acknowledgments

* [EdgarTools](https://github.com/dgunning/edgartools) - Python library to access SEC EDGAR
* [SEC EDGAR MCP](https://github.com/stefanoamorelli/sec-edgar-mcp) - Rich OSS SEC MCP server

## Learn More

For complete documentation on building environments and running evaluations, visit [docs.hud.ai](https://docs.hud.ai).

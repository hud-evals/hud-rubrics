FROM python:3.11-slim

# Validate required build arguments early (fail fast)
ARG EDGAR_IDENTITY
RUN test -n "$EDGAR_IDENTITY" || (echo "ERROR: EDGAR_IDENTITY build arg is required (format: 'Your Name email@example.com')" && exit 1)

WORKDIR /app

# Install git for dependency installation
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy and install all dependencies
COPY pyproject.toml ./
COPY environment/pyproject.toml ./environment/
RUN pip install --no-cache-dir . ./environment

# Copy source code
COPY environment/ ./environment/
COPY env.py ./
COPY tasks.py ./

ENV ENV_SERVER_PORT=8000
ENV PYTHONPATH=/app
ENV EDGAR_IDENTITY=$EDGAR_IDENTITY

# Start environment server in background, then run MCP environment with stdio
CMD ["sh", "-c", "uvicorn environment.server:app --host 0.0.0.0 --port $ENV_SERVER_PORT --log-level warning --reload >&2 & sleep 0.5 && exec hud dev env:env --stdio"]

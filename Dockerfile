# --- Stage 1: Build ---
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Cache dependency installation
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy source and install project
COPY src/ ./src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    find .venv -type d -name "__pycache__" -exec rm -rf {} +


# --- Stage 2: Runtime ---
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8080 \
    MLFLOW_SERVER_ENABLE_JOB_EXECUTION=false \
    MLFLOW_SERVER_JOB_ALLOWLIST="" \
    OTEL_SERVICE_NAME=ceramicraft-product-agent \
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true \
    OTEL_PYTHON_LOG_CORRELATION=true

WORKDIR /app

# Security: non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -s /sbin/nologin appuser

# Copy built artifacts from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src

USER appuser

EXPOSE 8080

# Launch via opentelemetry-instrument to auto-inject traces/metrics/logs
# into OTLP exporter (OTEL_EXPORTER_OTLP_ENDPOINT env var configured at deploy time).
CMD ["opentelemetry-instrument", "python", "-m", "ceramicraft_product_agent.app"]

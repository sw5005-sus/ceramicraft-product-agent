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
    uv sync --frozen --no-dev


# --- Stage 2: Runtime ---
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8001

WORKDIR /app

# Security: non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -s /sbin/nologin appuser

# Copy built artifacts from builder
COPY --from=builder /app /app

RUN chmod -R 555 /app && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8001

CMD ["python", "-m", "ceramicraft_product_agent.app"]

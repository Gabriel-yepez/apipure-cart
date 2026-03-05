# ──────────────────────────────────────────────
# Stage 1: builder — install deps with UV
# ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml README.md ./

# Create virtual environment and install dependencies only
RUN uv venv && uv pip install -r pyproject.toml

# ──────────────────────────────────────────────
# Stage 2: runtime
# ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY app/ ./app/

# Make sure the venv is on PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

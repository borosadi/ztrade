# Multi-stage Dockerfile for Ztrade Trading System
# Optimized for both development and production use

# ============================================================================
# Stage 1: Base Python image with uv
# ============================================================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /app

# ============================================================================
# Stage 2: Dependencies
# ============================================================================
FROM base as dependencies

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies with uv
RUN uv sync --frozen

# ============================================================================
# Stage 3: Development
# ============================================================================
FROM base as development

# Copy dependencies from previous stage
COPY --from=dependencies /app/.venv /app/.venv

# Copy application code
COPY . .

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN useradd -m -u 1000 ztrade && \
    chown -R ztrade:ztrade /app

USER ztrade

# Expose ports
EXPOSE 8501 5555

# Default command (can be overridden)
CMD ["uv", "run", "ztrade", "--help"]

# ============================================================================
# Stage 4: Production
# ============================================================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only virtual environment and application code
COPY --from=dependencies /app/.venv /app/.venv
COPY --from=development /app /app

# Create non-root user
RUN useradd -m -u 1000 ztrade && \
    chown -R ztrade:ztrade /app

USER ztrade

# Expose ports
EXPOSE 8501 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["uv", "run", "ztrade", "--help"]

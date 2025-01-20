# Stage 1: Base Python image with common dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mcsuser

# Create necessary directories with proper permissions
RUN mkdir -p /app/backend /app/shared \
    /app/backend/logs \
    /app/backend/data \
    /app/backend/config \
    /app/backend/data/powders \
    /app/backend/data/sequences \
    /app/backend/data/patterns \
    /app/backend/data/nozzles \
    /app/backend/data/parameters \
    /app/backend/data/runs \
    && chown -R mcsuser:mcsuser /app

# Switch to non-root user
USER mcsuser

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY --chown=mcsuser:mcsuser requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Stage 2: Service-specific image
FROM base AS service

# Copy shared package
COPY --chown=mcsuser:mcsuser shared /app/shared/

# Copy backend files
COPY --chown=mcsuser:mcsuser backend /app/backend/

# Copy setup files
COPY --chown=mcsuser:mcsuser setup.py .

# Install the package
RUN pip install -e .

# Port Mapping:
# 8001: Config Service
# 8002: Communication Service
# 8003: Process Service
# 8004: Data Collection Service
EXPOSE 8001-8004

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
CMD curl -f http://localhost:8001/health || exit 1

# Command to run the application
CMD ["python", "-m", "backend.src.mcs"] 
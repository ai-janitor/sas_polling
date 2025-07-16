# =============================================================================
# DATAFIT JOB POLLING SERVICE DOCKERFILE - AMAZON LINUX 2023
# =============================================================================
# Purpose: Containerize the job polling service with queue management
# Technology: Python 3.11 with Flask/FastAPI and background workers
# Base Image: Amazon Linux 2023 (Python 3.11 pre-installed)
# =============================================================================

FROM amazonlinux:2023

# Install minimal runtime dependencies (using built-in Python 3.9)
# Note: python3-pip removed due to package conflicts - using ensurepip instead
RUN dnf update -y && dnf install -y --allowerasing \
    curl \
    shadow-utils \
    && dnf clean all

# Ensure pip is available using ensurepip
RUN python3 -m ensurepip --upgrade

# Create non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
# Create virtual environment to avoid conflicts with system packages
RUN python3 -m venv /app/venv && \
    source /app/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Reports module will be mounted via volume in docker-compose
# COPY ../reports ./reports

# Create necessary directories and set permissions
RUN mkdir -p \
    /var/log/datafit \
    /tmp/datafit/output \
    /tmp/datafit/files \
    /app/mock-data \
    /app/templates && \
    chown -R appuser:appgroup \
    /app \
    /var/log/datafit \
    /tmp/datafit && \
    chmod -R 755 /app && \
    chmod -R 777 /tmp/datafit && \
    chmod +x /app/venv/bin/python

# Switch to non-root user
USER appuser

# Expose service port (configurable)
ARG POLLING_PORT=5001
EXPOSE ${POLLING_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Production command using virtual environment
CMD ["/app/venv/bin/python", "app.py"]

# =============================================================================
# ENVIRONMENT VARIABLES:
#
# Required at runtime:
# - POLLING_PORT: Service port (default: 5001)
# - POLLING_HOST: Service host (default: 0.0.0.0)
# - POLLING_WORKERS: Number of background workers (default: 4)
# - POLLING_QUEUE_SIZE: Maximum queue size (default: 100)
# - FILE_STORAGE_PATH: Path for generated files
# - REPORTS_DATA_PATH: Path to mock data files
# - LOG_LEVEL: Logging level (default: INFO)
#
# Optional:
# - POLLING_JOB_TIMEOUT: Job execution timeout (default: 300)
# - FILE_RETENTION_DAYS: File cleanup period (default: 7)
# - RATE_LIMIT_REQUESTS: Rate limiting (default: 100)
# - ENABLE_METRICS: Prometheus metrics (default: true)
#
# Volume Mounts:
# - /tmp/datafit: Temporary file storage (should be mounted)
# - /app/mock-data: Mock data files (should be mounted)
# - /app/templates: HTML templates (should be mounted)
# - /var/log/datafit: Log files (optional mount)
#
# BUILD INSTRUCTIONS:
#
# Development build:
#   docker build -t datafit-polling:dev .
#   docker run -p 5001:5001 --env-file config.dev.env \
#     -v $(pwd)/mock-data:/app/mock-data \
#     -v $(pwd)/templates:/app/templates \
#     datafit-polling:dev
#
# Production build:
#   docker build -t datafit-polling:prod .
#   docker run -p 5001:5001 --env-file config.prod.env \
#     -v /data/mock-data:/app/mock-data \
#     -v /data/templates:/app/templates \
#     -v /data/storage:/tmp/datafit \
#     datafit-polling:prod
#
# Multi-architecture build:
#   docker buildx build --platform linux/amd64,linux/arm64 -t datafit-polling .
# =============================================================================
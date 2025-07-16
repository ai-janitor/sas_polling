# =============================================================================
# DATAFIT JOB POLLING SERVICE DOCKERFILE - AMAZON LINUX 2023
# =============================================================================
# Purpose: Containerize the job polling service with queue management
# Technology: Python 3.11 with Flask/FastAPI and background workers
# Base Image: Amazon Linux 2023 with Python 3.11
#
# STRICT REQUIREMENTS:
# - Amazon Linux 2023 base image MANDATORY
# - Multi-stage build for production optimization
# - Non-root user for security
# - Health checks for container monitoring
# - Proper signal handling for graceful shutdown
# - Configuration from environment variables
# - Support for concurrent job processing
#
# BUILD STAGES:
# 1. Dependencies installation stage
# 2. Production runtime stage
#
# SECURITY FEATURES:
# - Non-root user execution
# - Minimal attack surface
# - No unnecessary packages or tools
# - Read-only root filesystem support
# - Secure file handling for report generation
#
# CONFIGURATION:
# All configuration loaded from config.dev.env via environment variables
# =============================================================================

# Dependencies stage
FROM amazonlinux:2023 AS dependencies

# Install Python 3.11 and development tools for report generation
RUN dnf update -y && dnf install -y --allowerasing \
    python3.11 \
    python3.11-pip \
    python3.11-devel \
    gcc \
    openssl-devel \
    libffi-devel \
    curl \
    && dnf clean all

# Set Python 3.11 as default python3
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.11 1

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# =============================================================================

# Production runtime stage
FROM amazonlinux:2023 AS production

# Install runtime dependencies
RUN dnf update -y && dnf install -y --allowerasing \
    python3.11 \
    python3.11-pip \
    curl \
    shadow-utils \
    && dnf clean all

# Set Python 3.11 as default python3
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.11 1

# Create non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Install Python dependencies directly in production stage
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

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
    chmod -R 777 /tmp/datafit

# Switch to non-root user
USER appuser

# Expose service port (configurable)
ARG POLLING_PORT=5001
EXPOSE ${POLLING_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Production command with background workers
CMD ["python3", "-m", "gunicorn", \
     "--bind", "0.0.0.0:5001", \
     "--workers", "2", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "300", \
     "--keep-alive", "2", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--preload", \
     "app:app"]

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
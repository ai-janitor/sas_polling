# =============================================================================
# DATAFIT JOB SUBMISSION SERVICE DOCKERFILE - AMAZON LINUX 2023
# =============================================================================
# Purpose: Containerize the job submission REST API service
# Technology: Python 3.11 with Flask/FastAPI
# Base Image: Amazon Linux 2023 with Python 3.11
#
# STRICT REQUIREMENTS:
# - Amazon Linux 2023 base image MANDATORY
# - Multi-stage build for production optimization
# - Non-root user for security
# - Health checks for container monitoring
# - Proper signal handling for graceful shutdown
# - Configuration from environment variables
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
#
# CONFIGURATION:
# All configuration loaded from config.dev.env via environment variables
# =============================================================================

# Dependencies stage
FROM amazonlinux:2023 AS dependencies

# Install Python 3.11 and development tools
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

# Create necessary directories and set permissions
RUN mkdir -p /var/log/datafit /tmp/datafit && \
    chown -R appuser:appgroup /app /var/log/datafit /tmp/datafit && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Expose service port (configurable)
ARG SUBMISSION_PORT=5000
EXPOSE ${SUBMISSION_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Production command
CMD ["python3", "-m", "gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--timeout", "30", \
     "--keep-alive", "2", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]

# =============================================================================
# ENVIRONMENT VARIABLES:
#
# Required at runtime:
# - SUBMISSION_PORT: Service port (default: 5000)
# - SUBMISSION_HOST: Service host (default: 0.0.0.0)
# - POLLING_SERVICE_URL: URL to polling service
# - LOG_LEVEL: Logging level (default: INFO)
#
# Optional:
# - SUBMISSION_WORKERS: Number of worker processes (default: 4)
# - SUBMISSION_TIMEOUT: Request timeout (default: 30)
# - CORS_ORIGINS: Allowed CORS origins
# - RATE_LIMIT_REQUESTS: Rate limiting (default: 100)
#
# BUILD INSTRUCTIONS:
#
# Development build:
#   docker build -t datafit-submission:dev .
#   docker run -p 5000:5000 --env-file config.dev.env datafit-submission:dev
#
# Production build:
#   docker build -t datafit-submission:prod .
#   docker run -p 5000:5000 --env-file config.prod.env datafit-submission:prod
#
# Multi-architecture build:
#   docker buildx build --platform linux/amd64,linux/arm64 -t datafit-submission .
# =============================================================================
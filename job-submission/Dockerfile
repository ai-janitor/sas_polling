# =============================================================================
# DATAFIT JOB SUBMISSION SERVICE DOCKERFILE - AMAZON LINUX 2023
# =============================================================================
# Purpose: Containerize the job submission REST API service
# Technology: Python 3.11 with Flask/FastAPI
# Base Image: Amazon Linux 2023 (Python 3.11 pre-installed)
# =============================================================================

FROM amazonlinux:2023

# Install minimal runtime dependencies (using built-in Python 3.9)
RUN dnf update -y && dnf install -y --allowerasing \
    python3-pip \
    curl \
    shadow-utils \
    && dnf clean all

# Create non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

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

# Production command using vanilla Python 3.9 http.server
CMD ["python3", "app.py"]

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
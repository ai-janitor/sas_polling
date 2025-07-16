# =============================================================================
# DATAFIT JOB SUBMISSION SERVICE DOCKERFILE
# =============================================================================
# Purpose: Containerize the job submission REST API service
# Technology: Python 3.11 with Flask/FastAPI
# Base Image: Python 3.11 Alpine for security and size optimization
#
# STRICT REQUIREMENTS:
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
# - Minimal attack surface with Alpine Linux
# - No unnecessary packages or tools
# - Read-only root filesystem support
#
# CONFIGURATION:
# All configuration loaded from config.dev.env via environment variables
# =============================================================================

# Dependencies stage
FROM python:3.11-alpine AS dependencies

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    curl

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================

# Production runtime stage
FROM python:3.11-alpine AS production

# Install runtime dependencies
RUN apk add --no-cache \
    curl \
    dumb-init

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

# Set working directory
WORKDIR /app

# Copy Python dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

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
    CMD curl -f http://localhost:${SUBMISSION_PORT}/health || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Production command
CMD ["python", "-m", "gunicorn", \
     "--bind", "0.0.0.0:${SUBMISSION_PORT}", \
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
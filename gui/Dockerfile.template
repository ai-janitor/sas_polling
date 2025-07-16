# =============================================================================
# DATAFIT GUI SERVICE DOCKERFILE - AMAZON LINUX 2023
# =============================================================================
# Purpose: Containerize the GUI Single Page Application
# Technology: Multi-stage build with Node.js for development and Nginx for production
# Base Image: Amazon Linux 2023 with Node.js 20+ and Nginx
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
# 1. Development stage with hot reload capability
# 2. Production build stage with optimization
# 3. Production runtime with Nginx
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

# Development stage
FROM amazonlinux:2023 AS development

# Install Node.js 20 and development tools
RUN dnf update -y && dnf install -y \
    nodejs20 \
    nodejs20-npm \
    curl \
    && dnf clean all

# Create non-root user
RUN groupadd -g 1001 nodejs && \
    useradd -u 1001 -g nodejs -m -s /bin/bash nextjs

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package*.json ./

# Install development dependencies
RUN npm install && \
    npm cache clean --force

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose development port (configurable)
ARG GUI_PORT=3000
EXPOSE ${GUI_PORT}

# Health check for development
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${GUI_PORT}/health || exit 1

# Development command with hot reload
CMD ["npm", "run", "dev"]

# =============================================================================

# Production build stage
FROM amazonlinux:2023 AS builder

# Install Node.js 20 for building
RUN dnf update -y && dnf install -y \
    nodejs20 \
    nodejs20-npm \
    && dnf clean all

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies for building
RUN npm install && \
    npm cache clean --force

# Copy source code
COPY . .

# Build the application
RUN npm run build

# =============================================================================

# Production runtime stage
FROM amazonlinux:2023 AS production

# Install Nginx and curl for health checks
RUN dnf update -y && dnf install -y --allowerasing \
    nginx \
    curl \
    && dnf clean all

# Create non-root user for Nginx
RUN groupadd -g 1001 nginx_app && \
    useradd -u 1001 -g nginx_app -m -s /bin/bash nginx_app

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directories and set permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run /var/lib/nginx/tmp/client_body /var/lib/nginx/tmp/proxy /var/lib/nginx/tmp/fastcgi /var/lib/nginx/tmp/uwsgi /var/lib/nginx/tmp/scgi && \
    chown -R nginx_app:nginx_app /var/cache/nginx /var/log/nginx /var/run /var/lib/nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Switch to non-root user
USER nginx_app

# Expose HTTP port (configurable)
ARG GUI_PORT=3000
EXPOSE ${GUI_PORT}

# Health check for production
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Production command
CMD ["nginx", "-g", "daemon off;"]

# =============================================================================
# BUILD INSTRUCTIONS:
# 
# Development build:
#   docker build --target development -t datafit-gui:dev .
#   docker run -p 3000:3000 -v $(pwd):/app datafit-gui:dev
#
# Production build:
#   docker build --target production -t datafit-gui:prod .
#   docker run -p 3000:3000 datafit-gui:prod
#
# Multi-architecture build:
#   docker buildx build --platform linux/amd64,linux/arm64 -t datafit-gui .
# =============================================================================
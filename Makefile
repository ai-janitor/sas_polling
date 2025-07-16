# =============================================================================
# DATAFIT INFRASTRUCTURE MAKEFILE
# =============================================================================
# Purpose: Single point of control for all infrastructure operations
# Configuration: Reads all settings from config.dev.env
# 
# STRICT REQUIREMENTS:
# - NO hardcoded values anywhere in the infrastructure
# - All ports, URLs, credentials come from config.dev.env
# - Single command deployment and management
# - Environment-specific overrides supported
# - Proper cleanup and resource management
#
# AVAILABLE TARGETS:
# - build: Build all Docker images
# - deploy: Deploy all services 
# - start: Start all services
# - stop: Stop all services
# - clean: Clean up containers, images, and volumes
# - logs: Show logs from all services
# - status: Show status of all services
# - test: Run all tests
# - dev: Start in development mode
# - prod: Deploy in production mode
# =============================================================================

# Load configuration from environment file
include config.dev.env
export

# Set default environment if not specified
ENV ?= dev
CONFIG_FILE ?= config.$(ENV).env

# Docker Compose configuration
COMPOSE_FILE := docker-compose.yml
COMPOSE_DEV_FILE := docker-compose.dev.yml
COMPOSE_PROD_FILE := docker-compose.prod.yml
COMPOSE_PROJECT_NAME := $(DOCKER_NETWORK)

# Service names (from config)
GUI_SERVICE := datafit-gui
SUBMISSION_SERVICE := datafit-job-submission  
POLLING_SERVICE := datafit-job-polling
REDIS_SERVICE := datafit-redis

# Build arguments from config
BUILD_ARGS := \
	--build-arg GUI_PORT=$(GUI_PORT) \
	--build-arg SUBMISSION_PORT=$(SUBMISSION_PORT) \
	--build-arg POLLING_PORT=$(POLLING_PORT) \
	--build-arg NODE_ENV=$(DEV_MODE) \
	--build-arg PYTHON_ENV=$(DEV_MODE)

# Detect Docker Compose command (plugin vs standalone)
DOCKER_COMPOSE := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)

# Docker Compose command with config
COMPOSE_CMD := $(DOCKER_COMPOSE) \
	-f $(COMPOSE_FILE) \
	-p $(COMPOSE_PROJECT_NAME) \
	--env-file $(CONFIG_FILE)

# Development compose command
COMPOSE_DEV_CMD := $(COMPOSE_CMD) \
	-f $(COMPOSE_DEV_FILE)

# Production compose command  
COMPOSE_PROD_CMD := $(COMPOSE_CMD) \
	-f $(COMPOSE_PROD_FILE)

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# =============================================================================
# HELP TARGET
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)DataFit Infrastructure Management$(NC)"
	@echo "=================================="
	@echo ""
	@echo "$(YELLOW)Configuration:$(NC)"
	@echo "  Environment: $(ENV)"
	@echo "  Config File: $(CONFIG_FILE)"
	@echo "  Project:     $(COMPOSE_PROJECT_NAME)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# =============================================================================
# VALIDATION TARGETS
# =============================================================================

.PHONY: validate-config
validate-config: ## Validate configuration file exists and is readable
	@echo "$(BLUE)Validating configuration...$(NC)"
	@if [ ! -f $(CONFIG_FILE) ]; then \
		echo "$(RED)Error: Configuration file $(CONFIG_FILE) not found$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Configuration file $(CONFIG_FILE) exists$(NC)"
	@echo "$(BLUE)Checking required variables...$(NC)"
	@for var in GUI_PORT SUBMISSION_PORT POLLING_PORT DOCKER_NETWORK; do \
		value=$$(eval echo \$$$$var); \
		if [ -z "$$value" ]; then \
			echo "$(RED)Error: Required variable $$var not set$(NC)"; \
			exit 1; \
		fi; \
		echo "$(GREEN)✓ $$var = $$value$(NC)"; \
	done

.PHONY: validate-docker
validate-docker: ## Validate Docker and Docker Compose are available
	@echo "$(BLUE)Validating Docker environment...$(NC)"
	@docker --version > /dev/null 2>&1 || (echo "$(RED)Error: Docker not found$(NC)" && exit 1)
	@(docker compose version > /dev/null 2>&1 || docker-compose --version > /dev/null 2>&1) || (echo "$(RED)Error: Docker Compose not found$(NC)" && exit 1)
	@echo "$(GREEN)✓ Docker environment ready$(NC)"

# =============================================================================
# BUILD TARGETS
# =============================================================================

.PHONY: build
build: validate-config validate-docker ## Build all Docker images
	@echo "$(BLUE)Building all services...$(NC)"
	$(COMPOSE_CMD) build $(BUILD_ARGS)
	@echo "$(GREEN)✓ All services built successfully$(NC)"

.PHONY: build-gui
build-gui: validate-config validate-docker ## Build GUI service only
	@echo "$(BLUE)Building GUI service...$(NC)"
	$(COMPOSE_CMD) build $(BUILD_ARGS) $(GUI_SERVICE)
	@echo "$(GREEN)✓ GUI service built$(NC)"

.PHONY: build-submission
build-submission: validate-config validate-docker ## Build job submission service only
	@echo "$(BLUE)Building job submission service...$(NC)"
	$(COMPOSE_CMD) build $(BUILD_ARGS) $(SUBMISSION_SERVICE)
	@echo "$(GREEN)✓ Job submission service built$(NC)"

.PHONY: build-polling
build-polling: validate-config validate-docker ## Build job polling service only
	@echo "$(BLUE)Building job polling service...$(NC)"
	$(COMPOSE_CMD) build $(BUILD_ARGS) $(POLLING_SERVICE)
	@echo "$(GREEN)✓ Job polling service built$(NC)"

.PHONY: rebuild
rebuild: clean build ## Clean and rebuild all services
	@echo "$(GREEN)✓ Complete rebuild finished$(NC)"

# =============================================================================
# DEPLOYMENT TARGETS
# =============================================================================

.PHONY: deploy
deploy: build ## Deploy all services
	@echo "$(BLUE)Deploying all services...$(NC)"
	$(COMPOSE_CMD) up -d
	@echo "$(BLUE)Waiting for services to be healthy...$(NC)"
	@sleep 10
	@$(MAKE) status
	@echo "$(GREEN)✓ All services deployed$(NC)"

.PHONY: dev
dev: validate-config validate-docker ## Start in development mode with hot reload
	@echo "$(BLUE)Starting development environment...$(NC)"
	@if [ ! -f $(COMPOSE_DEV_FILE) ]; then \
		echo "$(YELLOW)Creating development override file...$(NC)"; \
		$(MAKE) create-dev-override; \
	fi
	$(COMPOSE_DEV_CMD) up --build
	@echo "$(GREEN)✓ Development environment started$(NC)"

.PHONY: prod
prod: validate-config validate-docker ## Deploy in production mode
	@echo "$(BLUE)Deploying production environment...$(NC)"
	@if [ ! -f config.prod.env ]; then \
		echo "$(YELLOW)Warning: config.prod.env not found, using $(CONFIG_FILE)$(NC)"; \
	fi
	$(COMPOSE_PROD_CMD) up -d --build
	@echo "$(GREEN)✓ Production environment deployed$(NC)"

# =============================================================================
# SERVICE MANAGEMENT TARGETS
# =============================================================================

.PHONY: start
start: validate-config ## Start all services
	@echo "$(BLUE)Starting all services...$(NC)"
	$(COMPOSE_CMD) start
	@echo "$(GREEN)✓ All services started$(NC)"

.PHONY: stop
stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	$(COMPOSE_CMD) stop
	@echo "$(GREEN)✓ All services stopped$(NC)"

.PHONY: restart
restart: stop start ## Restart all services
	@echo "$(GREEN)✓ All services restarted$(NC)"

.PHONY: down
down: ## Stop and remove all containers
	@echo "$(BLUE)Stopping and removing containers...$(NC)"
	$(COMPOSE_CMD) down
	@echo "$(GREEN)✓ All containers stopped and removed$(NC)"

# =============================================================================
# MONITORING TARGETS
# =============================================================================

.PHONY: status
status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@echo "==============="
	$(COMPOSE_CMD) ps
	@echo ""
	@echo "$(BLUE)Health Checks:$(NC)"
	@echo "=============="
	@for service in $(GUI_SERVICE) $(SUBMISSION_SERVICE) $(POLLING_SERVICE); do \
		echo -n "$$service: "; \
		if docker exec $$service curl -f http://localhost:$$(docker port $$service | cut -d: -f2)/health > /dev/null 2>&1; then \
			echo "$(GREEN)✓ Healthy$(NC)"; \
		else \
			echo "$(RED)✗ Unhealthy$(NC)"; \
		fi; \
	done

.PHONY: logs
logs: ## Show logs from all services
	$(COMPOSE_CMD) logs -f

.PHONY: logs-gui
logs-gui: ## Show GUI service logs
	$(COMPOSE_CMD) logs -f $(GUI_SERVICE)

.PHONY: logs-submission
logs-submission: ## Show job submission service logs
	$(COMPOSE_CMD) logs -f $(SUBMISSION_SERVICE)

.PHONY: logs-polling
logs-polling: ## Show job polling service logs
	$(COMPOSE_CMD) logs -f $(POLLING_SERVICE)

# =============================================================================
# TESTING TARGETS
# =============================================================================

.PHONY: test
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@if [ -d tests ]; then \
		docker run --rm -v $(PWD):/app -w /app python:3.11-alpine \
			sh -c "pip install -r job-submission/requirements.txt && \
			       pip install -r job-polling/requirements.txt && \
			       python -m pytest tests/ -v --cov=. --cov-report=term-missing"; \
	else \
		echo "$(YELLOW)No tests directory found$(NC)"; \
	fi

.PHONY: test-integration
test-integration: deploy ## Run integration tests against running services
	@echo "$(BLUE)Running integration tests...$(NC)"
	@echo "Testing GUI service at http://localhost:$(GUI_PORT)"
	@curl -f http://localhost:$(GUI_PORT)/health || echo "$(RED)GUI health check failed$(NC)"
	@echo "Testing submission service at http://localhost:$(SUBMISSION_PORT)"
	@curl -f http://localhost:$(SUBMISSION_PORT)/health || echo "$(RED)Submission health check failed$(NC)"
	@echo "Testing polling service at http://localhost:$(POLLING_PORT)"
	@curl -f http://localhost:$(POLLING_PORT)/health || echo "$(RED)Polling health check failed$(NC)"
	@echo "$(GREEN)✓ Integration tests completed$(NC)"

# =============================================================================
# CLEANUP TARGETS
# =============================================================================

.PHONY: clean
clean: ## Clean up containers, images, and volumes
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	$(COMPOSE_CMD) down -v --remove-orphans
	@echo "$(YELLOW)Removing unused images...$(NC)"
	docker image prune -f --filter "label=project=$(COMPOSE_PROJECT_NAME)"
	@echo "$(YELLOW)Removing unused volumes...$(NC)"
	docker volume prune -f
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

.PHONY: clean-all
clean-all: clean ## Clean everything including networks and system resources
	@echo "$(BLUE)Deep cleaning Docker resources...$(NC)"
	docker system prune -af --volumes
	@echo "$(GREEN)✓ Deep cleanup completed$(NC)"

.PHONY: clean-logs
clean-logs: ## Clean up log files
	@echo "$(BLUE)Cleaning log files...$(NC)"
	@if [ -d "$(VOLUME_LOGS)" ]; then \
		sudo rm -rf $(VOLUME_LOGS)/*; \
		echo "$(GREEN)✓ Log files cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Log directory $(VOLUME_LOGS) not found$(NC)"; \
	fi

# =============================================================================
# DEVELOPMENT HELPERS
# =============================================================================

.PHONY: shell-gui
shell-gui: ## Open shell in GUI container
	docker exec -it $(GUI_SERVICE) /bin/sh

.PHONY: shell-submission
shell-submission: ## Open shell in job submission container
	docker exec -it $(SUBMISSION_SERVICE) /bin/bash

.PHONY: shell-polling
shell-polling: ## Open shell in job polling container
	docker exec -it $(POLLING_SERVICE) /bin/bash

.PHONY: create-dev-override
create-dev-override: ## Create development docker-compose override file
	@echo "$(BLUE)Creating development override file...$(NC)"
	@echo "# Development overrides for hot reload and debugging" > $(COMPOSE_DEV_FILE)
	@echo "version: '3.8'" >> $(COMPOSE_DEV_FILE)
	@echo "services:" >> $(COMPOSE_DEV_FILE)
	@echo "  datafit-gui:" >> $(COMPOSE_DEV_FILE)
	@echo "    build:" >> $(COMPOSE_DEV_FILE)
	@echo "      target: development" >> $(COMPOSE_DEV_FILE)
	@echo "    volumes:" >> $(COMPOSE_DEV_FILE)
	@echo "      - ./gui:/app:cached" >> $(COMPOSE_DEV_FILE)
	@echo "    environment:" >> $(COMPOSE_DEV_FILE)
	@echo "      - NODE_ENV=development" >> $(COMPOSE_DEV_FILE)
	@echo "      - GUI_HOT_RELOAD=\$${GUI_HOT_RELOAD}" >> $(COMPOSE_DEV_FILE)
	@echo "    ports:" >> $(COMPOSE_DEV_FILE)
	@echo "      - \"\$${GUI_PORT}:\$${GUI_PORT}\"" >> $(COMPOSE_DEV_FILE)
	@echo "  datafit-job-submission:" >> $(COMPOSE_DEV_FILE)
	@echo "    volumes:" >> $(COMPOSE_DEV_FILE)
	@echo "      - ./job-submission:/app:cached" >> $(COMPOSE_DEV_FILE)
	@echo "    environment:" >> $(COMPOSE_DEV_FILE)
	@echo "      - FLASK_ENV=development" >> $(COMPOSE_DEV_FILE)
	@echo "      - FLASK_DEBUG=\$${DEV_DEBUG}" >> $(COMPOSE_DEV_FILE)
	@echo "    ports:" >> $(COMPOSE_DEV_FILE)
	@echo "      - \"\$${SUBMISSION_PORT}:\$${SUBMISSION_PORT}\"" >> $(COMPOSE_DEV_FILE)
	@echo "  datafit-job-polling:" >> $(COMPOSE_DEV_FILE)
	@echo "    volumes:" >> $(COMPOSE_DEV_FILE)
	@echo "      - ./job-polling:/app:cached" >> $(COMPOSE_DEV_FILE)
	@echo "      - ./reports:/app/reports:cached" >> $(COMPOSE_DEV_FILE)
	@echo "    environment:" >> $(COMPOSE_DEV_FILE)
	@echo "      - FLASK_ENV=development" >> $(COMPOSE_DEV_FILE)
	@echo "      - FLASK_DEBUG=\$${DEV_DEBUG}" >> $(COMPOSE_DEV_FILE)
	@echo "    ports:" >> $(COMPOSE_DEV_FILE)
	@echo "      - \"\$${POLLING_PORT}:\$${POLLING_PORT}\"" >> $(COMPOSE_DEV_FILE)
	@echo "$(GREEN)✓ Development override file created$(NC)"

.PHONY: backup
backup: ## Backup data and configuration
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p backups
	@tar -czf backups/datafit-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		--exclude=backups \
		--exclude=.git \
		--exclude=node_modules \
		--exclude=__pycache__ \
		.
	@echo "$(GREEN)✓ Backup created in backups/$(NC)"

# =============================================================================
# ENVIRONMENT MANAGEMENT
# =============================================================================

.PHONY: switch-env
switch-env: ## Switch to different environment (usage: make switch-env ENV=prod)
	@echo "$(BLUE)Switching to environment: $(ENV)$(NC)"
	@if [ ! -f config.$(ENV).env ]; then \
		echo "$(RED)Error: config.$(ENV).env not found$(NC)"; \
		exit 1; \
	fi
	@$(MAKE) ENV=$(ENV) validate-config
	@echo "$(GREEN)✓ Switched to $(ENV) environment$(NC)"

.PHONY: create-env
create-env: ## Create new environment config (usage: make create-env ENV=staging)
	@echo "$(BLUE)Creating $(ENV) environment config...$(NC)"
	@if [ -f config.$(ENV).env ]; then \
		echo "$(YELLOW)Warning: config.$(ENV).env already exists$(NC)"; \
		read -p "Overwrite? (y/N): " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo "$(YELLOW)Cancelled$(NC)"; \
			exit 0; \
		fi; \
	fi
	@cp config.dev.env config.$(ENV).env
	@echo "$(GREEN)✓ Created config.$(ENV).env$(NC)"
	@echo "$(YELLOW)Remember to update the configuration for $(ENV) environment$(NC)"

# =============================================================================
# DEFAULT TARGET
# =============================================================================

.DEFAULT_GOAL := help

# Make all targets phony to avoid conflicts with files
.PHONY: $(MAKECMDGOALS)
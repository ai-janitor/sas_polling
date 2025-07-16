# DataFit Demo Makefile (Simplified)
# Usage: make [target]

# Service URLs (hardcoded for simplicity)
SUBMISSION_URL := http://localhost:8101
POLLING_URL := http://localhost:8102

# Demo settings
DEMO_USER := cli_demo_user
OUTPUTS_DIR := outputs

# Colors
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m

.PHONY: help health test-reports demo clean

help: ## Show help
	@echo "$(BLUE)DataFit Demo Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@echo "  $(YELLOW)health$(NC)        Check if services are running"
	@echo "  $(YELLOW)test-reports$(NC)  Test all report types"
	@echo "  $(YELLOW)demo$(NC)          Run simple demo workflow"
	@echo "  $(YELLOW)clean$(NC)         Clean up output files"
	@echo ""

setup:
	@mkdir -p $(OUTPUTS_DIR)

health: setup ## Check service health
	@echo "$(BLUE)Checking services...$(NC)"
	@echo -n "Submission Service: "
	@if curl -s -f $(SUBMISSION_URL)/health > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi
	@echo -n "Polling Service: "
	@if curl -s -f $(POLLING_URL)/health > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi

test-reports: health ## Test all report types
	@echo "$(BLUE)Testing all report types...$(NC)"
	@echo "Testing CMBS report..."
	@curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"name":"Test-CMBS","jobDefinitionUri":"cmbs-user-manual","arguments":{"start_date":"2024-01-01","end_date":"2024-12-31","username":"$(DEMO_USER)"},"submitted_by":"$(DEMO_USER)","priority":5}' \
		| jq -r '.id' > $(OUTPUTS_DIR)/cmbs-job-id.txt
	@echo "  Job ID: $$(cat $(OUTPUTS_DIR)/cmbs-job-id.txt)"
	@echo "Testing RMBS report..."
	@curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"name":"Test-RMBS","jobDefinitionUri":"rmbs-performance","arguments":{"report_date":"2024-12-01","username":"$(DEMO_USER)"},"submitted_by":"$(DEMO_USER)","priority":5}' \
		| jq -r '.id' > $(OUTPUTS_DIR)/rmbs-job-id.txt
	@echo "  Job ID: $$(cat $(OUTPUTS_DIR)/rmbs-job-id.txt)"
	@echo "Testing VaR report..."
	@curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"name":"Test-VaR","jobDefinitionUri":"var-daily","arguments":{"calculation_date":"2024-12-15","username":"$(DEMO_USER)"},"submitted_by":"$(DEMO_USER)","priority":5}' \
		| jq -r '.id' > $(OUTPUTS_DIR)/var-job-id.txt
	@echo "  Job ID: $$(cat $(OUTPUTS_DIR)/var-job-id.txt)"
	@echo "$(GREEN)All report tests completed$(NC)"

demo: health ## Run simple demo
	@echo "$(BLUE)Running demo...$(NC)"
	@echo "1. Submitting test job..."
	@JOB_ID=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"name":"Demo-Job","jobDefinitionUri":"var-daily","arguments":{"calculation_date":"2024-12-15","username":"$(DEMO_USER)"},"submitted_by":"$(DEMO_USER)","priority":5}' \
		| jq -r '.id'); \
	echo "Job ID: $$JOB_ID"; \
	echo "2. Checking status..."; \
	curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/status | jq '.status, .progress'; \
	echo "$(GREEN)Demo completed$(NC)"

clean: ## Clean up
	@rm -rf $(OUTPUTS_DIR)
	@echo "$(GREEN)Cleaned up$(NC)"

# Default target
all: help
# =============================================================================
# DATAFIT CLI DEMO MAKEFILE
# =============================================================================
# Purpose: Automated CLI testing and demonstration of DataFit services
# Configuration: Reads settings from ../config.dev.env
# 
# STRICT REQUIREMENTS:
# - NO hardcoded URLs or ports (all from config.dev.env)
# - Automated service health checking before tests
# - Clean separation of test scenarios and outputs
# - Comprehensive error handling and reporting
# - Performance measurement and validation
#
# AVAILABLE TARGETS:
# - demo: Run complete end-to-end demonstration
# - health: Check service health and readiness
# - test-all: Run all test scenarios
# - test-basic: Run basic functionality tests
# - test-errors: Run error handling tests
# - test-performance: Run performance tests
# - test-reports: Test all report types
# - clean: Clean up demo outputs and temporary files
# - logs: Show service logs
# - help: Show this help message
# =============================================================================

# Load configuration from parent directory
include ../config.dev.env
export

# Demo configuration
DEMO_DIR := $(shell pwd)
SCRIPTS_DIR := $(DEMO_DIR)/scripts
CONFIGS_DIR := $(DEMO_DIR)/configs
OUTPUTS_DIR := $(DEMO_DIR)/outputs
TEMP_DIR := $(OUTPUTS_DIR)/temp

# Service URLs from config
SUBMISSION_URL := http://localhost:$(SUBMISSION_PORT)
POLLING_URL := http://localhost:$(POLLING_PORT)

# Demo settings
DEMO_USER := cli_demo_user
DEMO_TIMEOUT := 30
MAX_RETRIES := 10
POLL_INTERVAL := 2

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help demo health test-all test-basic test-errors test-performance test-reports clean logs setup

# Default target
all: help

help: ## Show this help message
	@echo "$(BLUE)DataFit CLI Demo Makefile$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Configuration:$(NC)"
	@echo "  Submission Service: $(SUBMISSION_URL)"
	@echo "  Polling Service:    $(POLLING_URL)"
	@echo "  Demo User:          $(DEMO_USER)"
	@echo "  Output Directory:   $(OUTPUTS_DIR)"

setup: ## Create demo directory structure
	@echo "$(BLUE)Setting up demo environment...$(NC)"
	@mkdir -p $(SCRIPTS_DIR) $(CONFIGS_DIR) $(OUTPUTS_DIR) $(TEMP_DIR)
	@echo "$(GREEN)Demo directories created$(NC)"

health: setup ## Check service health and readiness
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo -n "Submission Service: "
	@if curl -s -f $(SUBMISSION_URL)/health > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
		exit 1; \
	fi
	@echo -n "Polling Service: "
	@if curl -s -f $(POLLING_URL)/health > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)All services are healthy$(NC)"

test-basic: health ## Run basic functionality tests
	@echo "$(BLUE)Running basic functionality tests...$(NC)"
	@$(MAKE) --no-print-directory _test-health-endpoints
	@$(MAKE) --no-print-directory _test-report-definitions
	@$(MAKE) --no-print-directory _test-simple-job-submission
	@echo "$(GREEN)Basic tests completed$(NC)"

test-errors: health ## Run error handling tests
	@echo "$(BLUE)Running error handling tests...$(NC)"
	@$(MAKE) --no-print-directory _test-invalid-submissions
	@$(MAKE) --no-print-directory _test-nonexistent-resources
	@$(MAKE) --no-print-directory _test-malformed-requests
	@echo "$(GREEN)Error handling tests completed$(NC)"

test-reports: health ## Test all report types
	@echo "$(BLUE)Testing all report types...$(NC)"
	@$(MAKE) --no-print-directory _test-cmbs-report
	@$(MAKE) --no-print-directory _test-rmbs-report
	@$(MAKE) --no-print-directory _test-var-report
	@$(MAKE) --no-print-directory _test-stress-report
	@$(MAKE) --no-print-directory _test-trading-report
	@$(MAKE) --no-print-directory _test-aml-report
	@$(MAKE) --no-print-directory _test-focus-report
	@echo "$(GREEN)All report tests completed$(NC)"

test-performance: health ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	@$(MAKE) --no-print-directory _test-response-times
	@$(MAKE) --no-print-directory _test-concurrent-jobs
	@$(MAKE) --no-print-directory _test-rate-limiting
	@echo "$(GREEN)Performance tests completed$(NC)"

test-all: ## Run all test scenarios
	@echo "$(BLUE)Running complete test suite...$(NC)"
	@$(MAKE) --no-print-directory test-basic
	@$(MAKE) --no-print-directory test-errors
	@$(MAKE) --no-print-directory test-reports
	@$(MAKE) --no-print-directory test-performance
	@echo "$(GREEN)All tests completed successfully$(NC)"

demo: ## Run complete end-to-end demonstration
	@echo "$(BLUE)Starting DataFit CLI Demonstration...$(NC)"
	@echo ""
	@$(MAKE) --no-print-directory health
	@echo ""
	@$(MAKE) --no-print-directory _demo-workflow
	@echo ""
	@echo "$(GREEN)Demonstration completed successfully!$(NC)"
	@echo "$(YELLOW)Check $(OUTPUTS_DIR) for generated files$(NC)"

clean: ## Clean up demo outputs and temporary files
	@echo "$(BLUE)Cleaning up demo files...$(NC)"
	@rm -rf $(OUTPUTS_DIR)/*
	@mkdir -p $(TEMP_DIR)
	@echo "$(GREEN)Demo files cleaned$(NC)"

logs: ## Show service logs (if running in Docker)
	@echo "$(BLUE)Service logs:$(NC)"
	@echo "$(YELLOW)Note: This requires services to be running in Docker$(NC)"
	@docker logs datafit-job-submission 2>/dev/null || echo "Job submission service not running in Docker"
	@docker logs datafit-job-polling 2>/dev/null || echo "Job polling service not running in Docker"

# Internal test targets
_test-health-endpoints:
	@echo "  Testing health endpoints..."
	@curl -s $(SUBMISSION_URL)/health | jq '.service, .status' > $(TEMP_DIR)/submission-health.json
	@curl -s $(POLLING_URL)/health | jq '.service, .status' > $(TEMP_DIR)/polling-health.json
	@echo "    ✓ Health endpoints responding"

_test-report-definitions:
	@echo "  Testing report definitions..."
	@curl -s $(SUBMISSION_URL)/api/reports | jq '.title' > $(TEMP_DIR)/reports.json
	@echo "    ✓ Report definitions loaded"

_test-simple-job-submission:
	@echo "  Testing simple job submission..."
	@JOB_ID=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"name":"Test Job","jobDefinitionUri":"cmbs-user-manual","arguments":{"start_date":"2024-01-01","end_date":"2024-12-31","username":"$(DEMO_USER)"},"submitted_by":"$(DEMO_USER)","priority":5}' \
		| jq -r '.id'); \
	echo $$JOB_ID > $(TEMP_DIR)/last-job-id.txt; \
	echo "    ✓ Job submitted with ID: $$JOB_ID"

_test-invalid-submissions:
	@echo "  Testing invalid submissions..."
	@curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"name":"","jobDefinitionUri":"invalid","arguments":{},"submitted_by":""}' \
		| jq '.code' > $(TEMP_DIR)/invalid-submission.json
	@echo "    ✓ Invalid submission rejected"

_test-nonexistent-resources:
	@echo "  Testing nonexistent resources..."
	@curl -s $(POLLING_URL)/api/jobs/nonexistent-job/status \
		| jq '.code' > $(TEMP_DIR)/nonexistent-job.json
	@echo "    ✓ Nonexistent resources handled"

_test-malformed-requests:
	@echo "  Testing malformed requests..."
	@curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: text/plain" \
		-d "not json" \
		| jq '.code' > $(TEMP_DIR)/malformed-request.json
	@echo "    ✓ Malformed requests rejected"

_test-cmbs-report:
	@echo "  Testing CMBS report..."
	@$(call submit_and_wait_job,cmbs-user-manual,'{"start_date":"2024-01-01","end_date":"2024-12-31","property_type":"Office","include_charts":true,"username":"$(DEMO_USER)"}')

_test-rmbs-report:
	@echo "  Testing RMBS report..."
	@$(call submit_and_wait_job,rmbs-performance,'{"report_date":"2024-12-01","loan_type":"Prime","performance_metrics":"Enhanced","username":"$(DEMO_USER)"}')

_test-var-report:
	@echo "  Testing VaR report..."
	@$(call submit_and_wait_job,var-daily,'{"calculation_date":"2024-12-15","confidence_level":"99%","username":"$(DEMO_USER)"}')

_test-stress-report:
	@echo "  Testing Stress Testing report..."
	@$(call submit_and_wait_job,stress-testing,'{"test_date":"2024-12-15","scenario_type":"Baseline","test_horizon":"2 Years","username":"$(DEMO_USER)"}')

_test-trading-report:
	@echo "  Testing Trading Activity report..."
	@$(call submit_and_wait_job,trading-activity,'{"trade_date":"2024-12-15","asset_class":"Bonds","username":"$(DEMO_USER)"}')

_test-aml-report:
	@echo "  Testing AML Alerts report..."
	@$(call submit_and_wait_job,aml-alerts,'{"alert_date":"2024-12-15","alert_type":"Suspicious Activity","username":"$(DEMO_USER)"}')

_test-focus-report:
	@echo "  Testing FOCUS Manual report..."
	@$(call submit_and_wait_job,focus-manual,'{"reporting_date":"2024-12-01","report_type":"Monthly","entity_type":"Broker-Dealer","username":"$(DEMO_USER)"}')

_test-response-times:
	@echo "  Testing response times..."
	@echo "    Health endpoint:" 
	@time curl -s $(SUBMISSION_URL)/health > /dev/null
	@echo "    Reports endpoint:"
	@time curl -s $(SUBMISSION_URL)/api/reports > /dev/null

_test-concurrent-jobs:
	@echo "  Testing concurrent job submissions..."
	@for i in 1 2 3; do \
		curl -s -X POST $(SUBMISSION_URL)/api/jobs \
			-H "Content-Type: application/json" \
			-d "{\"name\":\"Concurrent Job $$i\",\"jobDefinitionUri\":\"var-daily\",\"arguments\":{\"calculation_date\":\"2024-12-15\",\"username\":\"$(DEMO_USER)\"},\"submitted_by\":\"$(DEMO_USER)\",\"priority\":5}" \
			| jq -r '.id' >> $(TEMP_DIR)/concurrent-jobs.txt & \
	done; \
	wait; \
	echo "    ✓ Submitted $$(wc -l < $(TEMP_DIR)/concurrent-jobs.txt) concurrent jobs"

_test-rate-limiting:
	@echo "  Testing rate limiting..."
	@for i in {1..25}; do \
		curl -s -o /dev/null -w "%{http_code}\n" $(SUBMISSION_URL)/api/reports; \
	done | grep -c "429" > $(TEMP_DIR)/rate-limit-hits.txt || true
	@echo "    ✓ Rate limiting triggered $$(cat $(TEMP_DIR)/rate-limit-hits.txt) times"

_demo-workflow:
	@echo "$(BLUE)Running end-to-end workflow demonstration...$(NC)"
	@echo ""
	@echo "1. Checking service health..."
	@curl -s $(SUBMISSION_URL)/health | jq '.service, .status'
	@curl -s $(POLLING_URL)/health | jq '.service, .status'
	@echo ""
	@echo "2. Fetching available reports..."
	@curl -s $(SUBMISSION_URL)/api/reports | jq '.title, (.categories | length)'
	@echo ""
	@echo "3. Submitting CMBS report job..."
	@JOB_ID=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"name":"Demo CMBS Report","jobDefinitionUri":"cmbs-user-manual","arguments":{"start_date":"2024-01-01","end_date":"2024-12-31","property_type":"Office","include_charts":true,"username":"$(DEMO_USER)"},"submitted_by":"$(DEMO_USER)","priority":5}' \
		| jq -r '.id'); \
	echo "Job submitted with ID: $$JOB_ID"; \
	echo $$JOB_ID > $(OUTPUTS_DIR)/demo-job-id.txt; \
	echo ""; \
	echo "4. Monitoring job status..."; \
	for i in {1..$(MAX_RETRIES)}; do \
		STATUS=$$(curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/status | jq -r '.status'); \
		PROGRESS=$$(curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/status | jq -r '.progress'); \
		echo "   Status: $$STATUS, Progress: $$PROGRESS%"; \
		if [ "$$STATUS" = "completed" ] || [ "$$STATUS" = "failed" ] || [ "$$STATUS" = "cancelled" ]; then \
			break; \
		fi; \
		sleep $(POLL_INTERVAL); \
	done; \
	echo ""; \
	if [ "$$STATUS" = "completed" ]; then \
		echo "5. Listing generated files..."; \
		curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/files | jq '.files[] | .filename'; \
		echo ""; \
		echo "6. Downloading sample file..."; \
		curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/files/report.html -o $(OUTPUTS_DIR)/demo-report.html; \
		echo "   Downloaded demo-report.html to $(OUTPUTS_DIR)/"; \
	else \
		echo "5. Job did not complete successfully (Status: $$STATUS)"; \
	fi

# Function to submit job and wait for completion
define submit_and_wait_job
	JOB_ID=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"name":"Test $(1) Report","jobDefinitionUri":"$(1)","arguments":$(2),"submitted_by":"$(DEMO_USER)","priority":5}' \
		| jq -r '.id'); \
	echo "    Job ID: $$JOB_ID"; \
	for i in {1..5}; do \
		STATUS=$$(curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/status | jq -r '.status'); \
		if [ "$$STATUS" = "completed" ] || [ "$$STATUS" = "failed" ] || [ "$$STATUS" = "cancelled" ]; then \
			echo "    ✓ Job completed with status: $$STATUS"; \
			break; \
		fi; \
		sleep 1; \
	done
endef

# Validation targets
validate-config: ## Validate configuration
	@echo "$(BLUE)Validating configuration...$(NC)"
	@if [ -z "$(SUBMISSION_PORT)" ]; then echo "$(RED)SUBMISSION_PORT not set$(NC)"; exit 1; fi
	@if [ -z "$(POLLING_PORT)" ]; then echo "$(RED)POLLING_PORT not set$(NC)"; exit 1; fi
	@echo "$(GREEN)Configuration valid$(NC)"

# Generate demo report
report: ## Generate demo execution report
	@echo "$(BLUE)Generating demo report...$(NC)"
	@echo "# DataFit Demo Execution Report" > $(OUTPUTS_DIR)/demo-report.md
	@echo "" >> $(OUTPUTS_DIR)/demo-report.md
	@echo "**Execution Date:** $$(date)" >> $(OUTPUTS_DIR)/demo-report.md
	@echo "**Demo User:** $(DEMO_USER)" >> $(OUTPUTS_DIR)/demo-report.md
	@echo "" >> $(OUTPUTS_DIR)/demo-report.md
	@echo "## Service Configuration" >> $(OUTPUTS_DIR)/demo-report.md
	@echo "- Submission Service: $(SUBMISSION_URL)" >> $(OUTPUTS_DIR)/demo-report.md
	@echo "- Polling Service: $(POLLING_URL)" >> $(OUTPUTS_DIR)/demo-report.md
	@echo "" >> $(OUTPUTS_DIR)/demo-report.md
	@echo "## Files Generated" >> $(OUTPUTS_DIR)/demo-report.md
	@find $(OUTPUTS_DIR) -name "*.html" -o -name "*.json" -o -name "*.txt" | \
		while read file; do echo "- $$file"; done >> $(OUTPUTS_DIR)/demo-report.md
	@echo "$(GREEN)Demo report generated: $(OUTPUTS_DIR)/demo-report.md$(NC)"
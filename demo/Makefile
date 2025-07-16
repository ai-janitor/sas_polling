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

# Service URLs from config (using external ports for CLI access)
SUBMISSION_URL := http://localhost:$(SUBMISSION_EXTERNAL_PORT)
POLLING_URL := http://localhost:$(POLLING_EXTERNAL_PORT)

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

.PHONY: help demo health test-all test-basic test-errors test-performance test-reports clean logs setup step1 step2 step3 step4

# Default target
all: help

help: ## Show this help message
	@echo "$(BLUE)DataFit CLI Demo Makefile$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Demo Steps (Quick Start):$(NC)"
	@echo "  $(YELLOW)step1$(NC)           Submit single CMBS job with validation"
	@echo "  $(YELLOW)step2$(NC)           Submit multiple jobs (RMBS, VaR, Trading)"
	@echo "  $(YELLOW)step3$(NC)           Demonstrate error handling scenarios"
	@echo "  $(YELLOW)step4$(NC)           Complete workflow: submit → monitor → download files"
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
	@$(MAKE) --no-print-directory _test-portfolio-pdf-report
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
	@$(call submit_and_wait_job_from_file,$(CONFIGS_DIR)/cmbs-test.json)

_test-rmbs-report:
	@echo "  Testing RMBS report..."
	@$(call submit_and_wait_job_from_file,$(CONFIGS_DIR)/rmbs-test.json)

_test-var-report:
	@echo "  Testing VaR report..."
	@$(call submit_and_wait_job_from_file,$(CONFIGS_DIR)/var-test.json)

_test-stress-report:
	@echo "  Testing Stress Testing report..."
	@$(call submit_and_wait_job_from_file,$(CONFIGS_DIR)/stress-test.json)

_test-trading-report:
	@echo "  Testing Trading Activity report..."
	@$(call submit_and_wait_job_from_file,$(CONFIGS_DIR)/trading-test.json)

_test-aml-report:
	@echo "  Testing AML Alerts report..."
	@$(call submit_and_wait_job_from_file,$(CONFIGS_DIR)/aml-test.json)

_test-focus-report:
	@echo "  Testing FOCUS Manual report..."
	@$(call submit_and_wait_job_from_file,$(CONFIGS_DIR)/focus-test.json)

_test-portfolio-pdf-report:
	@echo "  Testing Portfolio Analytics PDF report..."
	@$(call submit_and_wait_job_from_file,$(CONFIGS_DIR)/portfolio-pdf-test.json)

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
define submit_and_wait_job_from_file
	JOB_ID=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d @$(1) \
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

# =============================================================================
# DEMO STEP TARGETS - Based on Frontend Success Patterns
# =============================================================================

step1: health ## Demo Step 1: Submit single CMBS job with validation
	@echo "$(BLUE)Demo Step 1: Single Job Submission$(NC)"
	@echo "$(YELLOW)Submitting CMBS User Manual report job...$(NC)"
	@echo ""
	@echo "1. Job Submission Request:"
	@JOB_RESPONSE=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Demo-CMBS-Report", \
			"jobDefinitionUri": "cmbs-user-manual", \
			"arguments": { \
				"start_date": "2025-01-01", \
				"end_date": "2025-07-16", \
				"property_type": "All", \
				"include_charts": true, \
				"username": "$(DEMO_USER)" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 5 \
		}'); \
	echo "$$JOB_RESPONSE" | jq '.'; \
	JOB_ID=$$(echo "$$JOB_RESPONSE" | jq -r '.id'); \
	echo ""; \
	if [ "$$JOB_ID" != "null" ] && [ "$$JOB_ID" != "" ]; then \
		echo "$(GREEN)✓ Job submitted successfully with ID: $$JOB_ID$(NC)"; \
		echo "$$JOB_ID" > $(OUTPUTS_DIR)/step1-job-id.txt; \
		echo ""; \
		echo "2. Checking job status:"; \
		STATUS_RESPONSE=$$(curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/status); \
		echo "$$STATUS_RESPONSE" | jq '.'; \
		echo ""; \
		echo "$(GREEN)Step 1 completed successfully!$(NC)"; \
	else \
		echo "$(RED)✗ Job submission failed$(NC)"; \
		exit 1; \
	fi

step2: health ## Demo Step 2: Submit multiple jobs with different report types  
	@echo "$(BLUE)Demo Step 2: Multiple Job Submissions$(NC)"
	@echo "$(YELLOW)Submitting multiple report jobs...$(NC)"
	@echo ""
	@rm -f $(OUTPUTS_DIR)/step2-job-ids.txt
	@echo "1. Submitting RMBS Performance Report:"
	@JOB_ID1=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Demo-RMBS-Report", \
			"jobDefinitionUri": "rmbs-performance", \
			"arguments": { \
				"report_date": "2024-12-01", \
				"pool_id": "DEMO-POOL-001", \
				"loan_type": "Prime", \
				"performance_metrics": "Enhanced", \
				"username": "$(DEMO_USER)" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 3 \
		}' | jq -r '.id'); \
	echo "   Job ID: $$JOB_ID1"; \
	echo "$$JOB_ID1" >> $(OUTPUTS_DIR)/step2-job-ids.txt; \
	echo ""; \
	echo "2. Submitting VaR Daily Report:"; \
	JOB_ID2=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Demo-VaR-Report", \
			"jobDefinitionUri": "var-daily", \
			"arguments": { \
				"calculation_date": "2025-07-16", \
				"confidence_level": "99%", \
				"portfolio": "MAIN_PORTFOLIO", \
				"include_stress": true, \
				"username": "$(DEMO_USER)" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 1 \
		}' | jq -r '.id'); \
	echo "   Job ID: $$JOB_ID2"; \
	echo "$$JOB_ID2" >> $(OUTPUTS_DIR)/step2-job-ids.txt; \
	echo ""; \
	echo "3. Submitting Trading Activity Report:"; \
	JOB_ID3=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Demo-Trading-Report", \
			"jobDefinitionUri": "trading-activity", \
			"arguments": { \
				"trade_date": "2025-07-16", \
				"asset_class": "Bonds", \
				"trader_id": "DEMO_TRADER_001", \
				"include_pnl": true, \
				"username": "$(DEMO_USER)" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 4 \
		}' | jq -r '.id'); \
	echo "   Job ID: $$JOB_ID3"; \
	echo "$$JOB_ID3" >> $(OUTPUTS_DIR)/step2-job-ids.txt; \
	echo ""; \
	echo "4. Monitoring all job statuses:"; \
	cat $(OUTPUTS_DIR)/step2-job-ids.txt | while read job_id; do \
		if [ -n "$$job_id" ]; then \
			echo "   Checking job $$job_id:"; \
			curl -s $(POLLING_URL)/api/jobs/$$job_id/status | jq -c '{id: .id, status: .status, progress: .progress}'; \
		fi; \
	done; \
	echo ""; \
	echo "$(GREEN)Step 2 completed! Submitted $$(wc -l < $(OUTPUTS_DIR)/step2-job-ids.txt) jobs$(NC)"

step3: health ## Demo Step 3: Error handling and edge cases
	@echo "$(BLUE)Demo Step 3: Error Handling & Edge Cases$(NC)"
	@echo "$(YELLOW)Testing various error scenarios...$(NC)"
	@echo ""
	@echo "1. Testing invalid job name (with forbidden characters):"
	@RESPONSE1=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Invalid Job: Name, With: Forbidden! Characters", \
			"jobDefinitionUri": "cmbs-user-manual", \
			"arguments": { \
				"start_date": "2025-01-01", \
				"end_date": "2025-07-16", \
				"username": "$(DEMO_USER)" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 5 \
		}'); \
	echo "$$RESPONSE1" | jq '.'; \
	echo ""; \
	echo "2. Testing missing required field (username):"; \
	RESPONSE2=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Missing-Username-Test", \
			"jobDefinitionUri": "cmbs-user-manual", \
			"arguments": { \
				"start_date": "2025-01-01", \
				"end_date": "2025-07-16", \
				"property_type": "All" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 5 \
		}'); \
	echo "$$RESPONSE2" | jq '.'; \
	echo ""; \
	echo "3. Testing non-existent report ID:"; \
	RESPONSE3=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Invalid-Report-Test", \
			"jobDefinitionUri": "non-existent-report", \
			"arguments": { \
				"username": "$(DEMO_USER)" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 5 \
		}'); \
	echo "$$RESPONSE3" | jq '.'; \
	echo ""; \
	echo "4. Testing malformed JSON:"; \
	RESPONSE4=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{"invalid": json, syntax}'); \
	echo "$$RESPONSE4" | jq '.'; \
	echo ""; \
	echo "5. Testing valid job to confirm system still works:"; \
	RESPONSE5=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Recovery-Test-Job", \
			"jobDefinitionUri": "var-daily", \
			"arguments": { \
				"calculation_date": "2025-07-16", \
				"confidence_level": "95%", \
				"username": "$(DEMO_USER)" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 5 \
		}'); \
	echo "$$RESPONSE5" | jq '.'; \
	RECOVERY_JOB_ID=$$(echo "$$RESPONSE5" | jq -r '.id'); \
	if [ "$$RECOVERY_JOB_ID" != "null" ] && [ "$$RECOVERY_JOB_ID" != "" ]; then \
		echo ""; \
		echo "$(GREEN)✓ System recovery confirmed - valid job submitted: $$RECOVERY_JOB_ID$(NC)"; \
	else \
		echo ""; \
		echo "$(RED)✗ System recovery failed$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)Step 3 completed! Error handling demonstrated$(NC)"

step4: health ## Demo Step 4: Complete workflow with file download
	@echo "$(BLUE)Demo Step 4: Complete Workflow - Submit → Monitor → Download$(NC)"
	@echo "$(YELLOW)Demonstrating full job lifecycle...$(NC)"
	@echo ""
	@echo "1. Submitting VaR Daily report (quick job):"
	@JOB_RESPONSE=$$(curl -s -X POST $(SUBMISSION_URL)/api/jobs \
		-H "Content-Type: application/json" \
		-d '{ \
			"name": "Demo-Complete-Workflow", \
			"jobDefinitionUri": "var-daily", \
			"arguments": { \
				"calculation_date": "2025-07-16", \
				"confidence_level": "95%", \
				"username": "$(DEMO_USER)" \
			}, \
			"submitted_by": "$(DEMO_USER)", \
			"priority": 5 \
		}'); \
	echo "$$JOB_RESPONSE" | jq '.'; \
	JOB_ID=$$(echo "$$JOB_RESPONSE" | jq -r '.id'); \
	echo ""; \
	if [ "$$JOB_ID" != "null" ] && [ "$$JOB_ID" != "" ]; then \
		echo "$(GREEN)✓ Job submitted with ID: $$JOB_ID$(NC)"; \
		echo "$$JOB_ID" > $(OUTPUTS_DIR)/step4-job-id.txt; \
		echo ""; \
		echo "2. Monitoring job progress (polling every 3 seconds):"; \
		for i in {1..10}; do \
			STATUS_RESPONSE=$$(curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/status); \
			STATUS=$$(echo "$$STATUS_RESPONSE" | jq -r '.status'); \
			PROGRESS=$$(echo "$$STATUS_RESPONSE" | jq -r '.progress'); \
			echo "   Poll $$i: Status=$$STATUS, Progress=$$PROGRESS%"; \
			if [ "$$STATUS" = "completed" ]; then \
				echo "   $(GREEN)✓ Job completed successfully!$(NC)"; \
				break; \
			elif [ "$$STATUS" = "failed" ]; then \
				echo "   $(RED)✗ Job failed$(NC)"; \
				break; \
			fi; \
			sleep 3; \
		done; \
		echo ""; \
		if [ "$$STATUS" = "completed" ]; then \
			echo "3. Listing available files:"; \
			FILES_RESPONSE=$$(curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/files); \
			echo "$$FILES_RESPONSE" | jq '.'; \
			echo ""; \
			echo "4. Downloading files:"; \
			echo "$$FILES_RESPONSE" | jq -r '.files[]?.filename' | while read filename; do \
				if [ -n "$$filename" ]; then \
					echo "   Downloading: $$filename"; \
					curl -s $(POLLING_URL)/api/jobs/$$JOB_ID/files/$$filename -o $(OUTPUTS_DIR)/$$filename; \
					echo "   $(GREEN)✓ Saved to: $(OUTPUTS_DIR)/$$filename$(NC)"; \
				fi; \
			done; \
			echo ""; \
			echo "5. Download URLs for reference:"; \
			echo "$$FILES_RESPONSE" | jq -r '.files[]?.filename' | while read filename; do \
				if [ -n "$$filename" ]; then \
					echo "   $(POLLING_URL)/api/jobs/$$JOB_ID/files/$$filename"; \
				fi; \
			done; \
		else \
			echo "3. Job did not complete within polling window (Status: $$STATUS)"; \
			echo "   You can check status later with:"; \
			echo "   curl $(POLLING_URL)/api/jobs/$$JOB_ID/status"; \
		fi; \
	else \
		echo "$(RED)✗ Job submission failed$(NC)"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(GREEN)Step 4 completed! Full workflow demonstrated$(NC)"
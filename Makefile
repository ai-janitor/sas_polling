# DataFit Testing and Development Makefile
# Usage: make [target]

.PHONY: help test test-unit test-integration test-performance test-all
.PHONY: coverage coverage-html coverage-xml coverage-report
.PHONY: lint format security docs clean install-dev
.PHONY: run-tests run-coverage run-lint run-security
.PHONY: setup-env check-requirements benchmark profile

# Default target
.DEFAULT_GOAL := help

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
MAGENTA = \033[0;35m
CYAN = \033[0;36m
WHITE = \033[0;37m
RESET = \033[0m

# Python and pip executables
PYTHON = python3
PIP = pip3
PYTEST = pytest
TOX = tox

# Directories
SRC_DIR = src
TEST_DIR = tests
DOCS_DIR = docs
COVERAGE_DIR = htmlcov
REPORTS_DIR = reports

# Create reports directory if it doesn't exist
$(shell mkdir -p $(REPORTS_DIR))

help: ## Show this help message
	@echo "$(CYAN)DataFit Testing and Development Commands$(RESET)"
	@echo ""
	@echo "$(YELLOW)Testing:$(RESET)"
	@awk 'BEGIN {FS = ":.*##"; printf "  %-20s %s\n", "Target", "Description"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | grep -E "(test|coverage)"
	@echo ""
	@echo "$(YELLOW)Code Quality:$(RESET)"
	@awk 'BEGIN {FS = ":.*##"; printf "  %-20s %s\n", "Target", "Description"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | grep -E "(lint|format|security)"
	@echo ""
	@echo "$(YELLOW)Development:$(RESET)"
	@awk 'BEGIN {FS = ":.*##"; printf "  %-20s %s\n", "Target", "Description"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | grep -E "(install|setup|clean|docs)"
	@echo ""

# =============================================================================
# Testing Targets
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(RESET)"
	$(PYTEST) $(TEST_DIR) -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(RESET)"
	$(PYTEST) $(TEST_DIR) -m "unit and not slow" -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(RESET)"
	$(PYTEST) $(TEST_DIR) -m "integration" -v

test-performance: ## Run performance tests only
	@echo "$(BLUE)Running performance tests...$(RESET)"
	$(PYTEST) $(TEST_DIR) -m "performance" -v --benchmark-only

test-slow: ## Run slow tests
	@echo "$(BLUE)Running slow tests...$(RESET)"
	$(PYTEST) $(TEST_DIR) -m "slow" -v

test-all: ## Run all tests including slow ones
	@echo "$(BLUE)Running all tests including slow ones...$(RESET)"
	$(PYTEST) $(TEST_DIR) -v --runslow

test-parallel: ## Run tests in parallel
	@echo "$(BLUE)Running tests in parallel...$(RESET)"
	$(PYTEST) $(TEST_DIR) -n auto -v

test-failed: ## Run only previously failed tests
	@echo "$(BLUE)Running previously failed tests...$(RESET)"
	$(PYTEST) --lf -v

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)Running tests in watch mode...$(RESET)"
	ptw $(TEST_DIR) -- -v

# =============================================================================
# Coverage Targets
# =============================================================================

coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html --cov-report=xml

coverage-unit: ## Run unit tests with coverage
	@echo "$(BLUE)Running unit tests with coverage...$(RESET)"
	$(PYTEST) $(TEST_DIR) -m "unit and not slow" --cov=$(SRC_DIR) --cov-report=term-missing

coverage-html: ## Generate HTML coverage report
	@echo "$(BLUE)Generating HTML coverage report...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html
	@echo "$(GREEN)Coverage report generated in $(COVERAGE_DIR)/index.html$(RESET)"

coverage-xml: ## Generate XML coverage report
	@echo "$(BLUE)Generating XML coverage report...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=xml

coverage-json: ## Generate JSON coverage report
	@echo "$(BLUE)Generating JSON coverage report...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=json

coverage-report: ## Show coverage report
	@echo "$(BLUE)Showing coverage report...$(RESET)"
	coverage report --show-missing

coverage-erase: ## Erase coverage data
	@echo "$(BLUE)Erasing coverage data...$(RESET)"
	coverage erase

# =============================================================================
# Code Quality Targets
# =============================================================================

lint: ## Run all linting checks
	@echo "$(BLUE)Running linting checks...$(RESET)"
	@echo "$(YELLOW)Checking import sorting...$(RESET)"
	isort --check-only --diff $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)Checking code formatting...$(RESET)"
	black --check --diff $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)Running flake8...$(RESET)"
	flake8 $(SRC_DIR) $(TEST_DIR)
	@echo "$(YELLOW)Running mypy...$(RESET)"
	mypy $(SRC_DIR) --ignore-missing-imports

lint-fix: ## Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(RESET)"
	isort $(SRC_DIR) $(TEST_DIR)
	black $(SRC_DIR) $(TEST_DIR)

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(RESET)"
	isort $(SRC_DIR) $(TEST_DIR)
	black $(SRC_DIR) $(TEST_DIR)

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(RESET)"
	isort --check-only $(SRC_DIR) $(TEST_DIR)
	black --check $(SRC_DIR) $(TEST_DIR)

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking...$(RESET)"
	mypy $(SRC_DIR) --ignore-missing-imports

# =============================================================================
# Security Targets
# =============================================================================

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(RESET)"
	@echo "$(YELLOW)Checking for known vulnerabilities...$(RESET)"
	safety check --json --output $(REPORTS_DIR)/safety-report.json || true
	@echo "$(YELLOW)Running security linting...$(RESET)"
	bandit -r $(SRC_DIR) -f json -o $(REPORTS_DIR)/bandit-report.json || true
	@echo "$(YELLOW)Auditing packages...$(RESET)"
	pip-audit --format=json --output=$(REPORTS_DIR)/pip-audit.json || true

bandit: ## Run bandit security linting
	@echo "$(BLUE)Running bandit security linting...$(RESET)"
	bandit -r $(SRC_DIR) -f json -o $(REPORTS_DIR)/bandit-report.json

safety: ## Check for known security vulnerabilities
	@echo "$(BLUE)Checking for known security vulnerabilities...$(RESET)"
	safety check --json --output $(REPORTS_DIR)/safety-report.json

# =============================================================================
# Development Environment Targets
# =============================================================================

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	$(PIP) install -r requirements-test.txt
	$(PIP) install -e .

setup-env: ## Set up development environment
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	$(PYTHON) -m venv venv
	@echo "$(GREEN)Virtual environment created. Activate with: source venv/bin/activate$(RESET)"
	@echo "$(YELLOW)Run 'make install-dev' after activating the virtual environment$(RESET)"

check-requirements: ## Check if all requirements are installed
	@echo "$(BLUE)Checking requirements...$(RESET)"
	$(PIP) check

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(RESET)"
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements-test.txt

# =============================================================================
# Tox Targets
# =============================================================================

tox: ## Run tox tests across all environments
	@echo "$(BLUE)Running tox tests...$(RESET)"
	$(TOX)

tox-env: ## Run tox for specific environment (usage: make tox-env ENV=py311)
	@echo "$(BLUE)Running tox for $(ENV)...$(RESET)"
	$(TOX) -e $(ENV)

tox-parallel: ## Run tox tests in parallel
	@echo "$(BLUE)Running tox tests in parallel...$(RESET)"
	$(TOX) --parallel auto

# =============================================================================
# Documentation Targets
# =============================================================================

docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(RESET)"
	cd $(DOCS_DIR) && make html
	@echo "$(GREEN)Documentation built in $(DOCS_DIR)/_build/html/$(RESET)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(RESET)"
	cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8080

docs-clean: ## Clean documentation build
	@echo "$(BLUE)Cleaning documentation build...$(RESET)"
	cd $(DOCS_DIR) && make clean

# =============================================================================
# Performance and Profiling Targets
# =============================================================================

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running performance benchmarks...$(RESET)"
	$(PYTEST) $(TEST_DIR) -m "performance" --benchmark-only --benchmark-sort=mean --benchmark-json=$(REPORTS_DIR)/benchmark.json

profile: ## Profile test execution
	@echo "$(BLUE)Profiling test execution...$(RESET)"
	$(PYTEST) $(TEST_DIR) --profile --profile-svg

memory-profile: ## Run memory profiling
	@echo "$(BLUE)Running memory profiling...$(RESET)"
	mprof run $(PYTEST) $(TEST_DIR) -m "unit"
	mprof plot --output $(REPORTS_DIR)/memory_profile.png

# =============================================================================
# Reporting Targets
# =============================================================================

test-report: ## Generate comprehensive test report
	@echo "$(BLUE)Generating comprehensive test report...$(RESET)"
	$(PYTEST) $(TEST_DIR) --html=$(REPORTS_DIR)/pytest-report.html --self-contained-html --json-report --json-report-file=$(REPORTS_DIR)/pytest-report.json

ci-test: ## Run tests for CI environment
	@echo "$(BLUE)Running CI tests...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=xml --cov-report=term --junit-xml=$(REPORTS_DIR)/junit.xml

quality-report: ## Generate code quality report
	@echo "$(BLUE)Generating code quality report...$(RESET)"
	@make lint > $(REPORTS_DIR)/lint-report.txt 2>&1 || true
	@make security
	@echo "$(GREEN)Quality reports generated in $(REPORTS_DIR)/$(RESET)"

# =============================================================================
# Cleanup Targets
# =============================================================================

clean: ## Clean up generated files and directories
	@echo "$(BLUE)Cleaning up...$(RESET)"
	rm -rf $(COVERAGE_DIR)
	rm -rf .pytest_cache
	rm -rf .tox
	rm -rf .coverage*
	rm -rf coverage.xml
	rm -rf coverage.json
	rm -rf .mypy_cache
	rm -rf $(REPORTS_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-all: clean ## Clean everything including documentation
	@echo "$(BLUE)Cleaning everything...$(RESET)"
	cd $(DOCS_DIR) && make clean 2>/dev/null || true
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

# =============================================================================
# Utility Targets
# =============================================================================

list-tests: ## List all tests
	@echo "$(BLUE)Listing all tests...$(RESET)"
	$(PYTEST) --collect-only -q

list-markers: ## List all test markers
	@echo "$(BLUE)Listing all test markers...$(RESET)"
	$(PYTEST) --markers

count-tests: ## Count total number of tests
	@echo "$(BLUE)Counting tests...$(RESET)"
	@echo "Total tests: $$($(PYTEST) --collect-only -q | grep -c '<Module')"
	@echo "Unit tests: $$($(PYTEST) --collect-only -q -m 'unit' | grep -c '<Module')"
	@echo "Integration tests: $$($(PYTEST) --collect-only -q -m 'integration' | grep -c '<Module')"

validate-phase5a: ## Validate Phase 5A test completion
	@echo "$(BLUE)Validating Phase 5A test completion...$(RESET)"
	@echo "$(YELLOW)Checking test file structure...$(RESET)"
	@test -d tests/test_job_submission && echo "✓ Job submission tests directory exists" || echo "✗ Missing job submission tests"
	@test -d tests/test_job_polling && echo "✓ Job polling tests directory exists" || echo "✗ Missing job polling tests"
	@test -d tests/test_reports && echo "✓ Report tests directory exists" || echo "✗ Missing report tests"
	@test -d tests/test_infrastructure && echo "✓ Infrastructure tests directory exists" || echo "✗ Missing infrastructure tests"
	@test -d tests/test_mocks && echo "✓ Mock tests directory exists" || echo "✗ Missing mock tests"
	@test -d tests/test_fixtures && echo "✓ Fixture tests directory exists" || echo "✗ Missing fixture tests"
	@echo "$(YELLOW)Running test validation...$(RESET)"
	@$(PYTEST) $(TEST_DIR) --collect-only | grep -c "collected" || echo "0 tests collected"

# =============================================================================
# Quick Shortcuts
# =============================================================================

quick-test: test-unit ## Quick unit test run
unit: test-unit ## Alias for test-unit
integration: test-integration ## Alias for test-integration
perf: test-performance ## Alias for test-performance
cov: coverage ## Alias for coverage

# =============================================================================
# Help and Information
# =============================================================================

status: ## Show project testing status
	@echo "$(CYAN)DataFit Testing Status$(RESET)"
	@echo "$(YELLOW)Test Files:$(RESET)"
	@find $(TEST_DIR) -name "test_*.py" | wc -l | xargs echo "  Test files:"
	@echo "$(YELLOW)Coverage:$(RESET)"
	@if [ -f .coverage ]; then \
		coverage report --show-missing | tail -1; \
	else \
		echo "  No coverage data available. Run 'make coverage' first."; \
	fi
	@echo "$(YELLOW)Last Test Run:$(RESET)"
	@if [ -f .pytest_cache/v/cache/lastfailed ]; then \
		echo "  Some tests failed in last run"; \
	else \
		echo "  All tests passed in last run"; \
	fi

info: ## Show environment information
	@echo "$(CYAN)Environment Information$(RESET)"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "Pip version: $$($(PIP) --version)"
	@echo "Pytest version: $$($(PYTEST) --version)"
	@echo "Working directory: $$(pwd)"
	@echo "Virtual environment: $$(echo $$VIRTUAL_ENV)"
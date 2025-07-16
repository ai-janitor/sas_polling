# DataFit Testing Guide - Phase 5A Backend Unit Testing

## Overview

This document provides comprehensive guidance for running and maintaining the Phase 5A Backend Unit Testing suite for the DataFit SAS Viya job execution system.

## Quick Start

### Prerequisites
- Python 3.9+ installed
- Virtual environment recommended
- Git repository cloned

### Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install test dependencies
pip install -r requirements-test.txt

# Verify installation
pytest --version
```

### Run Tests
```bash
# Run all unit tests
make test-unit

# Run with coverage
make coverage

# Run specific test categories
pytest tests/test_job_submission -v
pytest tests/test_reports -v
pytest -m "unit and not slow" -v
```

## Phase 5A Test Structure

### Test Categories
The Phase 5A testing suite is organized into 6 main categories:

1. **Job Submission Service Tests** (2 files)
   - `tests/test_job_submission/test_models.py`
   - `tests/test_job_submission/test_utils.py`

2. **Job Polling Service Tests** (4 files)
   - `tests/test_job_polling/test_app.py`
   - `tests/test_job_polling/test_models.py`
   - `tests/test_job_polling/test_job_executor.py`
   - `tests/test_job_polling/test_file_manager.py`

3. **Report Generator Tests** (7 files)
   - `tests/test_reports/test_cmbs_user_manual.py`
   - `tests/test_reports/test_rmbs_performance.py`
   - `tests/test_reports/test_var_daily.py`
   - `tests/test_reports/test_stress_test.py`
   - `tests/test_reports/test_trading_activity.py`
   - `tests/test_reports/test_aml_alerts.py`
   - `tests/test_reports/test_focus_manual.py`

4. **Infrastructure Tests** (4 files)
   - `tests/test_infrastructure/test_config.py`
   - `tests/test_infrastructure/test_utils.py`
   - `tests/test_infrastructure/test_security.py`
   - `tests/test_infrastructure/test_performance.py`

5. **Mock and Fixture Tests** (2 files)
   - `tests/test_mocks/test_data_generators.py`
   - `tests/test_fixtures/test_report_definitions.py`

6. **Testing Infrastructure**
   - `conftest.py` - Global fixtures and configuration
   - `pytest.ini` - Pytest configuration
   - `.coveragerc` - Coverage configuration

### Coverage Requirements
- **Minimum Line Coverage:** 80%
- **Function Coverage:** 90%
- **Branch Coverage:** 75%

## Running Tests

### Command Line Options

#### Basic Test Execution
```bash
# Run all tests
pytest

# Run unit tests only (fast)
pytest -m "unit and not slow"

# Run integration tests
pytest -m "integration"

# Run performance tests
pytest -m "performance"

# Run slow tests
pytest -m "slow"
```

#### Coverage Testing
```bash
# Run with coverage reporting
pytest --cov=src --cov-report=html --cov-report=term-missing

# Coverage with threshold enforcement
pytest --cov=src --cov-fail-under=80

# Generate multiple coverage formats
pytest --cov=src --cov-report=html --cov-report=xml --cov-report=json
```

#### Parallel Execution
```bash
# Run tests in parallel
pytest -n auto

# Specify number of workers
pytest -n 4
```

#### Detailed Output
```bash
# Verbose output with timing
pytest -v --durations=10

# Show local variables on failure
pytest -v --tb=long --showlocals

# Only show test summary
pytest --tb=no -q
```

### Using Makefile

The project includes a comprehensive Makefile with predefined targets:

```bash
# Quick commands
make test          # Run all tests
make test-unit     # Run unit tests only
make coverage      # Run tests with coverage
make lint          # Run code quality checks
make clean         # Clean generated files

# Coverage variants
make coverage-html # Generate HTML coverage report
make coverage-xml  # Generate XML coverage report
make coverage-unit # Unit test coverage only

# Utility commands
make list-tests    # List all available tests
make count-tests   # Count tests by category
make validate-phase5a  # Validate Phase 5A completion
```

### Using Test Script

The project includes a comprehensive test execution script:

```bash
# Run Phase 5A test suite with default settings
./scripts/run_tests.sh

# Run with custom coverage threshold
./scripts/run_tests.sh --coverage-threshold 85

# Run with custom reports directory
./scripts/run_tests.sh --reports-dir custom_reports
```

## Test Configuration

### pytest.ini
Core pytest configuration including:
- Test discovery patterns
- Marker definitions
- Default options
- Logging configuration
- Timeout settings

### .coveragerc
Coverage analysis configuration:
- Source inclusion/exclusion
- Report formatting
- Threshold settings
- Output formats

### conftest.py
Global test fixtures including:
- Database mocks
- Sample data generators
- Configuration fixtures
- Performance utilities
- Validation helpers

## Test Development Guidelines

### Test Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Fixtures: descriptive names without `test_` prefix

### Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestComponentName:
    @pytest.fixture
    def component_instance(self):
        return ComponentName()
    
    @pytest.mark.unit
    def test_basic_functionality(self, component_instance):
        # Arrange
        input_data = "test_input"
        
        # Act
        result = component_instance.process(input_data)
        
        # Assert
        assert result is not None
        assert result.status == "success"
    
    @pytest.mark.integration
    def test_integration_scenario(self, component_instance):
        # Integration test implementation
        pass
    
    @pytest.mark.performance
    def test_performance_benchmark(self, component_instance):
        # Performance test implementation
        pass
```

### Markers
Use appropriate markers to categorize tests:
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Cross-component integration tests
- `@pytest.mark.performance` - Performance and benchmark tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.security` - Security-related tests

### Mocking Best Practices
```python
# Mock external dependencies
@patch('external_service.api_call')
def test_with_external_mock(mock_api):
    mock_api.return_value = {"status": "success"}
    # Test implementation

# Use fixtures for complex mocks
@pytest.fixture
def mock_database(mocker):
    return mocker.patch('database.connection')
```

## Coverage Analysis

### Viewing Coverage Reports

#### HTML Report (Recommended)
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

#### Terminal Report
```bash
pytest --cov=src --cov-report=term-missing
# Shows missing lines in terminal
```

#### Coverage Summary
```bash
coverage report --show-missing
coverage report --fail-under=80
```

### Interpreting Coverage Metrics

- **Line Coverage:** Percentage of code lines executed
- **Branch Coverage:** Percentage of conditional branches tested
- **Function Coverage:** Percentage of functions called

### Improving Coverage
1. Identify uncovered lines with `--cov-report=html`
2. Add tests for missing code paths
3. Focus on error handling and edge cases
4. Test both positive and negative scenarios

## Continuous Integration

### GitHub Actions Workflow
The project includes automated testing via GitHub Actions:

- **Trigger:** Push/PR to main/develop branches
- **Matrix Testing:** Python 3.9, 3.10, 3.11, 3.12
- **Coverage:** Automatic coverage reporting
- **Artifacts:** Test reports and coverage data
- **Validation:** Phase 5A completion verification

### Local CI Simulation
```bash
# Test across multiple Python versions
tox

# Run specific tox environment
tox -e py311

# Parallel tox execution
tox --parallel auto
```

## Performance Testing

### Benchmarking
```bash
# Run performance tests with benchmarking
pytest -m "performance" --benchmark-only --benchmark-sort=mean

# Generate benchmark report
pytest --benchmark-json=benchmark.json -m "performance"
```

### Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Run with memory profiling
mprof run pytest tests/test_performance/
mprof plot --output memory_profile.png
```

## Security Testing

### Security Scanning
```bash
# Run security checks
make security

# Individual security tools
bandit -r src/                    # Security linting
safety check                     # Vulnerability scanning
pip-audit                        # Package auditing
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure PYTHONPATH includes src directory
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# Or install in development mode
pip install -e .
```

#### Coverage Data Issues
```bash
# Clear coverage data
coverage erase

# Combine parallel coverage data
coverage combine

# Fix path issues in .coveragerc
```

#### Slow Test Performance
```bash
# Run only fast tests
pytest -m "unit and not slow"

# Use parallel execution
pytest -n auto

# Profile test execution
pytest --durations=10
```

### Debug Mode
```bash
# Run with debug output
pytest -v --tb=long --capture=no

# Drop into debugger on failure
pytest --pdb

# Run specific test with debugging
pytest tests/test_specific.py::test_function -v --pdb
```

## Phase 5A Validation

### Completion Checklist
- [ ] All 20 test files created
- [ ] Coverage threshold (80%) achieved
- [ ] All test categories passing
- [ ] Infrastructure files configured
- [ ] CI/CD workflow functional

### Validation Commands
```bash
# Comprehensive validation
make validate-phase5a

# Structure validation
./scripts/run_tests.sh

# CI simulation
tox
```

## Next Steps: Phase 5B

Upon successful completion of Phase 5A, proceed to:

1. **Frontend Testing** - UI component tests
2. **Integration Testing** - End-to-end workflows
3. **Performance Testing** - Load and stress testing
4. **Security Testing** - Penetration testing
5. **User Acceptance Testing** - Business validation

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [tox Documentation](https://tox.readthedocs.io/)

### Tools
- **pytest:** Testing framework
- **coverage:** Coverage analysis
- **tox:** Multi-environment testing
- **bandit:** Security linting
- **black:** Code formatting
- **flake8:** Code linting

### Support
- Review test logs in `reports/` directory
- Check GitHub Actions for CI/CD issues
- Consult project-specific documentation
- Reference Phase 5A planning documents

---

*This testing guide is maintained as part of the DataFit Phase 5A Backend Unit Testing implementation.*
#!/bin/bash
# Test execution script for DataFit Phase 5A
# Usage: ./scripts/run_tests.sh [options]

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="DataFit"
TEST_DIR="tests"
SRC_DIR="src"
COVERAGE_THRESHOLD=80
REPORTS_DIR="reports"

# Create reports directory
mkdir -p $REPORTS_DIR

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}$PROJECT_NAME - Phase 5A Backend Unit Testing${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✓ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}✗ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ $message${NC}"
            ;;
    esac
}

# Function to run tests with coverage
run_phase5a_tests() {
    print_status "INFO" "Running Phase 5A Backend Unit Tests..."
    
    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        print_status "ERROR" "pytest not found. Please install requirements-test.txt"
        exit 1
    fi
    
    # Run unit tests with coverage
    print_status "INFO" "Executing unit tests with coverage reporting..."
    
    pytest $TEST_DIR \
        --cov=$SRC_DIR \
        --cov-report=html:$REPORTS_DIR/coverage_html \
        --cov-report=xml:$REPORTS_DIR/coverage.xml \
        --cov-report=json:$REPORTS_DIR/coverage.json \
        --cov-report=term-missing \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        --html=$REPORTS_DIR/pytest_report.html \
        --self-contained-html \
        --json-report \
        --json-report-file=$REPORTS_DIR/pytest_report.json \
        --junit-xml=$REPORTS_DIR/junit.xml \
        -v \
        --tb=short \
        --durations=10 \
        -m "unit" \
        || test_exit_code=$?
    
    return ${test_exit_code:-0}
}

# Function to generate coverage summary
generate_coverage_summary() {
    print_status "INFO" "Generating coverage summary..."
    
    if [ -f ".coverage" ]; then
        # Generate text coverage report
        coverage report --show-missing > $REPORTS_DIR/coverage_summary.txt
        
        # Extract coverage percentage
        local coverage_pct=$(coverage report | tail -1 | awk '{print $4}' | sed 's/%//')
        
        echo "Coverage Percentage: $coverage_pct%" >> $REPORTS_DIR/coverage_summary.txt
        
        if (( $(echo "$coverage_pct >= $COVERAGE_THRESHOLD" | bc -l) )); then
            print_status "SUCCESS" "Coverage threshold met: $coverage_pct% >= $COVERAGE_THRESHOLD%"
        else
            print_status "WARNING" "Coverage below threshold: $coverage_pct% < $COVERAGE_THRESHOLD%"
        fi
    else
        print_status "WARNING" "No coverage data found"
    fi
}

# Function to validate test structure
validate_test_structure() {
    print_status "INFO" "Validating Phase 5A test structure..."
    
    local required_dirs=(
        "tests/test_job_submission"
        "tests/test_job_polling" 
        "tests/test_reports"
        "tests/test_infrastructure"
        "tests/test_mocks"
        "tests/test_fixtures"
    )
    
    local missing_dirs=()
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_status "SUCCESS" "Found $dir"
        else
            print_status "ERROR" "Missing $dir"
            missing_dirs+=("$dir")
        fi
    done
    
    if [ ${#missing_dirs[@]} -eq 0 ]; then
        print_status "SUCCESS" "All required test directories found"
        return 0
    else
        print_status "ERROR" "Missing test directories: ${missing_dirs[*]}"
        return 1
    fi
}

# Function to count test files
count_test_files() {
    print_status "INFO" "Counting test files..."
    
    local total_tests=$(find $TEST_DIR -name "test_*.py" | wc -l)
    local job_submission_tests=$(find tests/test_job_submission -name "test_*.py" 2>/dev/null | wc -l)
    local job_polling_tests=$(find tests/test_job_polling -name "test_*.py" 2>/dev/null | wc -l)
    local report_tests=$(find tests/test_reports -name "test_*.py" 2>/dev/null | wc -l)
    local infrastructure_tests=$(find tests/test_infrastructure -name "test_*.py" 2>/dev/null | wc -l)
    local mock_tests=$(find tests/test_mocks -name "test_*.py" 2>/dev/null | wc -l)
    local fixture_tests=$(find tests/test_fixtures -name "test_*.py" 2>/dev/null | wc -l)
    
    echo "Test File Count Summary:" > $REPORTS_DIR/test_file_count.txt
    echo "======================" >> $REPORTS_DIR/test_file_count.txt
    echo "Total test files: $total_tests" >> $REPORTS_DIR/test_file_count.txt
    echo "Job submission tests: $job_submission_tests" >> $REPORTS_DIR/test_file_count.txt
    echo "Job polling tests: $job_polling_tests" >> $REPORTS_DIR/test_file_count.txt
    echo "Report generator tests: $report_tests" >> $REPORTS_DIR/test_file_count.txt
    echo "Infrastructure tests: $infrastructure_tests" >> $REPORTS_DIR/test_file_count.txt
    echo "Mock tests: $mock_tests" >> $REPORTS_DIR/test_file_count.txt
    echo "Fixture tests: $fixture_tests" >> $REPORTS_DIR/test_file_count.txt
    
    print_status "INFO" "Total test files: $total_tests"
    
    # Validate expected file counts (based on Phase 5A plan)
    local expected_counts=(
        "job_submission:2"
        "job_polling:4" 
        "reports:7"
        "infrastructure:4"
        "mocks:1"
        "fixtures:1"
    )
    
    local validation_passed=true
    
    for expected in "${expected_counts[@]}"; do
        local category=$(echo $expected | cut -d: -f1)
        local expected_count=$(echo $expected | cut -d: -f2)
        local actual_count
        
        case $category in
            "job_submission") actual_count=$job_submission_tests ;;
            "job_polling") actual_count=$job_polling_tests ;;
            "reports") actual_count=$report_tests ;;
            "infrastructure") actual_count=$infrastructure_tests ;;
            "mocks") actual_count=$mock_tests ;;
            "fixtures") actual_count=$fixture_tests ;;
        esac
        
        if [ "$actual_count" -ge "$expected_count" ]; then
            print_status "SUCCESS" "$category tests: $actual_count >= $expected_count (expected)"
        else
            print_status "WARNING" "$category tests: $actual_count < $expected_count (expected)"
            validation_passed=false
        fi
    done
    
    return $([ "$validation_passed" = true ] && echo 0 || echo 1)
}

# Function to generate final report
generate_final_report() {
    print_status "INFO" "Generating Phase 5A completion report..."
    
    local report_file="$REPORTS_DIR/phase5a_completion_report.md"
    
    cat > $report_file << EOF
# DataFit Phase 5A Backend Unit Testing - Completion Report

## Executive Summary
This report summarizes the completion status of Phase 5A: Backend Unit Testing for the DataFit SAS Viya job execution system.

**Report Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**Project:** DataFit SAS Viya Job Execution System
**Phase:** 5A - Backend Unit Testing

## Test Structure Validation
EOF
    
    # Add test structure results
    echo "### Test Directory Structure" >> $report_file
    if validate_test_structure > /dev/null 2>&1; then
        echo "✅ **PASSED** - All required test directories are present" >> $report_file
    else
        echo "❌ **FAILED** - Some required test directories are missing" >> $report_file
    fi
    echo "" >> $report_file
    
    # Add test file counts
    echo "### Test File Count Analysis" >> $report_file
    cat $REPORTS_DIR/test_file_count.txt >> $report_file
    echo "" >> $report_file
    
    # Add coverage information
    echo "### Coverage Analysis" >> $report_file
    if [ -f "$REPORTS_DIR/coverage_summary.txt" ]; then
        cat $REPORTS_DIR/coverage_summary.txt >> $report_file
    else
        echo "Coverage data not available" >> $report_file
    fi
    echo "" >> $report_file
    
    # Add deliverables checklist
    cat >> $report_file << EOF

### Phase 5A Deliverables Checklist

#### Test Files Created (20 files total)
- [ ] Job Submission Service Tests (2 files)
  - [ ] test_models.py
  - [ ] test_utils.py
- [ ] Job Polling Service Tests (4 files)  
  - [ ] test_app.py
  - [ ] test_models.py
  - [ ] test_job_executor.py
  - [ ] test_file_manager.py
- [ ] Report Generator Tests (7 files)
  - [ ] test_cmbs_user_manual.py
  - [ ] test_rmbs_performance.py
  - [ ] test_var_daily.py
  - [ ] test_stress_test.py
  - [ ] test_trading_activity.py
  - [ ] test_aml_alerts.py
  - [ ] test_focus_manual.py
- [ ] Infrastructure Tests (4 files)
  - [ ] test_config.py
  - [ ] test_utils.py
  - [ ] test_security.py
  - [ ] test_performance.py
- [ ] Mock & Fixture Tests (2 files)
  - [ ] test_data_generators.py
  - [ ] test_report_definitions.py
- [ ] Testing Infrastructure (1 file)
  - [ ] pytest.ini configuration

#### Coverage Requirements
- [ ] 80% minimum line coverage
- [ ] 90% function coverage  
- [ ] 75% branch coverage

#### Additional Infrastructure
- [ ] pytest configuration (pytest.ini)
- [ ] Coverage configuration (.coveragerc)
- [ ] Test requirements (requirements-test.txt)
- [ ] Development Makefile
- [ ] Global test fixtures (conftest.py)
- [ ] Tox configuration (tox.ini)

## Recommendations

### Next Steps for Phase 5B
1. Frontend & Integration Testing
2. End-to-end workflow testing
3. Performance testing with realistic data volumes
4. Security testing validation
5. User acceptance testing preparation

### Continuous Improvement
1. Monitor coverage metrics and maintain >80% threshold
2. Regular test maintenance and updates
3. Integration with CI/CD pipeline
4. Automated test execution on code changes

## Technical Notes

### Test Framework Stack
- **pytest**: Primary testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Enhanced mocking capabilities
- **pytest-xdist**: Parallel test execution
- **tox**: Multi-environment testing

### Coverage Tools
- **coverage.py**: Core coverage analysis
- **HTML reports**: Interactive coverage visualization
- **XML/JSON**: Machine-readable coverage data

### Quality Assurance
- **flake8**: Code linting
- **black**: Code formatting
- **mypy**: Type checking
- **bandit**: Security analysis

---
*This report was automatically generated by the Phase 5A test execution script.*
EOF

    print_status "SUCCESS" "Final report generated: $report_file"
}

# Main execution function
main() {
    local exit_code=0
    
    print_status "INFO" "Starting Phase 5A Backend Unit Testing execution..."
    
    # Step 1: Validate test structure
    if ! validate_test_structure; then
        print_status "ERROR" "Test structure validation failed"
        exit_code=1
    fi
    
    # Step 2: Count and validate test files
    if ! count_test_files; then
        print_status "WARNING" "Test file count validation had issues"
    fi
    
    # Step 3: Run tests with coverage
    if run_phase5a_tests; then
        print_status "SUCCESS" "Phase 5A tests completed successfully"
    else
        print_status "ERROR" "Phase 5A tests failed"
        exit_code=1
    fi
    
    # Step 4: Generate coverage summary
    generate_coverage_summary
    
    # Step 5: Generate final report
    generate_final_report
    
    # Summary
    echo -e "\n${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}Phase 5A Execution Summary${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
    
    if [ $exit_code -eq 0 ]; then
        print_status "SUCCESS" "Phase 5A Backend Unit Testing completed successfully!"
        print_status "INFO" "Reports available in: $REPORTS_DIR/"
        print_status "INFO" "Coverage report: $REPORTS_DIR/coverage_html/index.html"
        print_status "INFO" "Test report: $REPORTS_DIR/pytest_report.html"
        print_status "INFO" "Completion report: $REPORTS_DIR/phase5a_completion_report.md"
    else
        print_status "ERROR" "Phase 5A Backend Unit Testing completed with issues"
        print_status "INFO" "Check reports in: $REPORTS_DIR/ for details"
    fi
    
    return $exit_code
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage-threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        --reports-dir)
            REPORTS_DIR="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --coverage-threshold N    Set coverage threshold (default: 80)"
            echo "  --reports-dir DIR         Set reports directory (default: reports)"
            echo "  --help                    Show this help message"
            exit 0
            ;;
        *)
            print_status "ERROR" "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Execute main function
main
exit $?
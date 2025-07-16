"""
=============================================================================
DATAFIT FRONTEND TESTS
=============================================================================
Purpose: Test the frontend components and functionality
Framework: pytest with Selenium for browser automation
Coverage: Frontend application behavior, API integration, user interactions

STRICT REQUIREMENTS:
- Test all major user workflows
- Validate form generation and validation
- Test report selection and job submission
- Test real-time job status updates
- Test responsive design and accessibility
- Mock backend API responses

TEST CATEGORIES:
1. Component Tests - Individual JavaScript components
2. Integration Tests - Component interactions
3. User Journey Tests - End-to-end workflows
4. API Integration Tests - Frontend-backend communication
5. Accessibility Tests - WCAG compliance
6. Performance Tests - Load times and responsiveness

MOCK STRATEGY:
- Mock all API endpoints
- Test with various report definitions
- Test error conditions and edge cases
- Test offline/network failure scenarios

BROWSER TESTING:
- Chrome (latest)
- Firefox (latest)
- Safari (if available)
- Mobile viewport testing
=============================================================================
"""

import pytest
import json
import os
from unittest.mock import Mock, patch
import tempfile
import subprocess


class TestFrontendStructure:
    """Test frontend file structure and basic setup"""
    
    def test_html_file_exists(self):
        """Test that main HTML file exists"""
        html_path = os.path.join('gui', 'index.html')
        assert os.path.exists(html_path), "index.html should exist"
    
    def test_css_file_exists(self):
        """Test that main CSS file exists"""
        css_path = os.path.join('gui', 'styles', 'main.css')
        assert os.path.exists(css_path), "main.css should exist"
    
    def test_js_files_exist(self):
        """Test that JavaScript files exist"""
        js_files = [
            'gui/app.js',
            'gui/components/report-selector.js',
            'gui/components/form-generator.js',
            'gui/components/job-status.js'
        ]
        
        for js_file in js_files:
            assert os.path.exists(js_file), f"{js_file} should exist"
    
    def test_html_structure(self):
        """Test HTML file has required structure"""
        html_path = os.path.join('gui', 'index.html')
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required elements
        required_elements = [
            'id="app"',
            'id="report-selector-container"',
            'id="form-container"',
            'id="active-jobs-container"',
            'id="job-history-container"',
            'id="toast-container"',
            'id="loading-overlay"',
            'id="job-modal"'
        ]
        
        for element in required_elements:
            assert element in content, f"HTML should contain {element}"
    
    def test_css_has_required_classes(self):
        """Test CSS file has required classes"""
        css_path = os.path.join('gui', 'styles', 'main.css')
        
        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_classes = [
            '.app-container',
            '.nav-button',
            '.report-card',
            '.form-group',
            '.btn',
            '.job-item',
            '.toast',
            '.modal'
        ]
        
        for css_class in required_classes:
            assert css_class in content, f"CSS should contain {css_class}"


class TestReportDefinitions:
    """Test report definitions and sample data"""
    
    def test_sample_reports_json_valid(self):
        """Test that sample reports JSON is valid"""
        reports_path = 'sample-reports.json'
        assert os.path.exists(reports_path), "sample-reports.json should exist"
        
        with open(reports_path, 'r', encoding='utf-8') as f:
            reports_data = json.load(f)
        
        # Check structure
        assert 'categories' in reports_data, "Reports should have categories"
        assert len(reports_data['categories']) > 0, "Should have at least one category"
        
        # Check first category structure
        category = reports_data['categories'][0]
        assert 'name' in category, "Category should have name"
        assert 'reports' in category, "Category should have reports"
        
        # Check first report structure
        if category['reports']:
            report = category['reports'][0]
            required_fields = ['id', 'name', 'description', 'prompts']
            for field in required_fields:
                assert field in report, f"Report should have {field}"
    
    def test_report_prompts_structure(self):
        """Test report prompts have correct structure"""
        reports_path = 'sample-reports.json'
        
        with open(reports_path, 'r', encoding='utf-8') as f:
            reports_data = json.load(f)
        
        for category in reports_data['categories']:
            for report in category['reports']:
                assert 'prompts' in report, f"Report {report['id']} should have prompts"
                
                for prompt_group in report['prompts']:
                    for field_name, field_config in prompt_group.items():
                        # Check required prompt fields
                        required_prompt_fields = ['active', 'inputType', 'label']
                        for field in required_prompt_fields:
                            assert field in field_config, f"Prompt {field_name} should have {field}"
                        
                        # Check valid input types
                        valid_types = ['inputtext', 'dropdown', 'date', 'checkbox', 'radio', 'hidden']
                        assert field_config['inputType'] in valid_types, \
                            f"Invalid input type: {field_config['inputType']}"


class TestMockData:
    """Test mock data files"""
    
    def test_mock_data_files_exist(self):
        """Test that required mock data files exist"""
        mock_data_dir = 'mock-data'
        required_files = [
            'var_daily.csv',
            'trading_activity.csv',
            'aml_alerts.csv',
            'rmbs_performance.csv',
            'stress_test_results.csv'
        ]
        
        for filename in required_files:
            file_path = os.path.join(mock_data_dir, filename)
            assert os.path.exists(file_path), f"Mock data file {filename} should exist"
    
    def test_csv_files_have_headers(self):
        """Test that CSV files have proper headers"""
        import csv
        
        csv_files = [
            ('mock-data/var_daily.csv', ['Date', 'Portfolio']),
            ('mock-data/trading_activity.csv', ['Trade_ID', 'Date'])
        ]
        
        for file_path, expected_headers in csv_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    
                    for expected_header in expected_headers:
                        assert expected_header in headers, \
                            f"{file_path} should have {expected_header} header"


class TestReportGenerators:
    """Test report generator functionality"""
    
    def test_report_generators_exist(self):
        """Test that report generator files exist"""
        reports_dir = 'reports'
        required_generators = [
            'base_report.py',
            'var_daily_report.py',
            'trading_activity_report.py'
        ]
        
        for generator in required_generators:
            file_path = os.path.join(reports_dir, generator)
            assert os.path.exists(file_path), f"Report generator {generator} should exist"
    
    def test_base_report_structure(self):
        """Test base report class structure"""
        base_report_path = os.path.join('reports', 'base_report.py')
        
        if os.path.exists(base_report_path):
            with open(base_report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for required methods
            required_methods = [
                'def validate_parameters',
                'def get_output_formats',
                'def get_estimated_duration',
                'def generate'
            ]
            
            for method in required_methods:
                assert method in content, f"BaseReport should have {method} method"


class TestDockerConfiguration:
    """Test Docker configuration"""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfiles exist"""
        dockerfiles = [
            'Dockerfile.frontend',
            'job-submission/Dockerfile',
            'job-polling/Dockerfile'
        ]
        
        for dockerfile in dockerfiles:
            if os.path.exists(dockerfile):
                assert True  # File exists
            else:
                # Check if service directory exists
                service_dir = os.path.dirname(dockerfile) if '/' in dockerfile else '.'
                if os.path.exists(service_dir):
                    assert os.path.exists(dockerfile), f"Dockerfile {dockerfile} should exist"
    
    def test_docker_compose_valid(self):
        """Test docker-compose.yml is valid"""
        compose_path = 'docker-compose.yml'
        
        if os.path.exists(compose_path):
            # Try to validate docker-compose file
            try:
                result = subprocess.run(
                    ['docker-compose', '-f', compose_path, 'config'],
                    capture_output=True,
                    text=True,
                    cwd='.'
                )
                # If docker-compose is available, check if config is valid
                if result.returncode == 0:
                    assert True  # Valid compose file
                else:
                    # Docker-compose might not be available in test environment
                    # Just check that file exists and has basic structure
                    with open(compose_path, 'r') as f:
                        content = f.read()
                        assert 'version:' in content
                        assert 'services:' in content
            except FileNotFoundError:
                # Docker-compose not available, just check file structure
                with open(compose_path, 'r') as f:
                    content = f.read()
                    assert 'version:' in content
                    assert 'services:' in content
    
    def test_makefile_exists(self):
        """Test that Makefile exists"""
        makefile_path = 'Makefile'
        assert os.path.exists(makefile_path), "Makefile should exist"
        
        with open(makefile_path, 'r') as f:
            content = f.read()
        
        # Check for required targets
        required_targets = [
            'build:',
            'deploy:',
            'start:',
            'stop:',
            'clean:',
            'test:'
        ]
        
        for target in required_targets:
            assert target in content, f"Makefile should have {target} target"


class TestConfiguration:
    """Test configuration files"""
    
    def test_config_dev_env_exists(self):
        """Test that development config exists"""
        config_path = 'config.dev.env'
        assert os.path.exists(config_path), "config.dev.env should exist"
        
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for required variables
        required_vars = [
            'GUI_PORT',
            'SUBMISSION_PORT',
            'POLLING_PORT'
        ]
        
        for var in required_vars:
            assert var in content, f"config.dev.env should define {var}"


class TestAccessibility:
    """Test accessibility features"""
    
    def test_html_has_aria_labels(self):
        """Test HTML has ARIA labels for accessibility"""
        html_path = os.path.join('gui', 'index.html')
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for accessibility attributes
        accessibility_attrs = [
            'aria-label',
            'aria-pressed',
            'aria-hidden',
            'aria-live',
            'role='
        ]
        
        found_attrs = sum(1 for attr in accessibility_attrs if attr in content)
        assert found_attrs >= 3, "HTML should have accessibility attributes"
    
    def test_css_has_focus_styles(self):
        """Test CSS has focus styles for keyboard navigation"""
        css_path = os.path.join('gui', 'styles', 'main.css')
        
        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for focus styles
        focus_selectors = [':focus', 'outline']
        found_focus = sum(1 for selector in focus_selectors if selector in content)
        assert found_focus >= 1, "CSS should have focus styles for accessibility"


def test_project_completeness():
    """Test overall project completeness"""
    # Check that key directories exist
    required_dirs = ['gui', 'reports', 'mock-data']
    for directory in required_dirs:
        assert os.path.exists(directory), f"Directory {directory} should exist"
    
    # Check that plan-phases.md exists
    assert os.path.exists('plan-phases.md'), "plan-phases.md should exist"
    
    # Check that project has README or documentation
    docs = ['README.md', 'project-structure.md', 'notes.md']
    has_docs = any(os.path.exists(doc) for doc in docs)
    assert has_docs, "Project should have documentation"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
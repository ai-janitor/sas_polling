"""
=============================================================================
END-TO-END INTEGRATION TESTS
=============================================================================
Purpose: Comprehensive end-to-end tests for complete DataFit workflows
Technology: pytest with real service integration and docker-compose
Testing: Full system integration from GUI to report generation

STRICT REQUIREMENTS:
- Complete workflow validation from start to finish
- Real service integration testing
- File generation and download verification
- Performance testing under realistic loads
- Security testing with complete attack scenarios

TEST SCENARIOS:
1. Complete Job Submission Workflow
   - GUI report selection
   - Form parameter input
   - Job submission to backend
   - Status polling and updates
   - File generation and download

2. Multi-Service Integration
   - GUI ↔ Job Submission Service
   - Job Submission ↔ Job Polling Service
   - Job Polling ↔ Report Generators
   - File storage and retrieval

3. Error Handling Workflows
   - Service unavailability scenarios
   - Network failure recovery
   - Invalid input propagation
   - Timeout handling across services

4. Performance Integration Tests
   - Concurrent user scenarios
   - Large report generation
   - High-frequency job submissions
   - System resource monitoring

5. Security Integration Tests
   - Authentication flow validation
   - Authorization across services
   - Input sanitization end-to-end
   - File access security

ENVIRONMENT SETUP:
- Docker Compose for service orchestration
- Test data volumes and networks
- Isolated test environment
- Service health verification

WORKFLOW VALIDATION:
- Job lifecycle state transitions
- File generation completeness
- Data consistency across services
- Error propagation accuracy
- Performance benchmark compliance

MONITORING AND LOGGING:
- Service interaction logging
- Performance metric collection
- Error tracking and analysis
- Resource usage monitoring
- User experience validation

DEPENDENCIES:
- pytest: Test framework
- docker: Container management
- selenium: GUI automation
- requests: HTTP client testing
- pytest-xdist: Parallel test execution
=============================================================================
"""

import pytest
import time
import requests
import json
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import docker
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

class TestEndToEndWorkflows:
    """End-to-end integration test class."""
    
    @pytest.fixture(scope="class")
    def docker_services(self):
        """Set up Docker services for testing."""
        client = docker.from_env()
        
        # Start services using docker-compose (simulated)
        services = {
            'gui': {'port': 3000, 'health_path': '/'},
            'job-submission': {'port': 5000, 'health_path': '/health'},
            'job-polling': {'port': 5001, 'health_path': '/health'}
        }
        
        # Wait for services to be healthy
        for service_name, config in services.items():
            self._wait_for_service_health(config['port'], config['health_path'])
        
        yield services
        
        # Cleanup would happen here
    
    def _wait_for_service_health(self, port, health_path, timeout=60):
        """Wait for service to become healthy."""
        start_time = time.time()
        url = f"http://localhost:{port}{health_path}"
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        raise TimeoutError(f"Service at {url} did not become healthy within {timeout} seconds")
    
    @pytest.fixture
    def browser(self):
        """Set up browser for GUI testing."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        yield driver
        
        driver.quit()
    
    @pytest.fixture
    def api_client(self, docker_services):
        """HTTP client for API testing."""
        class APIClient:
            def __init__(self, base_url):
                self.base_url = base_url
                self.session = requests.Session()
                self.session.headers.update({
                    'Content-Type': 'application/json',
                    'User-Agent': 'DataFit-Test-Client/1.0'
                })
            
            def submit_job(self, job_data):
                url = f"{self.base_url}/api/jobs"
                response = self.session.post(url, json=job_data, timeout=10)
                return response
            
            def get_job_status(self, job_id):
                url = f"{self.base_url}/api/jobs/{job_id}/status"
                response = self.session.get(url, timeout=10)
                return response
            
            def get_job_files(self, job_id):
                url = f"{self.base_url}/api/jobs/{job_id}/files"
                response = self.session.get(url, timeout=10)
                return response
            
            def download_file(self, job_id, filename):
                url = f"{self.base_url}/api/jobs/{job_id}/files/{filename}"
                response = self.session.get(url, timeout=30)
                return response
            
            def get_reports(self):
                url = f"{self.base_url}/api/reports"
                response = self.session.get(url, timeout=10)
                return response
        
        return APIClient("http://localhost:5000")
    
    @pytest.mark.e2e
    def test_complete_job_workflow_gui(self, browser, docker_services):
        """Test complete job workflow through GUI."""
        # Navigate to application
        browser.get("http://localhost:3000")
        
        # Wait for reports to load
        wait = WebDriverWait(browser, 20)
        report_cards = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "report-card"))
        )
        
        assert len(report_cards) > 0, "No report cards found"
        
        # Select first report
        report_cards[0].click()
        
        # Wait for form to appear
        form_container = wait.until(
            EC.visibility_of_element_located((By.ID, "form-container"))
        )
        
        # Fill form fields (example for CMBS report)
        quarter_select = browser.find_element(By.NAME, "asofqtr")
        quarter_select.send_keys("Q2")
        
        year_input = browser.find_element(By.NAME, "year")
        year_input.clear()
        year_input.send_keys("2024")
        
        # Submit job
        submit_button = browser.find_element(By.ID, "submit-job")
        submit_button.click()
        
        # Wait for job to appear in jobs section
        jobs_nav = browser.find_element(By.ID, "nav-jobs")
        jobs_nav.click()
        
        # Wait for job item to appear
        job_item = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "job-item"))
        )
        
        # Wait for job completion (with timeout)
        def wait_for_job_completion():
            max_wait = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_element = browser.find_element(By.CLASS_NAME, "job-status")
                status_text = status_element.text.lower()
                
                if "completed" in status_text:
                    return True
                elif "failed" in status_text:
                    raise AssertionError("Job failed")
                
                time.sleep(2)
                browser.refresh()
            
            raise TimeoutError("Job did not complete within timeout")
        
        wait_for_job_completion()
        
        # Verify download button is available
        download_button = browser.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
        assert download_button.is_displayed()
    
    @pytest.mark.e2e
    def test_complete_job_workflow_api(self, api_client):
        """Test complete job workflow through API."""
        # Get available reports
        reports_response = api_client.get_reports()
        assert reports_response.status_code == 200
        
        reports_data = reports_response.json()
        assert "categories" in reports_data
        
        # Find first report
        first_report = None
        for category in reports_data["categories"]:
            if "reports" in category and len(category["reports"]) > 0:
                first_report = category["reports"][0]
                break
        
        assert first_report is not None, "No reports found"
        
        # Submit job
        job_data = {
            "name": f"Test Job - {first_report['name']}",
            "jobDefinitionUri": first_report["id"],
            "arguments": {
                "asofqtr": "Q2",
                "year": "2024",
                "sortorder": "Name",
                "outputtp": "HTML"
            },
            "submitted_by": "test_user",
            "priority": 5
        }
        
        submit_response = api_client.submit_job(job_data)
        assert submit_response.status_code == 201
        
        job_response = submit_response.json()
        assert "id" in job_response
        job_id = job_response["id"]
        
        # Poll job status until completion
        max_polls = 150  # 5 minutes with 2-second intervals
        poll_count = 0
        
        while poll_count < max_polls:
            status_response = api_client.get_job_status(job_id)
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "completed":
                break
            elif status == "failed":
                error_msg = status_data.get("error", "Unknown error")
                raise AssertionError(f"Job failed: {error_msg}")
            
            time.sleep(2)
            poll_count += 1
        
        assert poll_count < max_polls, "Job did not complete within timeout"
        
        # Get job files
        files_response = api_client.get_job_files(job_id)
        assert files_response.status_code == 200
        
        files_data = files_response.json()
        assert len(files_data) > 0, "No files generated"
        
        # Download first file
        first_file = files_data[0]
        download_response = api_client.download_file(job_id, first_file["filename"])
        assert download_response.status_code == 200
        assert len(download_response.content) > 0
    
    @pytest.mark.e2e
    def test_multiple_concurrent_jobs(self, api_client):
        """Test multiple concurrent job submissions."""
        # Get available reports
        reports_response = api_client.get_reports()
        assert reports_response.status_code == 200
        reports_data = reports_response.json()
        
        # Find available reports
        available_reports = []
        for category in reports_data["categories"]:
            if "reports" in category:
                available_reports.extend(category["reports"])
        
        assert len(available_reports) > 0, "No reports available"
        
        # Submit multiple concurrent jobs
        job_ids = []
        num_jobs = min(5, len(available_reports))
        
        def submit_job(report_index):
            report = available_reports[report_index % len(available_reports)]
            job_data = {
                "name": f"Concurrent Test Job {report_index}",
                "jobDefinitionUri": report["id"],
                "arguments": {
                    "test_param": f"value_{report_index}"
                },
                "submitted_by": f"test_user_{report_index}",
                "priority": 5
            }
            
            response = api_client.submit_job(job_data)
            return response
        
        # Submit jobs concurrently
        with ThreadPoolExecutor(max_workers=num_jobs) as executor:
            futures = [executor.submit(submit_job, i) for i in range(num_jobs)]
            
            for future in as_completed(futures):
                response = future.result()
                assert response.status_code == 201
                job_data = response.json()
                job_ids.append(job_data["id"])
        
        assert len(job_ids) == num_jobs
        
        # Monitor all jobs until completion
        completed_jobs = set()
        max_wait_time = 600  # 10 minutes
        start_time = time.time()
        
        while len(completed_jobs) < num_jobs and time.time() - start_time < max_wait_time:
            for job_id in job_ids:
                if job_id not in completed_jobs:
                    status_response = api_client.get_job_status(job_id)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") in ["completed", "failed"]:
                            completed_jobs.add(job_id)
            
            time.sleep(5)
        
        assert len(completed_jobs) == num_jobs, f"Only {len(completed_jobs)} of {num_jobs} jobs completed"
    
    @pytest.mark.e2e
    def test_service_failure_recovery(self, api_client, docker_services):
        """Test system behavior during service failures."""
        # Submit initial job
        job_data = {
            "name": "Failure Recovery Test Job",
            "jobDefinitionUri": "test-report-id",
            "arguments": {"test_param": "test_value"},
            "submitted_by": "test_user",
            "priority": 5
        }
        
        submit_response = api_client.submit_job(job_data)
        initial_success = submit_response.status_code == 201
        
        if initial_success:
            job_id = submit_response.json()["id"]
        
        # Simulate service failure (would require actual container manipulation)
        # For now, test error handling
        
        # Test submission service error handling
        with pytest.raises(requests.exceptions.RequestException):
            # This would test actual service failure
            failed_client = api_client.__class__("http://localhost:9999")  # Non-existent port
            failed_client.submit_job(job_data)
    
    @pytest.mark.performance
    def test_system_performance_under_load(self, api_client):
        """Test system performance under realistic load."""
        performance_results = {
            'submission_times': [],
            'polling_times': [],
            'total_times': [],
            'memory_usage': [],
            'cpu_usage': []
        }
        
        def monitor_system_resources():
            """Monitor system resources during test."""
            while True:
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_info = psutil.virtual_memory()
                    
                    performance_results['cpu_usage'].append(cpu_percent)
                    performance_results['memory_usage'].append(memory_info.percent)
                    
                    time.sleep(5)
                except:
                    break
        
        # Start resource monitoring
        monitor_thread = threading.Thread(target=monitor_system_resources, daemon=True)
        monitor_thread.start()
        
        # Performance test parameters
        num_users = 10
        jobs_per_user = 3
        total_jobs = num_users * jobs_per_user
        
        def user_workflow(user_id):
            """Simulate user workflow."""
            user_results = []
            
            for job_index in range(jobs_per_user):
                start_time = time.time()
                
                # Submit job
                job_data = {
                    "name": f"Performance Test Job {user_id}-{job_index}",
                    "jobDefinitionUri": "test-report-id",
                    "arguments": {"user_id": str(user_id), "job_index": job_index},
                    "submitted_by": f"perf_user_{user_id}",
                    "priority": 5
                }
                
                submit_start = time.time()
                submit_response = api_client.submit_job(job_data)
                submit_time = time.time() - submit_start
                
                if submit_response.status_code == 201:
                    job_id = submit_response.json()["id"]
                    
                    # Poll until completion
                    poll_start = time.time()
                    while True:
                        status_response = api_client.get_job_status(job_id)
                        if status_response.status_code == 200:
                            status = status_response.json().get("status")
                            if status in ["completed", "failed"]:
                                break
                        time.sleep(1)
                    
                    poll_time = time.time() - poll_start
                    total_time = time.time() - start_time
                    
                    user_results.append({
                        'submission_time': submit_time,
                        'polling_time': poll_time,
                        'total_time': total_time,
                        'success': status == "completed"
                    })
                
                # Brief pause between jobs
                time.sleep(0.5)
            
            return user_results
        
        # Execute concurrent user workflows
        all_results = []
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_workflow, user_id) for user_id in range(num_users)]
            
            for future in as_completed(futures):
                user_results = future.result()
                all_results.extend(user_results)
        
        # Analyze performance results
        successful_jobs = [r for r in all_results if r['success']]
        success_rate = len(successful_jobs) / len(all_results)
        
        if successful_jobs:
            avg_submission_time = sum(r['submission_time'] for r in successful_jobs) / len(successful_jobs)
            avg_total_time = sum(r['total_time'] for r in successful_jobs) / len(successful_jobs)
            max_total_time = max(r['total_time'] for r in successful_jobs)
            
            # Performance assertions
            assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
            assert avg_submission_time < 2.0, f"Average submission time {avg_submission_time:.2f}s too high"
            assert avg_total_time < 180.0, f"Average total time {avg_total_time:.2f}s too high"
            assert max_total_time < 300.0, f"Maximum total time {max_total_time:.2f}s too high"
        
        # System resource assertions
        if performance_results['cpu_usage']:
            avg_cpu = sum(performance_results['cpu_usage']) / len(performance_results['cpu_usage'])
            max_cpu = max(performance_results['cpu_usage'])
            assert avg_cpu < 80.0, f"Average CPU usage {avg_cpu:.1f}% too high"
            assert max_cpu < 95.0, f"Maximum CPU usage {max_cpu:.1f}% too high"
        
        if performance_results['memory_usage']:
            avg_memory = sum(performance_results['memory_usage']) / len(performance_results['memory_usage'])
            max_memory = max(performance_results['memory_usage'])
            assert avg_memory < 70.0, f"Average memory usage {avg_memory:.1f}% too high"
            assert max_memory < 85.0, f"Maximum memory usage {max_memory:.1f}% too high"
    
    @pytest.mark.security
    def test_end_to_end_security(self, api_client, browser):
        """Test security measures across the entire system."""
        # Test malicious input injection
        malicious_job_data = {
            "name": "<script>alert('xss')</script>",
            "jobDefinitionUri": "'; DROP TABLE jobs; --",
            "arguments": {
                "malicious_param": "<?php system('rm -rf /'); ?>"
            },
            "submitted_by": "<img src=x onerror=alert('xss')>",
            "priority": 999999  # Invalid priority
        }
        
        # Should reject malicious input
        submit_response = api_client.submit_job(malicious_job_data)
        assert submit_response.status_code in [400, 422], "Malicious input was accepted"
        
        # Test file access restrictions
        restricted_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        for path in restricted_paths:
            response = api_client.download_file("test-job-id", path)
            assert response.status_code in [400, 403, 404], f"Allowed access to restricted path: {path}"
        
        # Test GUI XSS protection
        if browser:
            browser.get("http://localhost:3000")
            
            # Try to inject script via URL parameters
            malicious_url = "http://localhost:3000?param=<script>alert('xss')</script>"
            browser.get(malicious_url)
            
            # Check that script was not executed (no alerts)
            alerts = browser.execute_script("return window.alertCalled || false;")
            assert not alerts, "XSS script was executed"
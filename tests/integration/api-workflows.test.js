/*
=============================================================================
API WORKFLOW INTEGRATION TESTS
=============================================================================
Purpose: Test complete API workflows between frontend and backend services
Coverage: End-to-end API communication, data flow, error handling
Environment: Integration testing with mocked backend services

TEST SCENARIOS:
1. Complete job submission workflow
2. Report loading and caching
3. Job status polling lifecycle
4. File download workflows
5. Error handling and recovery
6. Service communication patterns
7. Data validation across services
8. Timeout and retry mechanisms

INTEGRATION STRATEGY:
- Mock backend API responses
- Test complete user workflows
- Validate data consistency
- Test error propagation
- Performance and timing validation
=============================================================================
*/

describe('API Workflow Integration Tests', () => {
  let mockApp;

  beforeEach(() => {
    // Setup complete application DOM
    document.body.innerHTML = `
      <div id="app" class="app-container">
        <header class="app-header">
          <h1 class="app-title">DataFit</h1>
          <nav class="header-nav">
            <button id="nav-reports" class="nav-button active">Reports</button>
            <button id="nav-jobs" class="nav-button">Jobs</button>
            <button id="nav-history" class="nav-button">History</button>
          </nav>
        </header>
        <main class="main-content">
          <section id="report-section" class="content-section active">
            <div class="report-selector-container">
              <select id="report-dropdown"></select>
              <div id="selected-report-info">
                <h3 id="selected-report-title"></h3>
                <p id="selected-report-description"></p>
              </div>
            </div>
            <div id="form-container" style="display: none;">
              <form id="job-form">
                <div class="form-fields"></div>
                <button type="submit" class="btn btn-primary">Submit Job</button>
                <button type="button" id="reset-form" class="btn btn-secondary">Reset</button>
              </form>
            </div>
          </section>
          <section id="jobs-section" class="content-section">
            <div id="active-jobs-container"></div>
          </section>
          <section id="history-section" class="content-section">
            <div id="job-history-container"></div>
          </section>
        </main>
        <div id="loading-overlay" style="display: none;">
          <div id="loading-message"></div>
        </div>
        <div id="toast-container"></div>
        <div id="job-modal" style="display: none;">
          <div class="modal-backdrop"></div>
          <div class="modal-content">
            <button class="modal-close">&times;</button>
            <div id="modal-body"></div>
          </div>
        </div>
      </div>
    `;

    // Import and initialize main application
    const { DataFitApp } = require('../../gui/app.js');
    mockApp = new DataFitApp();
  });

  afterEach(() => {
    if (mockApp && mockApp.destroy) {
      mockApp.destroy();
    }
    jest.clearAllMocks();
  });

  describe('Application Initialization Workflow', () => {
    test('should complete full initialization sequence', async () => {
      const mockReportsData = global.generateMockReportsData();
      global.mockFetchSuccess(mockReportsData);

      await mockApp.init();

      // Verify reports loaded
      expect(mockApp.state.reports).toEqual(mockReportsData);
      
      // Verify UI updated
      const reportDropdown = document.getElementById('report-dropdown');
      expect(reportDropdown.children.length).toBeGreaterThan(0);
      
      // Verify current view set
      expect(mockApp.currentView).toBe('reports');
    });

    test('should handle initialization failure gracefully', async () => {
      global.mockFetchNetworkError();

      const showToastSpy = jest.spyOn(mockApp, 'showToast').mockImplementation();

      await mockApp.init();

      expect(showToastSpy).toHaveBeenCalledWith(
        'Failed to initialize application',
        'error'
      );

      showToastSpy.mockRestore();
    });

    test('should retry initialization on failure', async () => {
      // First call fails, second succeeds
      global.fetch
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce(global.mockFetchResponse(global.generateMockReportsData()));

      await mockApp.init();

      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(mockApp.state.reports).toBeTruthy();
    });
  });

  describe('Report Selection Workflow', () => {
    beforeEach(async () => {
      const mockReportsData = global.generateMockReportsData();
      global.mockFetchSuccess(mockReportsData);
      await mockApp.init();
    });

    test('should complete report selection and form generation', () => {
      const mockReport = global.generateMockReport();
      
      // Simulate report selection
      mockApp.onReportSelected(mockReport);

      // Verify report selected
      expect(mockApp.state.currentReport).toEqual(mockReport);
      
      // Verify form container shown
      const formContainer = document.getElementById('form-container');
      expect(formContainer.style.display).toBe('block');
      
      // Verify form fields generated
      const formFields = document.querySelector('.form-fields');
      expect(formFields.children.length).toBeGreaterThan(0);
    });

    test('should update UI elements on report selection', () => {
      const mockReport = global.generateMockReport();
      
      mockApp.onReportSelected(mockReport);

      const titleElement = document.getElementById('selected-report-title');
      const descriptionElement = document.getElementById('selected-report-description');

      expect(titleElement.textContent).toBe(mockReport.name);
      expect(descriptionElement.textContent).toBe(mockReport.description);
    });

    test('should validate form generation matches report schema', () => {
      const mockReport = {
        id: 'complex_report',
        name: 'Complex Report',
        description: 'Report with multiple field types',
        prompts: [{
          text_field: {
            active: true,
            inputType: 'inputtext',
            label: 'Text Field',
            required: true
          },
          dropdown_field: {
            active: true,
            inputType: 'dropdown',
            label: 'Dropdown Field',
            options: [
              { value: 'opt1', label: 'Option 1' },
              { value: 'opt2', label: 'Option 2' }
            ]
          },
          date_field: {
            active: true,
            inputType: 'date',
            label: 'Date Field'
          }
        }]
      };

      mockApp.onReportSelected(mockReport);

      const textInput = document.querySelector('input[type="text"]');
      const selectInput = document.querySelector('select');
      const dateInput = document.querySelector('input[type="date"]');

      expect(textInput).toBeTruthy();
      expect(selectInput).toBeTruthy();
      expect(dateInput).toBeTruthy();
      expect(selectInput.children.length).toBe(3); // Including default option
    });
  });

  describe('Job Submission Workflow', () => {
    beforeEach(async () => {
      const mockReportsData = global.generateMockReportsData();
      global.mockFetchSuccess(mockReportsData);
      await mockApp.init();

      const mockReport = global.generateMockReport();
      mockApp.onReportSelected(mockReport);
    });

    test('should complete successful job submission', async () => {
      const mockJob = global.generateMockJob();
      global.mockFetchSuccess(mockJob);

      // Fill form data
      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'TestValue';

      // Submit form
      const form = document.getElementById('job-form');
      const submitEvent = new Event('submit', { bubbles: true });
      
      const preventDefaultSpy = jest.fn();
      submitEvent.preventDefault = preventDefaultSpy;

      await mockApp.handleJobSubmit(submitEvent);

      expect(preventDefaultSpy).toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/jobs',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: expect.stringContaining('TestValue')
        })
      );
    });

    test('should validate form before submission', async () => {
      const showToastSpy = jest.spyOn(mockApp, 'showToast').mockImplementation();

      // Submit form without filling required fields
      const form = document.getElementById('job-form');
      const submitEvent = new Event('submit', { bubbles: true });
      submitEvent.preventDefault = jest.fn();

      await mockApp.handleJobSubmit(submitEvent);

      expect(showToastSpy).toHaveBeenCalledWith(
        'Please fix form errors',
        'error'
      );

      showToastSpy.mockRestore();
    });

    test('should handle job submission failure', async () => {
      global.mockFetchError(500, 'Server Error');

      const showToastSpy = jest.spyOn(mockApp, 'showToast').mockImplementation();

      // Fill form data
      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'TestValue';

      // Submit form
      const submitEvent = new Event('submit', { bubbles: true });
      submitEvent.preventDefault = jest.fn();

      await mockApp.handleJobSubmit(submitEvent);

      expect(showToastSpy).toHaveBeenCalledWith(
        'Failed to submit job',
        'error'
      );

      showToastSpy.mockRestore();
    });

    test('should start job polling after successful submission', async () => {
      const mockJob = global.generateMockJob();
      global.mockFetchSuccess(mockJob);

      const startPollingSpy = jest.spyOn(mockApp, 'startJobPolling').mockImplementation();

      // Fill and submit form
      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'TestValue';

      const submitEvent = new Event('submit', { bubbles: true });
      submitEvent.preventDefault = jest.fn();

      await mockApp.handleJobSubmit(submitEvent);

      expect(startPollingSpy).toHaveBeenCalledWith(mockJob.id);
      expect(mockApp.state.activeJobs.has(mockJob.id)).toBe(true);

      startPollingSpy.mockRestore();
    });
  });

  describe('Job Status Polling Workflow', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    test('should poll job status until completion', async () => {
      const jobId = 'test-job-123';
      const runningJob = global.generateMockJob({ 
        id: jobId, 
        status: 'running' 
      });
      const completedJob = global.generateMockJob({ 
        id: jobId, 
        status: 'completed' 
      });

      // First poll returns running, second returns completed
      global.fetch
        .mockResolvedValueOnce(global.mockFetchResponse(runningJob))
        .mockResolvedValueOnce(global.mockFetchResponse(completedJob));

      const moveJobToHistorySpy = jest.spyOn(mockApp, 'moveJobToHistory').mockImplementation();

      mockApp.startJobPolling(jobId);

      // First poll - job still running
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      expect(global.fetch).toHaveBeenCalledWith(
        `/api/jobs/${jobId}/status`,
        expect.any(Object)
      );

      // Second poll - job completed
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      expect(moveJobToHistorySpy).toHaveBeenCalledWith(completedJob);

      moveJobToHistorySpy.mockRestore();
    });

    test('should implement exponential backoff in polling', async () => {
      const jobId = 'test-job-123';
      const runningJob = global.generateMockJob({ 
        id: jobId, 
        status: 'running' 
      });

      global.mockFetchSuccess(runningJob);

      mockApp.startJobPolling(jobId);

      // First poll at 2 seconds
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      // Second poll at 4 seconds (2 * 2)
      jest.advanceTimersByTime(4000);
      await Promise.resolve();

      // Third poll at 8 seconds (4 * 2)
      jest.advanceTimersByTime(8000);
      await Promise.resolve();

      expect(global.fetch).toHaveBeenCalledTimes(3);
    });

    test('should handle polling errors with retry', async () => {
      const jobId = 'test-job-123';

      // First call fails, second succeeds
      global.fetch
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce(global.mockFetchResponse(
          global.generateMockJob({ id: jobId, status: 'running' })
        ));

      mockApp.startJobPolling(jobId);

      // First attempt fails
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      // Retry succeeds
      jest.advanceTimersByTime(4000); // Exponential backoff
      await Promise.resolve();

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    test('should stop polling when job completes', async () => {
      const jobId = 'test-job-123';
      const completedJob = global.generateMockJob({ 
        id: jobId, 
        status: 'completed' 
      });

      global.mockFetchSuccess(completedJob);

      mockApp.startJobPolling(jobId);

      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      expect(mockApp.pollingIntervals.has(jobId)).toBe(false);
    });
  });

  describe('File Download Workflow', () => {
    test('should load job files list', async () => {
      const jobId = 'test-job-123';
      const mockFiles = [
        { filename: 'report.html', size: 12345, type: 'HTML' },
        { filename: 'data.csv', size: 6789, type: 'CSV' }
      ];

      global.mockFetchSuccess(mockFiles);

      const files = await mockApp.loadJobFiles(jobId);

      expect(files).toEqual(mockFiles);
      expect(global.fetch).toHaveBeenCalledWith(
        `/api/jobs/${jobId}/files`,
        expect.any(Object)
      );
    });

    test('should handle file download with blob response', async () => {
      const jobId = 'test-job-123';
      const filename = 'report.html';
      const mockBlob = new Blob(['<html>Test Report</html>'], { 
        type: 'text/html' 
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        blob: () => Promise.resolve(mockBlob)
      });

      const createObjectURLSpy = jest.spyOn(URL, 'createObjectURL')
        .mockReturnValue('blob:test-url');
      const appendChildSpy = jest.spyOn(document.body, 'appendChild')
        .mockImplementation();
      const removeChildSpy = jest.spyOn(document.body, 'removeChild')
        .mockImplementation();

      await mockApp.downloadFile(jobId, filename);

      expect(global.fetch).toHaveBeenCalledWith(
        `/api/jobs/${jobId}/files/${filename}`,
        expect.any(Object)
      );

      createObjectURLSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    test('should handle download failures gracefully', async () => {
      const jobId = 'test-job-123';
      const filename = 'report.html';

      global.mockFetchError(404, 'File Not Found');

      const showToastSpy = jest.spyOn(mockApp, 'showToast').mockImplementation();

      await mockApp.downloadFile(jobId, filename);

      expect(showToastSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to download'),
        'error'
      );

      showToastSpy.mockRestore();
    });
  });

  describe('Job Cancellation Workflow', () => {
    test('should cancel active job successfully', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId, status: 'running' });
      
      mockApp.state.activeJobs.set(jobId, mockJob);
      global.mockFetchSuccess({});

      const stopPollingSpy = jest.spyOn(mockApp, 'stopJobPolling').mockImplementation();
      const moveJobToHistorySpy = jest.spyOn(mockApp, 'moveJobToHistory').mockImplementation();

      await mockApp.cancelJob(jobId);

      expect(global.fetch).toHaveBeenCalledWith(
        `/api/jobs/${jobId}`,
        expect.objectContaining({ method: 'DELETE' })
      );
      expect(stopPollingSpy).toHaveBeenCalledWith(jobId);
      expect(moveJobToHistorySpy).toHaveBeenCalled();

      stopPollingSpy.mockRestore();
      moveJobToHistorySpy.mockRestore();
    });

    test('should handle cancellation failure', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId });
      
      mockApp.state.activeJobs.set(jobId, mockJob);
      global.mockFetchError(500, 'Server Error');

      const showToastSpy = jest.spyOn(mockApp, 'showToast').mockImplementation();

      await mockApp.cancelJob(jobId);

      expect(showToastSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to cancel'),
        'error'
      );

      showToastSpy.mockRestore();
    });
  });

  describe('Navigation and State Management', () => {
    test('should switch between views correctly', () => {
      const refreshActiveJobsSpy = jest.spyOn(mockApp, 'refreshActiveJobs').mockImplementation();
      const renderJobHistorySpy = jest.spyOn(mockApp, 'renderJobHistory').mockImplementation();

      // Switch to jobs view
      mockApp.switchView('jobs');

      expect(mockApp.currentView).toBe('jobs');
      expect(refreshActiveJobsSpy).toHaveBeenCalled();

      // Switch to history view
      mockApp.switchView('history');

      expect(mockApp.currentView).toBe('history');
      expect(renderJobHistorySpy).toHaveBeenCalled();

      refreshActiveJobsSpy.mockRestore();
      renderJobHistorySpy.mockRestore();
    });

    test('should maintain state consistency across views', async () => {
      // Initialize with reports
      const mockReportsData = global.generateMockReportsData();
      global.mockFetchSuccess(mockReportsData);
      await mockApp.init();

      // Select a report
      const mockReport = global.generateMockReport();
      mockApp.onReportSelected(mockReport);

      // Switch views
      mockApp.switchView('jobs');
      mockApp.switchView('reports');

      // Verify state preserved
      expect(mockApp.state.currentReport).toEqual(mockReport);
      expect(mockApp.state.reports).toEqual(mockReportsData);
    });
  });

  describe('Error Propagation and Recovery', () => {
    test('should handle cascading errors gracefully', async () => {
      // Setup scenario where multiple operations fail
      global.mockFetchNetworkError();

      const showToastSpy = jest.spyOn(mockApp, 'showToast').mockImplementation();

      // Try to initialize
      await mockApp.init();

      // Try to submit job without proper initialization
      const submitEvent = new Event('submit', { bubbles: true });
      submitEvent.preventDefault = jest.fn();
      await mockApp.handleJobSubmit(submitEvent);

      // Verify appropriate error messages shown
      expect(showToastSpy).toHaveBeenCalledWith(
        'Failed to initialize application',
        'error'
      );

      showToastSpy.mockRestore();
    });

    test('should recover from temporary network failures', async () => {
      // First attempt fails, second succeeds
      global.fetch
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce(global.mockFetchResponse(global.generateMockReportsData()));

      await mockApp.init();

      // Should retry and succeed
      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(mockApp.state.reports).toBeTruthy();
    });
  });

  describe('Performance and Timing', () => {
    test('should complete job submission within expected time', async () => {
      const mockJob = global.generateMockJob();
      global.mockFetchSuccess(mockJob);

      const mockReport = global.generateMockReport();
      mockApp.onReportSelected(mockReport);

      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'TestValue';

      const startTime = Date.now();
      
      const submitEvent = new Event('submit', { bubbles: true });
      submitEvent.preventDefault = jest.fn();
      
      await mockApp.handleJobSubmit(submitEvent);

      const endTime = Date.now();
      const duration = endTime - startTime;

      // Should complete within reasonable time (< 100ms for mocked operations)
      expect(duration).toBeLessThan(100);
    });

    test('should handle request timeouts appropriately', async () => {
      jest.useFakeTimers();

      // Mock a request that never resolves
      global.fetch.mockImplementation(() => new Promise(() => {}));

      const requestPromise = mockApp.makeRequest('/test-endpoint');

      // Fast-forward past timeout
      jest.advanceTimersByTime(10000);

      await expect(requestPromise).rejects.toThrow();

      jest.useRealTimers();
    });
  });

  describe('Data Consistency', () => {
    test('should maintain data consistency between components', async () => {
      // Initialize application
      const mockReportsData = global.generateMockReportsData();
      global.mockFetchSuccess(mockReportsData);
      await mockApp.init();

      // Submit a job
      const mockReport = global.generateMockReport();
      const mockJob = global.generateMockJob();
      
      mockApp.onReportSelected(mockReport);
      global.mockFetchSuccess(mockJob);

      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'TestValue';

      const submitEvent = new Event('submit', { bubbles: true });
      submitEvent.preventDefault = jest.fn();
      
      await mockApp.handleJobSubmit(submitEvent);

      // Verify job appears in active jobs
      expect(mockApp.state.activeJobs.has(mockJob.id)).toBe(true);
      
      // Complete the job
      const completedJob = { ...mockJob, status: 'completed' };
      mockApp.moveJobToHistory(completedJob);

      // Verify job moved from active to history
      expect(mockApp.state.activeJobs.has(mockJob.id)).toBe(false);
      expect(mockApp.state.jobHistory).toContainEqual(completedJob);
    });
  });
});
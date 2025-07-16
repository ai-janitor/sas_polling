/*
=============================================================================
DATAFIT APP COMPONENT TESTS
=============================================================================
Purpose: Test the main DataFit application logic and state management
Component: DataFitApp class from gui/app.js
Coverage: Constructor, initialization, state management, API calls, navigation

TEST SCENARIOS:
1. Application initialization and setup
2. Configuration and environment setup
3. Navigation between views
4. State management (reports, jobs, form data)
5. API communication and error handling
6. Job submission and polling
7. UI updates and notifications
8. Memory management and cleanup

MOCK STRATEGY:
- Mock all API endpoints
- Mock DOM elements and interactions
- Mock component dependencies
- Test error conditions and edge cases
=============================================================================
*/

// Mock the component dependencies before importing
jest.mock('../../../gui/components/report-selector.js', () => {
  return {
    ReportSelector: jest.fn().mockImplementation(() => ({
      render: jest.fn(),
      showError: jest.fn(),
      getSelectedReport: jest.fn(),
      resetSelection: jest.fn()
    }))
  };
});

jest.mock('../../../gui/components/form-generator.js', () => {
  return {
    FormGenerator: jest.fn().mockImplementation(() => ({
      generateForm: jest.fn(),
      getFormData: jest.fn(() => ({ test_field: 'test_value' })),
      validateForm: jest.fn(() => []),
      resetForm: jest.fn(),
      destroy: jest.fn()
    }))
  };
});

jest.mock('../../../gui/components/job-status.js', () => {
  return {
    JobStatus: jest.fn().mockImplementation(() => ({
      startPolling: jest.fn(),
      stopPolling: jest.fn(),
      destroy: jest.fn()
    }))
  };
});

describe('DataFitApp', () => {
  let app;
  let mockDOM;

  beforeEach(() => {
    // Setup DOM elements
    document.body.innerHTML = `
      <div id="app">
        <form id="job-form"></form>
        <button id="reset-form"></button>
        <button id="refresh-jobs"></button>
        <button id="clear-history"></button>
        <select id="history-filter"></select>
        <div id="job-modal">
          <div class="modal-backdrop"></div>
          <button class="modal-close"></button>
        </div>
        <div id="loading-overlay"></div>
        <div id="loading-message"></div>
        <div id="toast-container"></div>
        <div id="active-jobs-container"></div>
        <div id="job-history-container"></div>
        <button id="nav-reports" class="nav-button"></button>
        <button id="nav-jobs" class="nav-button"></button>
        <button id="nav-history" class="nav-button"></button>
        <section id="report-section" class="content-section"></section>
        <section id="jobs-section" class="content-section"></section>
        <section id="history-section" class="content-section"></section>
        <div id="modal-body"></div>
        <h3 id="selected-report-title"></h3>
        <p id="selected-report-description"></p>
        <div id="form-container"></div>
      </div>
    `;

    // Clear mocks
    jest.clearAllMocks();

    // Import and create app instance
    const { DataFitApp } = require('../../../gui/app.js');
    app = new DataFitApp();
  });

  afterEach(() => {
    if (app && app.destroy) {
      app.destroy();
    }
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  describe('Constructor and Initialization', () => {
    test('should initialize with default configuration', () => {
      expect(app.config).toBeDefined();
      expect(app.config.apiBaseUrl).toBe('/api');
      expect(app.config.pollingInterval).toBe(2000);
      expect(app.config.maxPollingInterval).toBe(30000);
      expect(app.config.requestTimeout).toBe(10000);
    });

    test('should initialize with empty state', () => {
      expect(app.state).toBeDefined();
      expect(app.state.currentReport).toBeNull();
      expect(app.state.formData).toEqual({});
      expect(app.state.activeJobs).toBeInstanceOf(Map);
      expect(app.state.jobHistory).toEqual([]);
      expect(app.state.reports).toBeNull();
      expect(app.state.isLoading).toBe(false);
    });

    test('should initialize component instances', () => {
      expect(app.reportSelector).toBeDefined();
      expect(app.formGenerator).toBeDefined();
      expect(app.jobStatus).toBeDefined();
    });

    test('should set default view to reports', () => {
      expect(app.currentView).toBe('reports');
    });
  });

  describe('Application Initialization', () => {
    test('should initialize successfully', async () => {
      const mockReportsData = global.generateMockReportsData();
      global.mockFetchSuccess(mockReportsData);

      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      await app.init();

      expect(consoleSpy).toHaveBeenCalledWith('Initializing DataFit application...');
      expect(consoleSpy).toHaveBeenCalledWith('DataFit application initialized successfully');
      expect(app.reportSelector.render).toHaveBeenCalledWith(mockReportsData);

      consoleSpy.mockRestore();
    });

    test('should handle initialization errors', async () => {
      global.mockFetchNetworkError();
      
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      const showToastSpy = jest.spyOn(app, 'showToast').mockImplementation();

      await app.init();

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to initialize application:', 
        expect.any(Error)
      );
      expect(showToastSpy).toHaveBeenCalledWith(
        'Failed to initialize application', 
        'error'
      );

      consoleErrorSpy.mockRestore();
      showToastSpy.mockRestore();
    });
  });

  describe('Navigation', () => {
    test('should switch views correctly', () => {
      const mockRefreshActiveJobs = jest.spyOn(app, 'refreshActiveJobs').mockImplementation();
      const mockRenderJobHistory = jest.spyOn(app, 'renderJobHistory').mockImplementation();

      app.switchView('jobs');

      expect(app.currentView).toBe('jobs');
      expect(mockRefreshActiveJobs).toHaveBeenCalled();

      app.switchView('history');

      expect(app.currentView).toBe('history');
      expect(mockRenderJobHistory).toHaveBeenCalled();

      mockRefreshActiveJobs.mockRestore();
      mockRenderJobHistory.mockRestore();
    });

    test('should update navigation UI when switching views', () => {
      const navButtons = document.querySelectorAll('.nav-button');
      const contentSections = document.querySelectorAll('.content-section');

      app.switchView('jobs');

      const activeButton = document.getElementById('nav-jobs');
      const activeSection = document.getElementById('jobs-section');

      expect(activeButton.classList.contains('active')).toBe(true);
      expect(activeButton.getAttribute('aria-pressed')).toBe('true');
      expect(activeSection.classList.contains('active')).toBe(true);
    });
  });

  describe('Report Loading', () => {
    test('should load reports successfully', async () => {
      const mockReportsData = global.generateMockReportsData();
      global.mockFetchSuccess(mockReportsData);

      const showLoadingSpy = jest.spyOn(app, 'showLoading').mockImplementation();
      const hideLoadingSpy = jest.spyOn(app, 'hideLoading').mockImplementation();

      await app.loadReports();

      expect(showLoadingSpy).toHaveBeenCalledWith('Loading reports...');
      expect(hideLoadingSpy).toHaveBeenCalled();
      expect(app.state.reports).toEqual(mockReportsData);
      expect(app.reportSelector.render).toHaveBeenCalledWith(mockReportsData);

      showLoadingSpy.mockRestore();
      hideLoadingSpy.mockRestore();
    });

    test('should handle report loading errors', async () => {
      global.mockFetchError(500, 'Server Error');

      const showToastSpy = jest.spyOn(app, 'showToast').mockImplementation();
      const showErrorSpy = jest.spyOn(app.reportSelector, 'showError');

      await app.loadReports();

      expect(showToastSpy).toHaveBeenCalledWith('Failed to load reports', 'error');
      expect(showErrorSpy).toHaveBeenCalledWith('Failed to load reports. Please try again.');

      showToastSpy.mockRestore();
    });
  });

  describe('Job Submission', () => {
    test('should submit job successfully', async () => {
      app.state.currentReport = global.generateMockReport();
      const mockJob = global.generateMockJob();
      global.mockFetchSuccess(mockJob);

      const showLoadingSpy = jest.spyOn(app, 'showLoading').mockImplementation();
      const hideLoadingSpy = jest.spyOn(app, 'hideLoading').mockImplementation();
      const showToastSpy = jest.spyOn(app, 'showToast').mockImplementation();
      const switchViewSpy = jest.spyOn(app, 'switchView').mockImplementation();
      const startPolllingSpy = jest.spyOn(app, 'startJobPolling').mockImplementation();

      const event = { preventDefault: jest.fn() };
      await app.handleJobSubmit(event);

      expect(event.preventDefault).toHaveBeenCalled();
      expect(showLoadingSpy).toHaveBeenCalledWith('Submitting job...');
      expect(hideLoadingSpy).toHaveBeenCalled();
      expect(showToastSpy).toHaveBeenCalledWith('Job submitted successfully', 'success');
      expect(switchViewSpy).toHaveBeenCalledWith('jobs');
      expect(app.state.activeJobs.has(mockJob.id)).toBe(true);
      expect(startPolllingSpy).toHaveBeenCalledWith(mockJob.id);

      showLoadingSpy.mockRestore();
      hideLoadingSpy.mockRestore();
      showToastSpy.mockRestore();
      switchViewSpy.mockRestore();
      startPolllingSpy.mockRestore();
    });

    test('should reject job submission without selected report', async () => {
      app.state.currentReport = null;
      const showToastSpy = jest.spyOn(app, 'showToast').mockImplementation();

      const event = { preventDefault: jest.fn() };
      await app.handleJobSubmit(event);

      expect(showToastSpy).toHaveBeenCalledWith('Please select a report first', 'warning');

      showToastSpy.mockRestore();
    });

    test('should handle validation errors', async () => {
      app.state.currentReport = global.generateMockReport();
      app.formGenerator.validateForm.mockReturnValue([
        { field: 'test_field', message: 'Required field' }
      ]);

      const showToastSpy = jest.spyOn(app, 'showToast').mockImplementation();

      const event = { preventDefault: jest.fn() };
      await app.handleJobSubmit(event);

      expect(showToastSpy).toHaveBeenCalledWith('Please fix form errors', 'error');

      showToastSpy.mockRestore();
    });

    test('should handle job submission errors', async () => {
      app.state.currentReport = global.generateMockReport();
      global.mockFetchError(500, 'Server Error');

      const showToastSpy = jest.spyOn(app, 'showToast').mockImplementation();

      const event = { preventDefault: jest.fn() };
      await app.handleJobSubmit(event);

      expect(showToastSpy).toHaveBeenCalledWith('Failed to submit job', 'error');

      showToastSpy.mockRestore();
    });
  });

  describe('Job Polling', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    test('should start job polling', () => {
      const jobId = 'test-job-123';
      
      app.startJobPolling(jobId);

      expect(app.pollingIntervals.has(jobId)).toBe(true);

      // Clear the timer
      app.stopJobPolling(jobId);
    });

    test('should stop job polling', () => {
      const jobId = 'test-job-123';
      
      app.startJobPolling(jobId);
      expect(app.pollingIntervals.has(jobId)).toBe(true);

      app.stopJobPolling(jobId);
      expect(app.pollingIntervals.has(jobId)).toBe(false);
    });

    test('should handle job completion during polling', async () => {
      const jobId = 'test-job-123';
      const completedJob = global.generateMockJob({ 
        id: jobId, 
        status: 'completed' 
      });

      global.mockFetchSuccess(completedJob);

      const moveJobToHistorySpy = jest.spyOn(app, 'moveJobToHistory').mockImplementation();
      const showToastSpy = jest.spyOn(app, 'showToast').mockImplementation();

      app.startJobPolling(jobId);

      // Fast-forward timers to trigger polling
      jest.advanceTimersByTime(2000);

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(moveJobToHistorySpy).toHaveBeenCalledWith(completedJob);
      expect(showToastSpy).toHaveBeenCalledWith('Job completed', 'success');

      moveJobToHistorySpy.mockRestore();
      showToastSpy.mockRestore();
    });
  });

  describe('API Communication', () => {
    test('should make successful API requests', async () => {
      const testData = { test: 'data' };
      global.mockFetchSuccess(testData);

      const result = await app.makeRequest('/test-endpoint');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test-endpoint',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
      expect(result).toEqual(testData);
    });

    test('should handle API request timeouts', async () => {
      // Mock a request that never resolves
      global.fetch.mockImplementation(() => new Promise(() => {}));

      const request = app.makeRequest('/test-endpoint');

      // Fast-forward past the timeout
      jest.advanceTimersByTime(10000);

      await expect(request).rejects.toThrow();
    });

    test('should handle API errors', async () => {
      global.mockFetchError(404, 'Not Found');

      await expect(app.makeRequest('/test-endpoint')).rejects.toThrow('HTTP 404: Not Found');
    });

    test('should handle network errors', async () => {
      global.mockFetchNetworkError();

      await expect(app.makeRequest('/test-endpoint')).rejects.toThrow('Network Error');
    });
  });

  describe('Job Management', () => {
    test('should refresh active jobs display', async () => {
      const mockJob = global.generateMockJob();
      app.state.activeJobs.set(mockJob.id, mockJob);

      app.refreshActiveJobs();

      const container = document.getElementById('active-jobs-container');
      expect(container.innerHTML).toContain('job-list');
      expect(container.innerHTML).toContain(mockJob.name);
    });

    test('should show empty state when no active jobs', async () => {
      app.state.activeJobs.clear();

      app.refreshActiveJobs();

      const container = document.getElementById('active-jobs-container');
      expect(container.innerHTML).toContain('empty-state');
      expect(container.innerHTML).toContain('No active jobs');
    });

    test('should cancel job successfully', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId });
      app.state.activeJobs.set(jobId, mockJob);

      global.mockFetchSuccess({});

      const stopPollingSpy = jest.spyOn(app, 'stopJobPolling').mockImplementation();
      const moveJobToHistorySpy = jest.spyOn(app, 'moveJobToHistory').mockImplementation();
      const showToastSpy = jest.spyOn(app, 'showToast').mockImplementation();
      const refreshJobsSpy = jest.spyOn(app, 'refreshActiveJobs').mockImplementation();

      await app.cancelJob(jobId);

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/jobs/test-job-123',
        expect.objectContaining({ method: 'DELETE' })
      );
      expect(stopPollingSpy).toHaveBeenCalledWith(jobId);
      expect(moveJobToHistorySpy).toHaveBeenCalled();
      expect(showToastSpy).toHaveBeenCalledWith('Job cancelled', 'warning');
      expect(refreshJobsSpy).toHaveBeenCalled();

      stopPollingSpy.mockRestore();
      moveJobToHistorySpy.mockRestore();
      showToastSpy.mockRestore();
      refreshJobsSpy.mockRestore();
    });
  });

  describe('UI Interactions', () => {
    test('should show and hide loading overlay', () => {
      const overlay = document.getElementById('loading-overlay');
      const message = document.getElementById('loading-message');

      app.showLoading('Test loading...');

      expect(overlay.style.display).toBe('flex');
      expect(message.textContent).toBe('Test loading...');
      expect(app.state.isLoading).toBe(true);

      app.hideLoading();

      expect(overlay.style.display).toBe('none');
      expect(app.state.isLoading).toBe(false);
    });

    test('should show toast notifications', () => {
      const container = document.getElementById('toast-container');

      app.showToast('Test message', 'success');

      expect(container.children.length).toBe(1);
      
      const toast = container.children[0];
      expect(toast.classList.contains('toast')).toBe(true);
      expect(toast.classList.contains('success')).toBe(true);
      expect(toast.innerHTML).toContain('Test message');
    });

    test('should auto-remove toast notifications', () => {
      jest.useFakeTimers();
      const container = document.getElementById('toast-container');

      app.showToast('Test message', 'info');

      expect(container.children.length).toBe(1);

      // Fast-forward past auto-remove timeout
      jest.advanceTimersByTime(5000);

      expect(container.children.length).toBe(0);
    });
  });

  describe('Memory Management', () => {
    test('should clean up resources on destroy', () => {
      const jobId1 = 'job-1';
      const jobId2 = 'job-2';
      
      app.startJobPolling(jobId1);
      app.startJobPolling(jobId2);

      expect(app.pollingIntervals.size).toBe(2);

      app.destroy();

      expect(app.pollingIntervals.size).toBe(0);
    });

    test('should clean up component instances on destroy', () => {
      app.destroy();

      expect(app.formGenerator.destroy).toHaveBeenCalled();
    });
  });

  describe('Report Selection', () => {
    test('should handle report selection', () => {
      const mockReport = global.generateMockReport();
      
      app.onReportSelected(mockReport);

      expect(app.state.currentReport).toEqual(mockReport);
      expect(app.formGenerator.generateForm).toHaveBeenCalledWith(mockReport);
      
      const titleElement = document.getElementById('selected-report-title');
      const descriptionElement = document.getElementById('selected-report-description');
      const formContainer = document.getElementById('form-container');

      expect(titleElement.textContent).toBe(mockReport.name);
      expect(descriptionElement.textContent).toBe(mockReport.description);
      expect(formContainer.style.display).toBe('block');
    });
  });
});
/*
=============================================================================
JOB STATUS COMPONENT TESTS
=============================================================================
Purpose: Test job status tracking, polling, and file management functionality
Component: JobStatus class from gui/components/job-status.js
Coverage: Status polling, progress tracking, file downloads, cancellation

TEST SCENARIOS:
1. Job status initialization and display
2. Real-time polling with exponential backoff
3. Progress tracking and visualization
4. Job completion and status updates
5. File download management
6. Job cancellation functionality
7. Error handling and retry mechanisms
8. Polling cleanup and memory management

MOCK STRATEGY:
- Mock API responses for job status
- Mock polling timers and intervals
- Mock file download triggers
- Test exponential backoff behavior
=============================================================================
*/

describe('JobStatus', () => {
  let jobStatus;
  let mockContainer;

  beforeEach(() => {
    jest.useFakeTimers();

    // Setup DOM container
    document.body.innerHTML = `
      <div id="job-status-container">
        <div class="job-status-component">
          <div class="active-jobs-section">
            <h3>Active Jobs</h3>
            <div class="jobs-list" id="active-jobs-list"></div>
          </div>
          <div class="job-history-section">
            <h3>Job History</h3>
            <div class="jobs-list" id="history-jobs-list"></div>
          </div>
          <div class="job-modal" id="job-details-modal">
            <div class="modal-content">
              <div class="modal-header">
                <h4 class="modal-title"></h4>
                <button class="modal-close">&times;</button>
              </div>
              <div class="modal-body"></div>
            </div>
          </div>
        </div>
      </div>
    `;

    mockContainer = document.getElementById('job-status-container');

    // Import and create component instance
    const { JobStatus } = require('../../../gui/components/job-status.js');
    jobStatus = new JobStatus(mockContainer);
  });

  afterEach(() => {
    if (jobStatus && jobStatus.destroy) {
      jobStatus.destroy();
    }
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  describe('Initialization', () => {
    test('should initialize with container element', () => {
      expect(jobStatus.container).toBe(mockContainer);
      expect(jobStatus.activeJobs).toBeInstanceOf(Map);
      expect(jobStatus.pollingIntervals).toBeInstanceOf(Map);
      expect(jobStatus.jobHistory).toEqual([]);
    });

    test('should setup DOM element references', () => {
      const activeJobsList = document.getElementById('active-jobs-list');
      const historyJobsList = document.getElementById('history-jobs-list');

      expect(activeJobsList).toBeTruthy();
      expect(historyJobsList).toBeTruthy();
    });

    test('should initialize polling configuration', () => {
      expect(jobStatus.config.pollingInterval).toBe(2000);
      expect(jobStatus.config.maxPollingInterval).toBe(30000);
      expect(jobStatus.config.maxRetries).toBe(3);
    });
  });

  describe('Job Tracking', () => {
    test('should add active job to tracking', () => {
      const mockJob = global.generateMockJob();
      
      jobStatus.addActiveJob(mockJob);

      expect(jobStatus.activeJobs.has(mockJob.id)).toBe(true);
      expect(jobStatus.activeJobs.get(mockJob.id)).toEqual(mockJob);
    });

    test('should remove job from active tracking', () => {
      const mockJob = global.generateMockJob();
      
      jobStatus.addActiveJob(mockJob);
      jobStatus.removeActiveJob(mockJob.id);

      expect(jobStatus.activeJobs.has(mockJob.id)).toBe(false);
    });

    test('should move completed job to history', () => {
      const mockJob = global.generateMockJob({ status: 'completed' });
      
      jobStatus.addActiveJob(mockJob);
      jobStatus.moveJobToHistory(mockJob);

      expect(jobStatus.activeJobs.has(mockJob.id)).toBe(false);
      expect(jobStatus.jobHistory.length).toBe(1);
      expect(jobStatus.jobHistory[0]).toEqual(mockJob);
    });

    test('should limit job history size', () => {
      // Add more than maximum history items
      for (let i = 0; i < 105; i++) {
        const mockJob = global.generateMockJob({ 
          id: `job_${i}`, 
          status: 'completed' 
        });
        jobStatus.moveJobToHistory(mockJob);
      }

      expect(jobStatus.jobHistory.length).toBe(100); // Maximum history size
    });
  });

  describe('Status Polling', () => {
    test('should start polling for job status', () => {
      const jobId = 'test-job-123';
      
      jobStatus.startPolling(jobId);

      expect(jobStatus.pollingIntervals.has(jobId)).toBe(true);
    });

    test('should stop polling for job', () => {
      const jobId = 'test-job-123';
      
      jobStatus.startPolling(jobId);
      jobStatus.stopPolling(jobId);

      expect(jobStatus.pollingIntervals.has(jobId)).toBe(false);
    });

    test('should implement exponential backoff', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId, status: 'running' });
      
      jobStatus.addActiveJob(mockJob);
      global.mockFetchSuccess(mockJob);

      jobStatus.startPolling(jobId);

      // First poll at 2 seconds
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      // Second poll should be at 4 seconds (2 * 2)
      jest.advanceTimersByTime(4000);
      await Promise.resolve();

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    test('should handle polling errors with retry', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId });
      
      jobStatus.addActiveJob(mockJob);
      global.mockFetchNetworkError();

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      jobStatus.startPolling(jobId);
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to poll job status')
      );

      consoleErrorSpy.mockRestore();
    });

    test('should stop polling when job completes', async () => {
      const jobId = 'test-job-123';
      const completedJob = global.generateMockJob({ 
        id: jobId, 
        status: 'completed' 
      });
      
      jobStatus.addActiveJob(completedJob);
      global.mockFetchSuccess(completedJob);

      const stopPollingSpy = jest.spyOn(jobStatus, 'stopPolling');
      
      jobStatus.startPolling(jobId);
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      expect(stopPollingSpy).toHaveBeenCalledWith(jobId);
      stopPollingSpy.mockRestore();
    });

    test('should stop polling when job fails', async () => {
      const jobId = 'test-job-123';
      const failedJob = global.generateMockJob({ 
        id: jobId, 
        status: 'failed' 
      });
      
      jobStatus.addActiveJob(failedJob);
      global.mockFetchSuccess(failedJob);

      const stopPollingSpy = jest.spyOn(jobStatus, 'stopPolling');
      
      jobStatus.startPolling(jobId);
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      expect(stopPollingSpy).toHaveBeenCalledWith(jobId);
      stopPollingSpy.mockRestore();
    });
  });

  describe('Job Display', () => {
    test('should render active jobs list', () => {
      const mockJob1 = global.generateMockJob({ id: 'job1', status: 'running' });
      const mockJob2 = global.generateMockJob({ id: 'job2', status: 'pending' });
      
      jobStatus.addActiveJob(mockJob1);
      jobStatus.addActiveJob(mockJob2);
      jobStatus.renderActiveJobs();

      const activeJobsList = document.getElementById('active-jobs-list');
      expect(activeJobsList.children.length).toBe(2);
      expect(activeJobsList.innerHTML).toContain('job1');
      expect(activeJobsList.innerHTML).toContain('job2');
    });

    test('should show empty state for no active jobs', () => {
      jobStatus.renderActiveJobs();

      const activeJobsList = document.getElementById('active-jobs-list');
      expect(activeJobsList.innerHTML).toContain('empty-state');
      expect(activeJobsList.innerHTML).toContain('No active jobs');
    });

    test('should render job history list', () => {
      const mockJob = global.generateMockJob({ status: 'completed' });
      
      jobStatus.moveJobToHistory(mockJob);
      jobStatus.renderJobHistory();

      const historyJobsList = document.getElementById('history-jobs-list');
      expect(historyJobsList.children.length).toBe(1);
      expect(historyJobsList.innerHTML).toContain(mockJob.id);
    });

    test('should display job progress indicators', () => {
      const mockJob = global.generateMockJob({ 
        status: 'running', 
        progress: 45 
      });
      
      jobStatus.addActiveJob(mockJob);
      jobStatus.renderActiveJobs();

      const progressBar = document.querySelector('.progress-bar');
      expect(progressBar).toBeTruthy();
      expect(progressBar.style.width).toBe('45%');
    });

    test('should show job status badges', () => {
      const mockJob = global.generateMockJob({ status: 'running' });
      
      jobStatus.addActiveJob(mockJob);
      jobStatus.renderActiveJobs();

      const statusBadge = document.querySelector('.status-badge');
      expect(statusBadge).toBeTruthy();
      expect(statusBadge.classList.contains('status-running')).toBe(true);
    });
  });

  describe('Job Cancellation', () => {
    test('should cancel active job', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId, status: 'running' });
      
      jobStatus.addActiveJob(mockJob);
      global.mockFetchSuccess({});

      const stopPollingSpy = jest.spyOn(jobStatus, 'stopPolling');
      
      await jobStatus.cancelJob(jobId);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/jobs/${jobId}`),
        expect.objectContaining({ method: 'DELETE' })
      );
      expect(stopPollingSpy).toHaveBeenCalledWith(jobId);

      stopPollingSpy.mockRestore();
    });

    test('should handle cancellation errors', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId });
      
      jobStatus.addActiveJob(mockJob);
      global.mockFetchError(500, 'Server Error');

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      await jobStatus.cancelJob(jobId);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to cancel job')
      );

      consoleErrorSpy.mockRestore();
    });

    test('should show cancel confirmation dialog', () => {
      const jobId = 'test-job-123';
      
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
      
      jobStatus.showCancelConfirmation(jobId);

      expect(confirmSpy).toHaveBeenCalledWith(
        expect.stringContaining('cancel this job')
      );

      confirmSpy.mockRestore();
    });
  });

  describe('File Management', () => {
    test('should load job files list', async () => {
      const jobId = 'test-job-123';
      const mockFiles = [
        { filename: 'report.html', size: 12345, type: 'HTML' },
        { filename: 'data.csv', size: 6789, type: 'CSV' }
      ];
      
      global.mockFetchSuccess(mockFiles);

      const files = await jobStatus.loadJobFiles(jobId);

      expect(files).toEqual(mockFiles);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/jobs/${jobId}/files`)
      );
    });

    test('should handle file download', async () => {
      const jobId = 'test-job-123';
      const filename = 'report.html';
      
      // Mock successful download
      global.mockFetchSuccess(new Blob(['<html>Test</html>'], { type: 'text/html' }));

      const createObjectURLSpy = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:url');
      const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation();
      const removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation();

      await jobStatus.downloadFile(jobId, filename);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/jobs/${jobId}/files/${filename}`)
      );

      createObjectURLSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    test('should handle download errors', async () => {
      const jobId = 'test-job-123';
      const filename = 'report.html';
      
      global.mockFetchError(404, 'File Not Found');

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      await jobStatus.downloadFile(jobId, filename);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to download file')
      );

      consoleErrorSpy.mockRestore();
    });

    test('should display download progress', async () => {
      const jobId = 'test-job-123';
      const filename = 'large-report.pdf';
      
      // Mock download with progress events
      const mockResponse = {
        ok: true,
        body: {
          getReader: () => ({
            read: jest.fn().mockResolvedValue({ done: true, value: new Uint8Array() })
          })
        },
        headers: new Headers({ 'content-length': '1000000' })
      };

      global.fetch.mockResolvedValueOnce(mockResponse);

      await jobStatus.downloadFile(jobId, filename);

      const progressElement = document.querySelector('.download-progress');
      expect(progressElement).toBeTruthy();
    });
  });

  describe('Job Details Modal', () => {
    test('should show job details modal', () => {
      const mockJob = global.generateMockJob({
        status: 'completed',
        submitted_at: '2023-12-01T10:00:00Z',
        completed_at: '2023-12-01T10:05:00Z'
      });
      
      jobStatus.showJobDetails(mockJob);

      const modal = document.getElementById('job-details-modal');
      const modalTitle = document.querySelector('.modal-title');
      const modalBody = document.querySelector('.modal-body');

      expect(modal.style.display).toBe('block');
      expect(modalTitle.textContent).toContain(mockJob.name);
      expect(modalBody.innerHTML).toContain(mockJob.status);
    });

    test('should close modal on close button click', () => {
      const mockJob = global.generateMockJob();
      
      jobStatus.showJobDetails(mockJob);
      
      const closeButton = document.querySelector('.modal-close');
      global.simulateEvent(closeButton, 'click');

      const modal = document.getElementById('job-details-modal');
      expect(modal.style.display).toBe('none');
    });

    test('should close modal on backdrop click', () => {
      const mockJob = global.generateMockJob();
      
      jobStatus.showJobDetails(mockJob);
      
      const modal = document.getElementById('job-details-modal');
      global.simulateEvent(modal, 'click');

      expect(modal.style.display).toBe('none');
    });
  });

  describe('Filtering and Search', () => {
    beforeEach(() => {
      // Add sample jobs to history
      const job1 = global.generateMockJob({ 
        id: 'job1', 
        name: 'Daily Report', 
        status: 'completed' 
      });
      const job2 = global.generateMockJob({ 
        id: 'job2', 
        name: 'Weekly Summary', 
        status: 'failed' 
      });
      
      jobStatus.moveJobToHistory(job1);
      jobStatus.moveJobToHistory(job2);
    });

    test('should filter jobs by status', () => {
      jobStatus.filterJobs('completed');

      const historyJobsList = document.getElementById('history-jobs-list');
      expect(historyJobsList.innerHTML).toContain('Daily Report');
      expect(historyJobsList.innerHTML).not.toContain('Weekly Summary');
    });

    test('should search jobs by name', () => {
      jobStatus.searchJobs('Daily');

      const historyJobsList = document.getElementById('history-jobs-list');
      expect(historyJobsList.innerHTML).toContain('Daily Report');
      expect(historyJobsList.innerHTML).not.toContain('Weekly Summary');
    });

    test('should clear filters', () => {
      jobStatus.filterJobs('completed');
      jobStatus.clearFilters();

      const historyJobsList = document.getElementById('history-jobs-list');
      expect(historyJobsList.innerHTML).toContain('Daily Report');
      expect(historyJobsList.innerHTML).toContain('Weekly Summary');
    });
  });

  describe('Notifications', () => {
    test('should show notification on job completion', () => {
      const mockJob = global.generateMockJob({ status: 'completed' });
      const showNotificationSpy = jest.spyOn(jobStatus, 'showNotification');
      
      jobStatus.onJobStatusChange(mockJob);

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Job completed successfully',
        'success'
      );

      showNotificationSpy.mockRestore();
    });

    test('should show notification on job failure', () => {
      const mockJob = global.generateMockJob({ status: 'failed' });
      const showNotificationSpy = jest.spyOn(jobStatus, 'showNotification');
      
      jobStatus.onJobStatusChange(mockJob);

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Job failed',
        'error'
      );

      showNotificationSpy.mockRestore();
    });
  });

  describe('Memory Management', () => {
    test('should clean up all polling intervals on destroy', () => {
      const job1 = 'job1';
      const job2 = 'job2';
      
      jobStatus.startPolling(job1);
      jobStatus.startPolling(job2);

      expect(jobStatus.pollingIntervals.size).toBe(2);

      jobStatus.destroy();

      expect(jobStatus.pollingIntervals.size).toBe(0);
    });

    test('should clear all job data on destroy', () => {
      const mockJob = global.generateMockJob();
      
      jobStatus.addActiveJob(mockJob);
      jobStatus.moveJobToHistory(mockJob);

      jobStatus.destroy();

      expect(jobStatus.activeJobs.size).toBe(0);
      expect(jobStatus.jobHistory.length).toBe(0);
    });

    test('should remove event listeners on destroy', () => {
      const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener');
      
      jobStatus.destroy();

      expect(removeEventListenerSpy).toHaveBeenCalled();
      removeEventListenerSpy.mockRestore();
    });
  });

  describe('Error Recovery', () => {
    test('should retry failed polling with exponential backoff', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId });
      
      jobStatus.addActiveJob(mockJob);
      
      // First call fails
      global.mockFetchNetworkError();
      
      jobStatus.startPolling(jobId);
      jest.advanceTimersByTime(2000);
      await Promise.resolve();

      // Second call succeeds
      global.mockFetchSuccess(mockJob);
      jest.advanceTimersByTime(4000); // Exponential backoff
      await Promise.resolve();

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    test('should stop polling after maximum retries', async () => {
      const jobId = 'test-job-123';
      const mockJob = global.generateMockJob({ id: jobId });
      
      jobStatus.addActiveJob(mockJob);
      global.mockFetchNetworkError();

      const stopPollingSpy = jest.spyOn(jobStatus, 'stopPolling');
      
      jobStatus.startPolling(jobId);

      // Advance through multiple failed attempts
      for (let i = 0; i < 5; i++) {
        jest.advanceTimersByTime(2000 * Math.pow(2, i));
        await Promise.resolve();
      }

      expect(stopPollingSpy).toHaveBeenCalledWith(jobId);
      stopPollingSpy.mockRestore();
    });
  });
});
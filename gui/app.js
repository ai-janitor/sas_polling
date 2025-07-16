/*
=============================================================================
DATAFIT SPA - MAIN APPLICATION LOGIC
=============================================================================
Purpose: Core JavaScript application for job submission and management
Technology: Vanilla ES6+ JavaScript with async/await
Dependencies: None (standalone vanilla JS)

STRICT REQUIREMENTS:
- ES6+ syntax with proper error handling
- Async/await for all API calls with timeout handling
- State management without external libraries
- Real-time job status updates with WebSocket fallback to polling
- Form validation with user-friendly error messages

CORE MODULES:
1. ReportManager - Handle report definition loading and caching
2. FormGenerator - Dynamic form creation from JSON schema
3. JobSubmitter - Job submission and validation
4. StatusTracker - Real-time job status monitoring
5. FileManager - Download management and history
6. ErrorHandler - Centralized error handling and user notification

API ENDPOINTS:
- reportDefinitionsUrl: GET /api/reports
- jobSubmissionUrl: POST /api/jobs  
- jobStatusUrl: GET /api/jobs/{id}/status
- fileDownloadUrl: GET /api/jobs/{id}/files/{filename}

CONFIGURATION:
All URLs and settings loaded from config via environment or API

STATE MANAGEMENT:
- currentReport: Selected report definition
- formData: User input parameters
- activeJobs: List of submitted jobs with status
- jobHistory: Completed jobs with download links
=============================================================================
*/

class DataFitApp {
    constructor() {
        this.config = {
            apiBaseUrl: '/api',
            pollingInterval: 2000,
            maxPollingInterval: 30000,
            requestTimeout: 10000
        };
        
        this.state = {
            currentReport: null,
            formData: {},
            activeJobs: new Map(),
            jobHistory: [],
            reports: null,
            isLoading: false
        };
        
        this.currentView = 'reports';
        this.pollingIntervals = new Map();
        
        this.reportSelector = new ReportSelector(this);
        this.formGenerator = new FormGenerator(this);
        this.jobStatus = new JobStatus(this);
    }

    async init() {
        try {
            console.log('Initializing DataFit application...');
            
            this.setupEventListeners();
            this.setupNavigation();
            
            await this.loadReports();
            
            this.loadJobHistory();
            
            console.log('DataFit application initialized successfully');
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.showToast('Failed to initialize application', 'error');
        }
    }

    setupEventListeners() {
        document.getElementById('job-form').addEventListener('submit', this.handleJobSubmit.bind(this));
        document.getElementById('reset-form').addEventListener('click', this.handleFormReset.bind(this));
        document.getElementById('refresh-jobs').addEventListener('click', this.refreshActiveJobs.bind(this));
        document.getElementById('clear-history').addEventListener('click', this.clearJobHistory.bind(this));
        document.getElementById('history-filter').addEventListener('change', this.filterJobHistory.bind(this));
        
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', this.closeModal.bind(this));
        });
        
        document.getElementById('job-modal').addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                this.closeModal();
            }
        });
    }

    setupNavigation() {
        document.querySelectorAll('.nav-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.currentTarget.id.replace('nav-', '');
                this.switchView(view);
            });
        });
    }

    switchView(view) {
        document.querySelectorAll('.nav-button').forEach(btn => {
            btn.classList.remove('active');
            btn.setAttribute('aria-pressed', 'false');
        });
        
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        const navElement = document.getElementById(`nav-${view}`);
        const sectionElement = document.getElementById(`${view}-section`);
        
        if (navElement) {
            navElement.classList.add('active');
            navElement.setAttribute('aria-pressed', 'true');
        }
        
        if (sectionElement) {
            sectionElement.classList.add('active');
        }
        
        this.currentView = view;
        
        if (view === 'jobs') {
            this.refreshActiveJobs();
        } else if (view === 'history') {
            this.renderJobHistory();
        }
    }

    async loadReports() {
        try {
            this.showLoading('Loading reports...');
            
            const response = await this.makeRequest('/reports');
            this.state.reports = response;
            
            this.reportSelector.render(response);
            
        } catch (error) {
            console.error('Failed to load reports:', error);
            this.showToast('Failed to load reports', 'error');
            this.reportSelector.showError('Failed to load reports. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async handleJobSubmit(e) {
        e.preventDefault();
        
        if (!this.state.currentReport) {
            this.showToast('Please select a report first', 'warning');
            return;
        }

        try {
            const formData = this.formGenerator.getFormData();
            const validationErrors = this.formGenerator.validateForm();
            
            if (validationErrors.length > 0) {
                this.showToast('Please fix form errors', 'error');
                return;
            }

            this.showLoading('Submitting job...');

            // Extract job name and remove it from arguments
            const jobName = formData.job_name || `${this.state.currentReport.name} - ${new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}`;
            const reportArguments = { ...formData };
            delete reportArguments.job_name;

            const jobRequest = {
                name: jobName,
                jobDefinitionUri: this.state.currentReport.id,
                arguments: reportArguments,
                submitted_by: 'user',
                priority: 5
            };

            console.log('DEBUG: Form data collected:', formData);
            console.log('DEBUG: Report arguments:', reportArguments);
            console.log('DEBUG: Current report:', this.state.currentReport);
            console.log('DEBUG: Job request payload:', jobRequest);
            console.log('DEBUG: JSON stringified payload:', JSON.stringify(jobRequest, null, 2));

            const job = await this.makeRequest('/jobs', {
                method: 'POST',
                body: JSON.stringify(jobRequest)
            });

            this.state.activeJobs.set(job.id, job);
            this.startJobPolling(job.id);
            
            this.showToast('Job submitted successfully', 'success');
            this.switchView('jobs');
            
        } catch (error) {
            console.error('Failed to submit job:', error);
            this.showToast('Failed to submit job', 'error');
        } finally {
            this.hideLoading();
        }
    }

    handleFormReset() {
        this.formGenerator.resetForm();
        this.state.formData = {};
    }

    async refreshActiveJobs() {
        try {
            const activeJobsContainer = document.getElementById('active-jobs-container');
            
            if (this.state.activeJobs.size === 0) {
                activeJobsContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>No active jobs</p>
                    </div>
                `;
                return;
            }

            const jobsHtml = Array.from(this.state.activeJobs.values())
                .map(job => this.renderJobItem(job))
                .join('');

            activeJobsContainer.innerHTML = `
                <div class="job-list">
                    ${jobsHtml}
                </div>
            `;
            
        } catch (error) {
            console.error('Failed to refresh active jobs:', error);
        }
    }

    startJobPolling(jobId) {
        if (this.pollingIntervals.has(jobId)) {
            return;
        }

        let pollingInterval = this.config.pollingInterval;
        
        const poll = async () => {
            try {
                const job = await this.makeRequest(`/jobs/${jobId}/status`);
                this.state.activeJobs.set(jobId, job);
                
                if (job.status === 'completed' || job.status === 'failed') {
                    this.stopJobPolling(jobId);
                    this.moveJobToHistory(job);
                    this.showToast(`Job ${job.status}`, job.status === 'completed' ? 'success' : 'error');
                }
                
                if (this.currentView === 'jobs') {
                    this.refreshActiveJobs();
                }
                
                pollingInterval = Math.min(pollingInterval * 1.1, this.config.maxPollingInterval);
                
            } catch (error) {
                console.error(`Failed to poll job ${jobId}:`, error);
                pollingInterval = Math.min(pollingInterval * 1.5, this.config.maxPollingInterval);
            }
            
            if (this.pollingIntervals.has(jobId)) {
                this.pollingIntervals.set(jobId, setTimeout(poll, pollingInterval));
            }
        };

        this.pollingIntervals.set(jobId, setTimeout(poll, pollingInterval));
    }

    stopJobPolling(jobId) {
        const intervalId = this.pollingIntervals.get(jobId);
        if (intervalId) {
            clearTimeout(intervalId);
            this.pollingIntervals.delete(jobId);
        }
    }

    moveJobToHistory(job) {
        this.state.activeJobs.delete(job.id);
        this.state.jobHistory.unshift(job);
        this.saveJobHistory();
    }

    renderJobItem(job) {
        const statusClass = job.status || 'pending';
        const progress = job.progress || 0;
        const timeAgo = job.submitted_at ? this.formatTimeAgo(new Date(job.submitted_at)) : 'Just now';
        
        return `
            <div class="job-item" data-job-id="${job.id}">
                <div class="job-header">
                    <div class="job-title">${job.name}</div>
                    <div class="job-status ${statusClass}">
                        <i class="fas fa-${this.getStatusIcon(job.status)}"></i>
                        ${job.status || 'pending'}
                    </div>
                </div>
                <div class="job-meta">
                    <span>Submitted: ${timeAgo}</span>
                    <span>ID: ${job.id}</span>
                </div>
                ${progress > 0 ? `
                    <div class="job-progress">
                        <div class="job-progress-bar" style="width: ${progress}%"></div>
                    </div>
                ` : ''}
                <div class="job-actions">
                    <button class="btn btn-secondary" onclick="app.showJobDetails('${job.id}')">
                        <i class="fas fa-info-circle"></i>
                        Details
                    </button>
                    ${job.status === 'completed' ? `
                        <button class="btn btn-success" onclick="app.downloadJobFiles('${job.id}')">
                            <i class="fas fa-download"></i>
                            Download
                        </button>
                    ` : ''}
                    ${job.status === 'running' || job.status === 'pending' ? `
                        <button class="btn btn-danger" onclick="app.cancelJob('${job.id}')">
                            <i class="fas fa-times"></i>
                            Cancel
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    getStatusIcon(status) {
        const icons = {
            pending: 'clock',
            running: 'spinner fa-spin',
            completed: 'check-circle',
            failed: 'exclamation-circle',
            cancelled: 'times-circle'
        };
        return icons[status] || 'clock';
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) return `${days}d ago`;
        if (hours > 0) return `${hours}h ago`;
        if (minutes > 0) return `${minutes}m ago`;
        return 'Just now';
    }

    async showJobDetails(jobId) {
        try {
            const job = this.state.activeJobs.get(jobId) || 
                       this.state.jobHistory.find(j => j.id === jobId);
            
            if (!job) {
                this.showToast('Job not found', 'error');
                return;
            }

            const modalBody = document.getElementById('modal-body');
            modalBody.innerHTML = `
                <div class="job-details">
                    <h4>Job Information</h4>
                    <table style="width: 100%; margin-bottom: 1rem;">
                        <tr><td><strong>Name:</strong></td><td>${job.name}</td></tr>
                        <tr><td><strong>ID:</strong></td><td>${job.id}</td></tr>
                        <tr><td><strong>Status:</strong></td><td>${job.status}</td></tr>
                        <tr><td><strong>Report:</strong></td><td>${job.jobDefinitionUri}</td></tr>
                        <tr><td><strong>Submitted:</strong></td><td>${job.submitted_at || 'N/A'}</td></tr>
                        <tr><td><strong>Progress:</strong></td><td>${job.progress || 0}%</td></tr>
                    </table>
                    
                    ${job.arguments ? `
                        <h4>Parameters</h4>
                        <pre style="background: #f5f5f5; padding: 1rem; border-radius: 4px; overflow-x: auto;">${JSON.stringify(job.arguments, null, 2)}</pre>
                    ` : ''}
                    
                    ${job.error ? `
                        <h4>Error Details</h4>
                        <div style="background: #fee2e2; color: #991b1b; padding: 1rem; border-radius: 4px;">
                            ${job.error}
                        </div>
                    ` : ''}
                </div>
            `;

            this.showModal();
            
        } catch (error) {
            console.error('Failed to show job details:', error);
            this.showToast('Failed to load job details', 'error');
        }
    }

    async cancelJob(jobId) {
        try {
            await this.makeRequest(`/jobs/${jobId}`, { method: 'DELETE' });
            this.stopJobPolling(jobId);
            
            const job = this.state.activeJobs.get(jobId);
            if (job) {
                job.status = 'cancelled';
                this.moveJobToHistory(job);
            }
            
            this.showToast('Job cancelled', 'warning');
            this.refreshActiveJobs();
            
        } catch (error) {
            console.error('Failed to cancel job:', error);
            this.showToast('Failed to cancel job', 'error');
        }
    }

    async downloadJobFiles(jobId) {
        try {
            const files = await this.makeRequest(`/jobs/${jobId}/files`);
            
            if (files.length === 0) {
                this.showToast('No files available for download', 'warning');
                return;
            }

            files.forEach(file => {
                const link = document.createElement('a');
                link.href = `${this.config.apiBaseUrl}/jobs/${jobId}/files/${file.filename}`;
                link.download = file.filename;
                link.click();
            });
            
            this.showToast('Downloads started', 'success');
            
        } catch (error) {
            console.error('Failed to download files:', error);
            this.showToast('Failed to download files', 'error');
        }
    }

    clearJobHistory() {
        this.state.jobHistory = [];
        this.saveJobHistory();
        this.renderJobHistory();
        this.showToast('Job history cleared', 'success');
    }

    filterJobHistory() {
        this.renderJobHistory();
    }

    renderJobHistory() {
        const filter = document.getElementById('history-filter').value;
        const container = document.getElementById('job-history-container');
        
        let filteredHistory = this.state.jobHistory;
        if (filter !== 'all') {
            filteredHistory = this.state.jobHistory.filter(job => job.status === filter);
        }
        
        if (filteredHistory.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <p>No job history</p>
                </div>
            `;
            return;
        }

        const jobsHtml = filteredHistory
            .map(job => this.renderJobItem(job))
            .join('');

        container.innerHTML = `
            <div class="job-list">
                ${jobsHtml}
            </div>
        `;
    }

    saveJobHistory() {
        try {
            localStorage.setItem('datafit_job_history', JSON.stringify(this.state.jobHistory));
        } catch (error) {
            console.error('Failed to save job history:', error);
        }
    }

    loadJobHistory() {
        try {
            const saved = localStorage.getItem('datafit_job_history');
            if (saved) {
                this.state.jobHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load job history:', error);
            this.state.jobHistory = [];
        }
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.config.apiBaseUrl}${endpoint}`;
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            timeout: this.config.requestTimeout
        };

        const config = { ...defaultOptions, ...options };
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), config.timeout);
        
        try {
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
            
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }

    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');
        messageEl.textContent = message;
        overlay.style.display = 'flex';
        this.state.isLoading = true;
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = 'none';
        this.state.isLoading = false;
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toastId = 'toast-' + Date.now();
        
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };

        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <i class="fas fa-${icons[type]} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="app.closeToast('${toastId}')">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            this.closeToast(toastId);
        }, 5000);
    }

    closeToast(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.remove();
        }
    }

    showModal() {
        const modal = document.getElementById('job-modal');
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
        
        const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            firstFocusable.focus();
        }
    }

    closeModal() {
        const modal = document.getElementById('job-modal');
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    }

    onReportSelected(report) {
        this.state.currentReport = report;
        this.formGenerator.generateForm(report);
        
        document.getElementById('selected-report-title').textContent = report.name;
        document.getElementById('selected-report-description').textContent = report.description;
        document.getElementById('form-container').style.display = 'block';
    }

    destroy() {
        this.pollingIntervals.forEach((intervalId) => {
            clearTimeout(intervalId);
        });
        this.pollingIntervals.clear();
    }
}

let app;

document.addEventListener('DOMContentLoaded', async () => {
    app = new DataFitApp();
    await app.init();
});

window.addEventListener('beforeunload', () => {
    if (app) {
        app.destroy();
    }
});
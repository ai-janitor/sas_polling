/*
=============================================================================
JOB STATUS TRACKING COMPONENT
=============================================================================
Purpose: Real-time job status monitoring and file download management
Technology: Vanilla JavaScript with periodic polling
Parent: app.js

STRICT REQUIREMENTS:
- Real-time status updates with exponential backoff polling
- Progress indicators for long-running jobs
- Error handling with retry mechanisms
- File download management with progress tracking
- Job history with pagination

STATUS TRACKING:
- Poll job status every 2 seconds initially
- Exponential backoff: 2s, 4s, 8s, 16s, max 30s
- Visual indicators for: pending, running, completed, failed
- Estimated completion time display
- Cancel job functionality

FILE MANAGEMENT:
- List generated files with metadata
- Download progress tracking
- File preview for HTML/CSV reports
- Bulk download capabilities
- File cleanup after retention period

JOB HISTORY:
- FIFO list of last 100 jobs
- Filter by status, date, report type
- Search by job name or parameters
- Export history as CSV
- Detailed job information modal

METHODS:
- startPolling(jobId): Begin status polling for job
- stopPolling(jobId): Stop polling for completed/failed jobs
- downloadFile(jobId, filename): Initiate file download
- cancelJob(jobId): Cancel running job
- showJobDetails(jobId): Display detailed job information
=============================================================================
*/

class JobStatus {
    constructor(app) {
        this.app = app;
        this.pollingIntervals = new Map();
        this.lastStatusUpdate = new Map();
        
        this.setupNotifications();
    }

    async setupNotifications() {
        if ('Notification' in window && Notification.permission === 'default') {
            try {
                await Notification.requestPermission();
            } catch (error) {
                console.log('Notification permission not granted:', error);
            }
        }
    }

    startPolling(jobId, initialInterval = 2000) {
        if (this.pollingIntervals.has(jobId)) {
            this.stopPolling(jobId);
        }

        let currentInterval = initialInterval;
        const maxInterval = 30000;
        const backoffMultiplier = 1.2;
        let errorCount = 0;
        const maxErrors = 5;

        const poll = async () => {
            try {
                const job = await this.app.makeRequest(`/jobs/${jobId}/status`);
                
                const previousStatus = this.lastStatusUpdate.get(jobId);
                this.lastStatusUpdate.set(jobId, job.status);
                
                this.app.state.activeJobs.set(jobId, job);
                
                if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
                    this.stopPolling(jobId);
                    this.app.moveJobToHistory(job);
                    this.notifyJobComplete(job);
                    
                    if (this.app.currentView === 'jobs') {
                        this.app.refreshActiveJobs();
                    }
                    return;
                }
                
                if (previousStatus && previousStatus !== job.status) {
                    currentInterval = initialInterval;
                } else {
                    currentInterval = Math.min(currentInterval * backoffMultiplier, maxInterval);
                }
                
                errorCount = 0;
                
                if (this.app.currentView === 'jobs') {
                    this.updateJobDisplay(job);
                }
                
            } catch (error) {
                console.error(`Failed to poll job ${jobId}:`, error);
                errorCount++;
                
                if (errorCount >= maxErrors) {
                    console.error(`Max polling errors reached for job ${jobId}, stopping`);
                    this.stopPolling(jobId);
                    return;
                }
                
                currentInterval = Math.min(currentInterval * 1.5, maxInterval);
            }
            
            if (this.pollingIntervals.has(jobId)) {
                const timeoutId = setTimeout(poll, currentInterval);
                this.pollingIntervals.set(jobId, timeoutId);
            }
        };

        const timeoutId = setTimeout(poll, currentInterval);
        this.pollingIntervals.set(jobId, timeoutId);
    }

    stopPolling(jobId) {
        const timeoutId = this.pollingIntervals.get(jobId);
        if (timeoutId) {
            clearTimeout(timeoutId);
            this.pollingIntervals.delete(jobId);
        }
        this.lastStatusUpdate.delete(jobId);
    }

    updateJobDisplay(job) {
        const jobItem = document.querySelector(`[data-job-id="${job.id}"]`);
        if (!jobItem) return;

        const statusElement = jobItem.querySelector('.job-status');
        if (statusElement) {
            statusElement.className = `job-status ${job.status}`;
            statusElement.innerHTML = `
                <i class="fas fa-${this.app.getStatusIcon(job.status)}"></i>
                ${job.status}
            `;
        }

        const progressElement = jobItem.querySelector('.job-progress-bar');
        if (progressElement && job.progress !== undefined) {
            progressElement.style.width = `${job.progress}%`;
            
            const progressContainer = jobItem.querySelector('.job-progress');
            if (job.progress > 0 && !progressContainer) {
                const progressHtml = `
                    <div class="job-progress">
                        <div class="job-progress-bar" style="width: ${job.progress}%"></div>
                    </div>
                `;
                const metaElement = jobItem.querySelector('.job-meta');
                metaElement.insertAdjacentHTML('afterend', progressHtml);
            }
        }

        this.updateJobActions(jobItem, job);
    }

    updateJobActions(jobItem, job) {
        const actionsContainer = jobItem.querySelector('.job-actions');
        if (!actionsContainer) return;

        let actionsHtml = `
            <button class="btn btn-secondary" onclick="app.showJobDetails('${job.id}')">
                <i class="fas fa-info-circle"></i>
                Details
            </button>
        `;

        if (job.status === 'completed') {
            actionsHtml += `
                <button class="btn btn-success" onclick="app.downloadJobFiles('${job.id}')">
                    <i class="fas fa-download"></i>
                    Download
                </button>
            `;
        } else if (job.status === 'running' || job.status === 'pending' || job.status === 'queued') {
            actionsHtml += `
                <button class="btn btn-danger" onclick="app.cancelJob('${job.id}')">
                    <i class="fas fa-times"></i>
                    Cancel
                </button>
            `;
        }

        actionsContainer.innerHTML = actionsHtml;
    }

    notifyJobComplete(job) {
        const status = job.status;
        const title = `Job ${status}`;
        let message = `${job.name}`;
        let type = 'info';

        if (status === 'completed') {
            message += ' has completed successfully';
            type = 'success';
        } else if (status === 'failed') {
            message += ' has failed';
            type = 'error';
        } else if (status === 'cancelled') {
            message += ' was cancelled';
            type = 'warning';
        }

        this.app.showToast(message, type);

        if ('Notification' in window && Notification.permission === 'granted') {
            try {
                new Notification(title, {
                    body: message,
                    icon: '/favicon.ico',
                    tag: `job-${job.id}`,
                    requireInteraction: status === 'failed'
                });
            } catch (error) {
                console.error('Failed to show browser notification:', error);
            }
        }
    }

    async getJobFiles(jobId) {
        try {
            const files = await this.app.makeRequest(`/jobs/${jobId}/files`);
            return files || [];
        } catch (error) {
            console.error(`Failed to get files for job ${jobId}:`, error);
            return [];
        }
    }

    async downloadFile(jobId, filename) {
        try {
            const url = `${this.app.config.apiBaseUrl}/jobs/${jobId}/files/${filename}`;
            
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.app.showToast(`Download started: ${filename}`, 'success');
            
        } catch (error) {
            console.error(`Failed to download file ${filename}:`, error);
            this.app.showToast(`Failed to download ${filename}`, 'error');
        }
    }

    async downloadAllFiles(jobId) {
        try {
            const files = await this.getJobFiles(jobId);
            
            if (files.length === 0) {
                this.app.showToast('No files available for download', 'warning');
                return;
            }

            for (const file of files) {
                await this.downloadFile(jobId, file.filename);
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
        } catch (error) {
            console.error(`Failed to download all files for job ${jobId}:`, error);
            this.app.showToast('Failed to download files', 'error');
        }
    }

    getJobStatusBadge(status) {
        const badges = {
            pending: { icon: 'clock', label: 'Pending', class: 'pending' },
            queued: { icon: 'list', label: 'Queued', class: 'pending' },
            running: { icon: 'spinner fa-spin', label: 'Running', class: 'running' },
            completed: { icon: 'check-circle', label: 'Completed', class: 'completed' },
            failed: { icon: 'exclamation-circle', label: 'Failed', class: 'failed' },
            cancelled: { icon: 'times-circle', label: 'Cancelled', class: 'failed' }
        };

        const badge = badges[status] || badges.pending;
        
        return `
            <span class="job-status ${badge.class}">
                <i class="fas fa-${badge.icon}"></i>
                ${badge.label}
            </span>
        `;
    }

    formatJobDuration(startTime, endTime) {
        if (!startTime) return 'N/A';
        
        const start = new Date(startTime);
        const end = endTime ? new Date(endTime) : new Date();
        const duration = end - start;
        
        const seconds = Math.floor(duration / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }

    calculateEstimatedCompletion(job) {
        if (!job.started_at || !job.progress || job.progress <= 0) {
            return 'Unknown';
        }

        const startTime = new Date(job.started_at);
        const now = new Date();
        const elapsed = now - startTime;
        
        const estimatedTotal = (elapsed / job.progress) * 100;
        const remaining = estimatedTotal - elapsed;
        
        if (remaining <= 0) {
            return 'Soon';
        }

        const remainingMinutes = Math.ceil(remaining / (1000 * 60));
        
        if (remainingMinutes < 1) {
            return 'Less than 1 minute';
        } else if (remainingMinutes < 60) {
            return `${remainingMinutes} minute${remainingMinutes !== 1 ? 's' : ''}`;
        } else {
            const hours = Math.floor(remainingMinutes / 60);
            const minutes = remainingMinutes % 60;
            return `${hours}h ${minutes}m`;
        }
    }

    exportJobHistory(jobs) {
        const csvHeaders = [
            'Job ID',
            'Name',
            'Status',
            'Report Type',
            'Submitted At',
            'Started At',
            'Completed At',
            'Duration',
            'Progress'
        ];

        const csvRows = jobs.map(job => [
            job.id,
            job.name,
            job.status,
            job.jobDefinitionUri || '',
            job.submitted_at || '',
            job.started_at || '',
            job.completed_at || '',
            this.formatJobDuration(job.started_at, job.completed_at),
            `${job.progress || 0}%`
        ]);

        const csvContent = [csvHeaders, ...csvRows]
            .map(row => row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(','))
            .join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `datafit-job-history-${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }
    }

    destroy() {
        this.pollingIntervals.forEach(timeoutId => {
            clearTimeout(timeoutId);
        });
        this.pollingIntervals.clear();
        this.lastStatusUpdate.clear();
    }

    stopAllPolling() {
        this.pollingIntervals.forEach((timeoutId, jobId) => {
            clearTimeout(timeoutId);
        });
        this.pollingIntervals.clear();
        this.lastStatusUpdate.clear();
    }

    getActiveJobCount() {
        return this.pollingIntervals.size;
    }

    getPollingStatus() {
        const status = {};
        this.pollingIntervals.forEach((timeoutId, jobId) => {
            status[jobId] = {
                polling: true,
                lastUpdate: this.lastStatusUpdate.get(jobId) || 'unknown'
            };
        });
        return status;
    }
}
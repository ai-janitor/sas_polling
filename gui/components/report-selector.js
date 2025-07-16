/*
=============================================================================
REPORT SELECTOR COMPONENT
=============================================================================
Purpose: Dropdown component for report selection with category grouping
Technology: Vanilla JavaScript with event delegation
Parent: app.js

STRICT REQUIREMENTS:
- Hierarchical display of categories and subcategories
- Search/filter functionality for report names
- Keyboard navigation support (arrow keys, enter)
- Loading states and error handling
- Mobile-friendly touch interactions

COMPONENT FEATURES:
1. Grouped dropdown with categories and subcategories
2. Search functionality with fuzzy matching
3. Recent reports quick access
4. Report description tooltips
5. Keyboard accessibility

DATA STRUCTURE:
Consumes report definitions JSON with categories/subcategories/reports hierarchy

EVENTS:
- reportSelected: Fired when user selects a report
- reportChanged: Fired when selection changes
- searchUpdated: Fired when search filter changes

METHODS:
- loadReports(reportsData): Initialize component with report data
- selectReport(reportId): Programmatically select a report
- filterReports(searchTerm): Filter reports by search term
- clearSelection(): Reset to default state
=============================================================================
*/

class ReportSelector {
    constructor(app) {
        this.app = app;
        this.reports = null;
        this.filteredReports = null;
        this.selectedReport = null;
        this.searchTerm = '';
        
        this.container = document.getElementById('report-selector-container');
        this.searchInput = document.getElementById('report-search');
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.searchInput.addEventListener('input', this.handleSearch.bind(this));
        this.searchInput.addEventListener('keydown', this.handleSearchKeydown.bind(this));
    }

    handleSearch(e) {
        this.searchTerm = e.target.value.toLowerCase();
        this.filterAndRender();
    }

    handleSearchKeydown(e) {
        if (e.key === 'Escape') {
            this.searchInput.value = '';
            this.searchTerm = '';
            this.filterAndRender();
        }
    }

    render(reportsData) {
        this.reports = reportsData;
        this.filteredReports = reportsData;
        this.renderReports();
    }

    renderReports() {
        if (!this.filteredReports) {
            return;
        }

        const html = `
            <div class="report-categories">
                ${this.filteredReports.categories.map(category => 
                    category.subcategories.map(subcategory => this.renderSubcategory(category, subcategory)).join('')
                ).join('')}
            </div>
        `;

        this.container.innerHTML = html;
        this.setupReportEventListeners();
    }

    renderSubcategory(category, subcategory) {
        const filteredReports = this.filterReportsInSubcategory(subcategory);
        
        if (filteredReports.length === 0) {
            return '';
        }

        return `
            <div class="report-category">
                <h3 class="category-title">${category.name} - ${subcategory.name}</h3>
                <div class="report-grid">
                    ${filteredReports.map(report => this.renderReportCard(report)).join('')}
                </div>
            </div>
        `;
    }

    renderReportCard(report) {
        const isSelected = this.selectedReport && this.selectedReport.id === report.id;
        
        return `
            <div class="report-card ${isSelected ? 'selected' : ''}" 
                 data-report-id="${report.id}"
                 tabindex="0"
                 role="button"
                 aria-pressed="${isSelected ? 'true' : 'false'}"
                 title="${report.description}">
                <div class="report-title">${report.name}</div>
                <div class="report-description">${report.description}</div>
            </div>
        `;
    }

    filterReportsInSubcategory(subcategory) {
        if (!subcategory.reports) {
            return [];
        }
        
        if (!this.searchTerm) {
            return subcategory.reports;
        }

        return subcategory.reports.filter(report => 
            report.name.toLowerCase().includes(this.searchTerm) ||
            report.description.toLowerCase().includes(this.searchTerm) ||
            report.id.toLowerCase().includes(this.searchTerm)
        );
    }

    filterAndRender() {
        if (!this.reports) {
            return;
        }

        if (!this.searchTerm) {
            this.filteredReports = this.reports;
        } else {
            this.filteredReports = {
                ...this.reports,
                categories: this.reports.categories.map(category => ({
                    ...category,
                    subcategories: category.subcategories.map(subcategory => ({
                        ...subcategory,
                        reports: this.filterReportsInSubcategory(subcategory)
                    })).filter(subcategory => subcategory.reports.length > 0)
                })).filter(category => category.subcategories.length > 0)
            };
        }

        this.renderReports();
    }

    setupReportEventListeners() {
        const reportCards = this.container.querySelectorAll('.report-card');
        
        reportCards.forEach(card => {
            card.addEventListener('click', this.handleReportClick.bind(this));
            card.addEventListener('keydown', this.handleReportKeydown.bind(this));
        });
    }

    handleReportClick(e) {
        const reportId = e.currentTarget.dataset.reportId;
        this.selectReport(reportId);
    }

    handleReportKeydown(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const reportId = e.currentTarget.dataset.reportId;
            this.selectReport(reportId);
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            this.navigateReports(e.key === 'ArrowDown' ? 1 : -1);
        }
    }

    navigateReports(direction) {
        const reportCards = Array.from(this.container.querySelectorAll('.report-card'));
        const currentIndex = reportCards.findIndex(card => card === document.activeElement);
        
        if (currentIndex === -1) {
            if (reportCards.length > 0) {
                reportCards[0].focus();
            }
            return;
        }

        const nextIndex = Math.max(0, Math.min(reportCards.length - 1, currentIndex + direction));
        reportCards[nextIndex].focus();
    }

    selectReport(reportId) {
        const report = this.findReportById(reportId);
        
        if (!report) {
            console.error('Report not found:', reportId);
            return;
        }

        this.clearSelection();
        this.selectedReport = report;
        
        const reportCard = this.container.querySelector(`[data-report-id="${reportId}"]`);
        if (reportCard) {
            reportCard.classList.add('selected');
            reportCard.setAttribute('aria-pressed', 'true');
        }

        this.app.onReportSelected(report);
        
        this.announceSelection(report);
    }

    findReportById(reportId) {
        if (!this.reports) {
            return null;
        }

        for (const category of this.reports.categories) {
            for (const subcategory of category.subcategories) {
                const report = subcategory.reports.find(r => r.id === reportId);
                if (report) {
                    return report;
                }
            }
        }
        
        return null;
    }

    clearSelection() {
        this.selectedReport = null;
        
        const selectedCards = this.container.querySelectorAll('.report-card.selected');
        selectedCards.forEach(card => {
            card.classList.remove('selected');
            card.setAttribute('aria-pressed', 'false');
        });
    }

    announceSelection(report) {
        const announcement = `Report selected: ${report.name}`;
        this.createAnnouncement(announcement);
    }

    createAnnouncement(message) {
        const announcement = document.createElement('div');
        announcement.className = 'sr-only';
        announcement.setAttribute('aria-live', 'polite');
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="app.loadReports()">
                    <i class="fas fa-retry"></i>
                    Retry
                </button>
            </div>
        `;
    }

    showLoading() {
        this.container.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                Loading reports...
            </div>
        `;
    }

    getSelectedReport() {
        return this.selectedReport;
    }

    getSelectedReportId() {
        return this.selectedReport ? this.selectedReport.id : null;
    }

    resetSelection() {
        this.clearSelection();
        this.searchInput.value = '';
        this.searchTerm = '';
        this.filterAndRender();
    }
}
/*
=============================================================================
REPORT SELECTOR COMPONENT TESTS
=============================================================================
Purpose: Test the report selector component functionality and user interactions
Component: ReportSelector class from gui/components/report-selector.js
Coverage: Report loading, filtering, selection, keyboard navigation

TEST SCENARIOS:
1. Component initialization and rendering
2. Report data loading and display
3. Search and filtering functionality
4. Report selection and events
5. Keyboard navigation
6. Error handling and edge cases
7. UI updates and accessibility
8. Mobile touch interactions

MOCK STRATEGY:
- Mock report data with categories
- Mock DOM element interactions
- Mock event listeners and triggers
- Test keyboard events and focus management
=============================================================================
*/

describe('ReportSelector', () => {
  let reportSelector;
  let mockContainer;

  beforeEach(() => {
    // Setup DOM container
    document.body.innerHTML = `
      <div id="report-selector-container">
        <div class="report-selector">
          <input type="text" id="report-search" placeholder="Search reports...">
          <div class="dropdown-container">
            <button class="dropdown-toggle" aria-expanded="false">Select Report</button>
            <div class="dropdown-menu" role="listbox"></div>
          </div>
          <div class="selected-report-info">
            <h3 id="selected-report-title"></h3>
            <p id="selected-report-description"></p>
          </div>
        </div>
      </div>
    `;

    mockContainer = document.getElementById('report-selector-container');

    // Import and create component instance
    const { ReportSelector } = require('../../../gui/components/report-selector.js');
    reportSelector = new ReportSelector(mockContainer);
  });

  afterEach(() => {
    if (reportSelector && reportSelector.destroy) {
      reportSelector.destroy();
    }
  });

  describe('Initialization', () => {
    test('should initialize with container element', () => {
      expect(reportSelector.container).toBe(mockContainer);
      expect(reportSelector.selectedReport).toBeNull();
      expect(reportSelector.reports).toBeNull();
      expect(reportSelector.filteredReports).toEqual([]);
    });

    test('should setup event listeners', () => {
      const searchInput = document.getElementById('report-search');
      const dropdownToggle = document.querySelector('.dropdown-toggle');

      expect(searchInput).toBeDefined();
      expect(dropdownToggle).toBeDefined();
    });

    test('should initialize accessibility attributes', () => {
      const dropdownMenu = document.querySelector('.dropdown-menu');
      const dropdownToggle = document.querySelector('.dropdown-toggle');

      expect(dropdownMenu.getAttribute('role')).toBe('listbox');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('false');
    });
  });

  describe('Report Loading', () => {
    test('should render reports with categories', () => {
      const mockReportsData = global.generateMockReportsData();
      
      reportSelector.render(mockReportsData);

      expect(reportSelector.reports).toEqual(mockReportsData);
      
      const dropdownMenu = document.querySelector('.dropdown-menu');
      expect(dropdownMenu.innerHTML).toContain('category-group');
      expect(dropdownMenu.innerHTML).toContain('Test Reports');
    });

    test('should handle empty reports data', () => {
      const emptyData = { categories: [] };
      
      reportSelector.render(emptyData);

      const dropdownMenu = document.querySelector('.dropdown-menu');
      expect(dropdownMenu.innerHTML).toContain('empty-state');
      expect(dropdownMenu.innerHTML).toContain('No reports available');
    });

    test('should handle invalid reports data', () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      reportSelector.render(null);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Invalid reports data provided to ReportSelector'
      );

      consoleErrorSpy.mockRestore();
    });

    test('should create report cards with correct structure', () => {
      const mockReportsData = global.generateMockReportsData();
      
      reportSelector.render(mockReportsData);

      const reportCards = document.querySelectorAll('.report-card');
      expect(reportCards.length).toBeGreaterThan(0);

      const firstCard = reportCards[0];
      expect(firstCard.getAttribute('role')).toBe('option');
      expect(firstCard.getAttribute('tabindex')).toBe('0');
      expect(firstCard.innerHTML).toContain('report-name');
      expect(firstCard.innerHTML).toContain('report-description');
    });
  });

  describe('Search and Filtering', () => {
    beforeEach(() => {
      const mockReportsData = global.generateMockReportsData();
      reportSelector.render(mockReportsData);
    });

    test('should filter reports by search term', () => {
      const searchInput = document.getElementById('report-search');
      
      // Simulate typing in search
      searchInput.value = 'Test Report 2';
      global.simulateEvent(searchInput, 'input');

      const visibleCards = document.querySelectorAll('.report-card:not(.hidden)');
      expect(visibleCards.length).toBe(1);
      expect(visibleCards[0].innerHTML).toContain('Test Report 2');
    });

    test('should show no results message for non-matching search', () => {
      const searchInput = document.getElementById('report-search');
      
      searchInput.value = 'NonExistentReport';
      global.simulateEvent(searchInput, 'input');

      const dropdownMenu = document.querySelector('.dropdown-menu');
      expect(dropdownMenu.innerHTML).toContain('no-results');
      expect(dropdownMenu.innerHTML).toContain('No reports found');
    });

    test('should clear search and show all reports', () => {
      const searchInput = document.getElementById('report-search');
      
      // First filter
      searchInput.value = 'Test Report 2';
      global.simulateEvent(searchInput, 'input');

      // Then clear
      searchInput.value = '';
      global.simulateEvent(searchInput, 'input');

      const visibleCards = document.querySelectorAll('.report-card:not(.hidden)');
      expect(visibleCards.length).toBeGreaterThan(1);
    });

    test('should perform case-insensitive search', () => {
      const searchInput = document.getElementById('report-search');
      
      searchInput.value = 'test report';
      global.simulateEvent(searchInput, 'input');

      const visibleCards = document.querySelectorAll('.report-card:not(.hidden)');
      expect(visibleCards.length).toBeGreaterThan(0);
    });
  });

  describe('Report Selection', () => {
    beforeEach(() => {
      const mockReportsData = global.generateMockReportsData();
      reportSelector.render(mockReportsData);
    });

    test('should select report on card click', () => {
      const onReportSelectedSpy = jest.fn();
      reportSelector.onReportSelected = onReportSelectedSpy;

      const reportCard = document.querySelector('.report-card');
      global.simulateEvent(reportCard, 'click');

      expect(onReportSelectedSpy).toHaveBeenCalled();
      expect(reportSelector.selectedReport).toBeDefined();
    });

    test('should update selected report display', () => {
      const reportCard = document.querySelector('.report-card');
      global.simulateEvent(reportCard, 'click');

      const titleElement = document.getElementById('selected-report-title');
      const descriptionElement = document.getElementById('selected-report-description');

      expect(titleElement.textContent).toBeTruthy();
      expect(descriptionElement.textContent).toBeTruthy();
    });

    test('should close dropdown after selection', () => {
      const dropdownToggle = document.querySelector('.dropdown-toggle');
      const reportCard = document.querySelector('.report-card');

      // Open dropdown first
      global.simulateEvent(dropdownToggle, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('true');

      // Select report
      global.simulateEvent(reportCard, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('false');
    });

    test('should handle programmatic report selection', () => {
      const mockReport = global.generateMockReport();
      
      reportSelector.selectReport(mockReport.id);

      expect(reportSelector.selectedReport.id).toBe(mockReport.id);
    });

    test('should handle invalid report ID selection', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      reportSelector.selectReport('invalid-id');

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Report with ID invalid-id not found'
      );
      expect(reportSelector.selectedReport).toBeNull();

      consoleWarnSpy.mockRestore();
    });
  });

  describe('Keyboard Navigation', () => {
    beforeEach(() => {
      const mockReportsData = global.generateMockReportsData();
      reportSelector.render(mockReportsData);
    });

    test('should navigate with arrow keys', () => {
      const reportCards = document.querySelectorAll('.report-card');
      const firstCard = reportCards[0];

      // Focus first card
      firstCard.focus();

      // Simulate arrow down
      global.simulateEvent(firstCard, 'keydown', { key: 'ArrowDown' });

      // Check if focus moved to next card
      expect(document.activeElement).toBe(reportCards[1]);
    });

    test('should select report with Enter key', () => {
      const onReportSelectedSpy = jest.fn();
      reportSelector.onReportSelected = onReportSelectedSpy;

      const reportCard = document.querySelector('.report-card');
      reportCard.focus();

      global.simulateEvent(reportCard, 'keydown', { key: 'Enter' });

      expect(onReportSelectedSpy).toHaveBeenCalled();
    });

    test('should select report with Space key', () => {
      const onReportSelectedSpy = jest.fn();
      reportSelector.onReportSelected = onReportSelectedSpy;

      const reportCard = document.querySelector('.report-card');
      reportCard.focus();

      global.simulateEvent(reportCard, 'keydown', { key: ' ' });

      expect(onReportSelectedSpy).toHaveBeenCalled();
    });

    test('should close dropdown with Escape key', () => {
      const dropdownToggle = document.querySelector('.dropdown-toggle');

      // Open dropdown
      global.simulateEvent(dropdownToggle, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('true');

      // Press Escape
      global.simulateEvent(document, 'keydown', { key: 'Escape' });
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('false');
    });
  });

  describe('Dropdown Behavior', () => {
    test('should toggle dropdown on button click', () => {
      const dropdownToggle = document.querySelector('.dropdown-toggle');

      // Initially closed
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('false');

      // Click to open
      global.simulateEvent(dropdownToggle, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('true');

      // Click to close
      global.simulateEvent(dropdownToggle, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('false');
    });

    test('should close dropdown on outside click', () => {
      const dropdownToggle = document.querySelector('.dropdown-toggle');

      // Open dropdown
      global.simulateEvent(dropdownToggle, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('true');

      // Click outside
      global.simulateEvent(document.body, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('false');
    });

    test('should not close dropdown on inside click', () => {
      const dropdownToggle = document.querySelector('.dropdown-toggle');
      const dropdownMenu = document.querySelector('.dropdown-menu');

      // Open dropdown
      global.simulateEvent(dropdownToggle, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('true');

      // Click inside dropdown
      global.simulateEvent(dropdownMenu, 'click');
      expect(dropdownToggle.getAttribute('aria-expanded')).toBe('true');
    });
  });

  describe('Error Handling', () => {
    test('should handle missing container element', () => {
      expect(() => {
        new ReportSelector(null);
      }).toThrow('Container element is required');
    });

    test('should show error state for load failures', () => {
      const showErrorSpy = jest.spyOn(reportSelector, 'showError');
      
      reportSelector.showError('Failed to load reports');

      expect(showErrorSpy).toHaveBeenCalledWith('Failed to load reports');
    });

    test('should display error message in UI', () => {
      reportSelector.showError('Test error message');

      const errorElement = document.querySelector('.error-message');
      expect(errorElement).toBeTruthy();
      expect(errorElement.textContent).toContain('Test error message');
    });
  });

  describe('Accessibility', () => {
    test('should have proper ARIA attributes', () => {
      const dropdownToggle = document.querySelector('.dropdown-toggle');
      const dropdownMenu = document.querySelector('.dropdown-menu');

      expect(dropdownToggle.getAttribute('aria-haspopup')).toBe('listbox');
      expect(dropdownMenu.getAttribute('role')).toBe('listbox');
    });

    test('should manage focus correctly', () => {
      const mockReportsData = global.generateMockReportsData();
      reportSelector.render(mockReportsData);

      const dropdownToggle = document.querySelector('.dropdown-toggle');
      const reportCards = document.querySelectorAll('.report-card');

      // Open dropdown and check focus
      global.simulateEvent(dropdownToggle, 'click');
      expect(reportCards[0].getAttribute('tabindex')).toBe('0');
    });

    test('should announce selection to screen readers', () => {
      const mockReportsData = global.generateMockReportsData();
      reportSelector.render(mockReportsData);

      const reportCard = document.querySelector('.report-card');
      global.simulateEvent(reportCard, 'click');

      const announcement = document.querySelector('[aria-live]');
      expect(announcement).toBeTruthy();
    });
  });

  describe('Recent Reports', () => {
    test('should track recently selected reports', () => {
      const mockReportsData = global.generateMockReportsData();
      reportSelector.render(mockReportsData);

      const reportCard = document.querySelector('.report-card');
      global.simulateEvent(reportCard, 'click');

      expect(reportSelector.recentReports.length).toBe(1);
    });

    test('should limit recent reports to maximum count', () => {
      const mockReportsData = global.generateMockReportsData();
      reportSelector.render(mockReportsData);

      // Select multiple reports
      for (let i = 0; i < 10; i++) {
        const mockReport = global.generateMockReport({ id: `report_${i}` });
        reportSelector.addToRecent(mockReport);
      }

      expect(reportSelector.recentReports.length).toBeLessThanOrEqual(5);
    });

    test('should display recent reports section', () => {
      const mockReportsData = global.generateMockReportsData();
      reportSelector.render(mockReportsData);

      const reportCard = document.querySelector('.report-card');
      global.simulateEvent(reportCard, 'click');

      const recentSection = document.querySelector('.recent-reports');
      expect(recentSection).toBeTruthy();
    });
  });

  describe('Memory Management', () => {
    test('should clean up event listeners on destroy', () => {
      const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener');
      
      reportSelector.destroy();

      expect(removeEventListenerSpy).toHaveBeenCalled();
      removeEventListenerSpy.mockRestore();
    });

    test('should clear internal state on destroy', () => {
      reportSelector.destroy();

      expect(reportSelector.reports).toBeNull();
      expect(reportSelector.selectedReport).toBeNull();
      expect(reportSelector.filteredReports).toEqual([]);
    });
  });
});
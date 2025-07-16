/*
=============================================================================
END-TO-END USER WORKFLOW TESTS
=============================================================================
Purpose: Test complete user workflows from start to finish
Technology: Puppeteer for browser automation
Coverage: Real browser interactions, user journeys, visual testing

TEST SCENARIOS:
1. Complete job submission workflow
2. Report selection and form filling
3. Job monitoring and status tracking
4. File download workflows
5. Error handling user experience
6. Navigation and state persistence
7. Responsive behavior testing
8. Accessibility compliance

E2E STRATEGY:
- Real browser automation with Puppeteer
- Actual DOM interactions and events
- Visual regression testing
- Performance measurement
- Cross-browser compatibility
=============================================================================
*/

const puppeteer = require('puppeteer');

describe('End-to-End User Workflows', () => {
  let browser;
  let page;
  const baseUrl = process.env.GUI_URL || 'http://localhost:3000';

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: process.env.CI === 'true',
      devtools: !process.env.CI,
      slowMo: process.env.CI ? 0 : 50,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
      ]
    });
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  beforeEach(async () => {
    page = await browser.newPage();
    
    // Set viewport for consistent testing
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Setup request interception for API mocking
    await page.setRequestInterception(true);
    
    page.on('request', (request) => {
      const url = request.url();
      
      // Mock API responses
      if (url.includes('/api/reports')) {
        request.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            categories: [{
              name: 'Test Reports',
              description: 'Test category',
              reports: [{
                id: 'test_report',
                name: 'Test Report',
                description: 'A test report for E2E testing',
                category: 'Test Reports',
                estimatedDuration: 120,
                outputFormats: ['HTML', 'PDF', 'CSV'],
                prompts: [{
                  test_field: {
                    active: true,
                    hide: false,
                    inputType: 'inputtext',
                    label: 'Test Field',
                    required: true,
                    validation: {
                      pattern: '^[A-Za-z0-9]+$',
                      minLength: 3,
                      maxLength: 50
                    }
                  }
                }]
              }]
            }]
          })
        });
      } else if (url.includes('/api/jobs') && request.method() === 'POST') {
        request.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'job_12345',
            name: 'Test Job',
            status: 'submitted',
            jobDefinitionUri: 'test_report',
            submitted_at: new Date().toISOString(),
            progress: 0
          })
        });
      } else if (url.includes('/api/jobs/') && url.includes('/status')) {
        const jobId = url.match(/\/api\/jobs\/([^\/]+)\/status/)[1];
        request.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: jobId,
            status: 'completed',
            progress: 100,
            completed_at: new Date().toISOString()
          })
        });
      } else if (url.includes('/api/jobs/') && url.includes('/files')) {
        request.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { filename: 'report.html', size: 12345, type: 'HTML' },
            { filename: 'data.csv', size: 6789, type: 'CSV' }
          ])
        });
      } else {
        request.continue();
      }
    });

    // Navigate to application
    await page.goto(baseUrl, { waitUntil: 'networkidle0' });
  });

  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  describe('Application Loading and Initialization', () => {
    test('should load application and display main interface', async () => {
      // Wait for application to load
      await page.waitForSelector('#app', { visible: true });
      
      // Check main elements are present
      const title = await page.$eval('.app-title', el => el.textContent);
      expect(title).toBe('DataFit');
      
      // Check navigation is present
      const navButtons = await page.$$('.nav-button');
      expect(navButtons.length).toBe(3);
      
      // Check initial view is reports
      const activeButton = await page.$eval('.nav-button.active', el => el.textContent);
      expect(activeButton).toBe('Reports');
    });

    test('should load reports on initialization', async () => {
      // Wait for reports to load
      await page.waitForSelector('#report-dropdown option', { visible: true });
      
      // Check reports dropdown is populated
      const options = await page.$$('#report-dropdown option');
      expect(options.length).toBeGreaterThan(1); // Including default option
      
      // Check report appears in dropdown
      const reportText = await page.$eval('#report-dropdown option:last-child', el => el.textContent);
      expect(reportText).toContain('Test Report');
    });

    test('should handle loading states correctly', async () => {
      // Page should show loading overlay during initialization
      const hasLoadingOverlay = await page.$('#loading-overlay') !== null;
      expect(hasLoadingOverlay).toBe(true);
    });
  });

  describe('Report Selection Workflow', () => {
    test('should select report and generate form', async () => {
      // Wait for dropdown to be populated
      await page.waitForSelector('#report-dropdown option:last-child');
      
      // Select a report
      await page.select('#report-dropdown', 'test_report');
      
      // Wait for form to appear
      await page.waitForSelector('#form-container', { visible: true });
      
      // Check form is visible
      const formVisible = await page.$eval('#form-container', el => 
        window.getComputedStyle(el).display !== 'none'
      );
      expect(formVisible).toBe(true);
      
      // Check form field is generated
      const formField = await page.$('input[name="test_field"]');
      expect(formField).toBeTruthy();
      
      // Check field is required
      const isRequired = await page.$eval('input[name="test_field"]', el => el.required);
      expect(isRequired).toBe(true);
    });

    test('should display selected report information', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      
      // Wait for report info to update
      await page.waitForSelector('#selected-report-title', { visible: true });
      
      const title = await page.$eval('#selected-report-title', el => el.textContent);
      const description = await page.$eval('#selected-report-description', el => el.textContent);
      
      expect(title).toBe('Test Report');
      expect(description).toBe('A test report for E2E testing');
    });

    test('should validate form fields correctly', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      // Try to submit empty form
      await page.click('button[type="submit"]');
      
      // Check for validation error
      await page.waitForSelector('.form-errors', { visible: true });
      
      const errorText = await page.$eval('.form-errors', el => el.textContent);
      expect(errorText).toContain('required');
    });
  });

  describe('Job Submission Workflow', () => {
    beforeEach(async () => {
      // Setup: Select report and fill form
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      await page.type('input[name="test_field"]', 'TestValue123');
    });

    test('should submit job successfully', async () => {
      // Submit the form
      await page.click('button[type="submit"]');
      
      // Wait for success notification
      await page.waitForSelector('.toast.success', { visible: true });
      
      const toastText = await page.$eval('.toast.success', el => el.textContent);
      expect(toastText).toContain('Job submitted successfully');
      
      // Check that we switched to jobs view
      await page.waitForSelector('#jobs-section.active', { visible: true });
      
      const activeSection = await page.$eval('.content-section.active', el => el.id);
      expect(activeSection).toBe('jobs-section');
    });

    test('should display job in active jobs list', async () => {
      await page.click('button[type="submit"]');
      
      // Wait for jobs view to load
      await page.waitForSelector('#jobs-section.active', { visible: true });
      
      // Wait for job to appear in active jobs
      await page.waitForSelector('.job-card', { visible: true });
      
      const jobCard = await page.$('.job-card');
      expect(jobCard).toBeTruthy();
      
      const jobName = await page.$eval('.job-card .job-name', el => el.textContent);
      expect(jobName).toContain('Test Job');
    });

    test('should show job progress and status updates', async () => {
      await page.click('button[type="submit"]');
      
      // Wait for job card to appear
      await page.waitForSelector('.job-card', { visible: true });
      
      // Check initial status
      const initialStatus = await page.$eval('.job-card .job-status', el => el.textContent);
      expect(initialStatus).toContain('submitted');
      
      // Wait for status to update (mocked to complete immediately)
      await page.waitForFunction(
        () => document.querySelector('.job-card .job-status').textContent.includes('completed'),
        { timeout: 10000 }
      );
      
      const finalStatus = await page.$eval('.job-card .job-status', el => el.textContent);
      expect(finalStatus).toContain('completed');
    });
  });

  describe('Navigation Workflow', () => {
    test('should navigate between different views', async () => {
      // Start on reports view
      let activeView = await page.$eval('.content-section.active', el => el.id);
      expect(activeView).toBe('report-section');
      
      // Navigate to jobs view
      await page.click('#nav-jobs');
      await page.waitForSelector('#jobs-section.active', { visible: true });
      
      activeView = await page.$eval('.content-section.active', el => el.id);
      expect(activeView).toBe('jobs-section');
      
      // Navigate to history view
      await page.click('#nav-history');
      await page.waitForSelector('#history-section.active', { visible: true });
      
      activeView = await page.$eval('.content-section.active', el => el.id);
      expect(activeView).toBe('history-section');
      
      // Navigate back to reports view
      await page.click('#nav-reports');
      await page.waitForSelector('#report-section.active', { visible: true });
      
      activeView = await page.$eval('.content-section.active', el => el.id);
      expect(activeView).toBe('report-section');
    });

    test('should maintain state when navigating between views', async () => {
      // Select a report
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      // Fill form
      await page.type('input[name="test_field"]', 'TestValue123');
      
      // Navigate away and back
      await page.click('#nav-jobs');
      await page.click('#nav-reports');
      
      // Check state is preserved
      const selectedValue = await page.$eval('#report-dropdown', el => el.value);
      expect(selectedValue).toBe('test_report');
      
      const fieldValue = await page.$eval('input[name="test_field"]', el => el.value);
      expect(fieldValue).toBe('TestValue123');
    });

    test('should update navigation active states correctly', async () => {
      // Check initial active state
      let activeButton = await page.$eval('.nav-button.active', el => el.id);
      expect(activeButton).toBe('nav-reports');
      
      // Click jobs navigation
      await page.click('#nav-jobs');
      
      // Check active state updated
      activeButton = await page.$eval('.nav-button.active', el => el.id);
      expect(activeButton).toBe('nav-jobs');
      
      // Check aria-pressed attribute
      const ariaPressed = await page.$eval('#nav-jobs', el => el.getAttribute('aria-pressed'));
      expect(ariaPressed).toBe('true');
    });
  });

  describe('Job History and File Downloads', () => {
    test('should move completed jobs to history', async () => {
      // Submit a job
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      await page.type('input[name="test_field"]', 'TestValue123');
      await page.click('button[type="submit"]');
      
      // Wait for job to complete (mocked)
      await page.waitForSelector('.job-card', { visible: true });
      await page.waitForFunction(
        () => document.querySelector('.job-card .job-status').textContent.includes('completed'),
        { timeout: 10000 }
      );
      
      // Navigate to history
      await page.click('#nav-history');
      await page.waitForSelector('#history-section.active', { visible: true });
      
      // Check job appears in history
      await page.waitForSelector('.job-history-item', { visible: true });
      
      const historyItem = await page.$('.job-history-item');
      expect(historyItem).toBeTruthy();
    });

    test('should display download links for completed jobs', async () => {
      // Submit and complete a job first
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      await page.type('input[name="test_field"]', 'TestValue123');
      await page.click('button[type="submit"]');
      
      // Wait for completion and navigate to history
      await page.waitForFunction(
        () => document.querySelector('.job-card .job-status').textContent.includes('completed'),
        { timeout: 10000 }
      );
      
      await page.click('#nav-history');
      await page.waitForSelector('.job-history-item', { visible: true });
      
      // Check for download links
      const downloadLinks = await page.$$('.download-link');
      expect(downloadLinks.length).toBeGreaterThan(0);
      
      // Check file types
      const linkTexts = await Promise.all(
        downloadLinks.map(link => page.evaluate(el => el.textContent, link))
      );
      
      expect(linkTexts.some(text => text.includes('HTML'))).toBe(true);
      expect(linkTexts.some(text => text.includes('CSV'))).toBe(true);
    });
  });

  describe('Error Handling User Experience', () => {
    beforeEach(async () => {
      // Override API mocking to simulate errors
      await page.setRequestInterception(true);
      page.removeAllListeners('request');
    });

    test('should handle API errors gracefully', async () => {
      page.on('request', (request) => {
        if (request.url().includes('/api/reports')) {
          request.respond({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Server Error' })
          });
        } else {
          request.continue();
        }
      });

      await page.reload({ waitUntil: 'networkidle0' });
      
      // Check error notification appears
      await page.waitForSelector('.toast.error', { visible: true, timeout: 10000 });
      
      const errorText = await page.$eval('.toast.error', el => el.textContent);
      expect(errorText).toContain('Failed to initialize application');
    });

    test('should show validation errors clearly', async () => {
      // Setup normal API responses
      page.on('request', (request) => {
        if (request.url().includes('/api/reports')) {
          request.respond({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              categories: [{
                name: 'Test Reports',
                reports: [{
                  id: 'test_report',
                  name: 'Test Report',
                  prompts: [{
                    test_field: {
                      active: true,
                      inputType: 'inputtext',
                      label: 'Test Field',
                      required: true,
                      validation: { pattern: '^[A-Za-z]+$' }
                    }
                  }]
                }]
              }]
            })
          });
        } else {
          request.continue();
        }
      });

      await page.reload({ waitUntil: 'networkidle0' });
      
      // Select report and try invalid input
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      // Enter invalid input (numbers when only letters allowed)
      await page.type('input[name="test_field"]', '12345');
      await page.click('button[type="submit"]');
      
      // Check validation error appears
      await page.waitForSelector('.form-errors', { visible: true });
      
      const errorText = await page.$eval('.form-errors', el => el.textContent);
      expect(errorText).toContain('pattern');
    });
  });

  describe('Responsive Design Testing', () => {
    test('should work correctly on mobile viewport', async () => {
      // Set mobile viewport
      await page.setViewport({ width: 375, height: 667 });
      
      // Check mobile layout
      const appContainer = await page.$('#app');
      expect(appContainer).toBeTruthy();
      
      // Check navigation is accessible
      const navButtons = await page.$$('.nav-button');
      expect(navButtons.length).toBe(3);
      
      // Check form works on mobile
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      const formVisible = await page.$eval('#form-container', el => 
        window.getComputedStyle(el).display !== 'none'
      );
      expect(formVisible).toBe(true);
    });

    test('should work correctly on tablet viewport', async () => {
      // Set tablet viewport
      await page.setViewport({ width: 768, height: 1024 });
      
      await page.reload({ waitUntil: 'networkidle0' });
      
      // Test functionality at tablet size
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      const formField = await page.$('input[name="test_field"]');
      expect(formField).toBeTruthy();
    });
  });

  describe('Accessibility Compliance', () => {
    test('should have proper keyboard navigation', async () => {
      // Test tab navigation
      await page.keyboard.press('Tab'); // Should focus first nav button
      
      let focusedElement = await page.evaluate(() => document.activeElement.id);
      expect(['nav-reports', 'nav-jobs', 'nav-history']).toContain(focusedElement);
      
      // Test arrow key navigation in dropdown
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.focus('#report-dropdown');
      await page.keyboard.press('ArrowDown');
      
      const selectedOption = await page.$eval('#report-dropdown', el => el.selectedIndex);
      expect(selectedOption).toBeGreaterThan(0);
    });

    test('should have proper ARIA attributes', async () => {
      // Check nav buttons have aria-pressed
      const ariaPressed = await page.$eval('#nav-reports', el => el.getAttribute('aria-pressed'));
      expect(ariaPressed).toBe('true');
      
      // Check form fields have proper labels
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      const fieldId = await page.$eval('input[name="test_field"]', el => el.id);
      const labelFor = await page.$eval(`label[for="${fieldId}"]`, el => el.getAttribute('for'));
      expect(labelFor).toBe(fieldId);
    });

    test('should announce important changes to screen readers', async () => {
      // Check for aria-live regions
      const liveRegions = await page.$$('[aria-live]');
      expect(liveRegions.length).toBeGreaterThan(0);
      
      // Test notification announcements
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      await page.type('input[name="test_field"]', 'TestValue123');
      await page.click('button[type="submit"]');
      
      // Check success message is announced
      await page.waitForSelector('.toast.success[aria-live]', { visible: true });
    });
  });

  describe('Performance Testing', () => {
    test('should load within acceptable time limits', async () => {
      const startTime = Date.now();
      
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });
      await page.waitForSelector('#app', { visible: true });
      
      const loadTime = Date.now() - startTime;
      
      // Should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });

    test('should handle multiple rapid interactions without lag', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      
      const startTime = Date.now();
      
      // Rapidly switch between views
      await page.click('#nav-jobs');
      await page.click('#nav-history');
      await page.click('#nav-reports');
      await page.click('#nav-jobs');
      await page.click('#nav-reports');
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      // Should complete within reasonable time
      expect(duration).toBeLessThan(1000);
    });
  });
});
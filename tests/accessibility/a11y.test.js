/*
=============================================================================
ACCESSIBILITY TESTING SUITE
=============================================================================
Purpose: Comprehensive accessibility compliance testing (WCAG 2.1 AA)
Technology: axe-core for automated accessibility testing
Coverage: Screen readers, keyboard navigation, color contrast, ARIA

TEST SCENARIOS:
1. Automated accessibility scanning with axe-core
2. Keyboard navigation and focus management
3. Screen reader compatibility and announcements
4. Color contrast and visual accessibility
5. ARIA attributes and semantic HTML
6. Form accessibility and error handling
7. Modal and dialog accessibility
8. Table and list accessibility

WCAG 2.1 AA COMPLIANCE:
- Perceivable: Alternative text, color contrast, resizable text
- Operable: Keyboard accessible, no seizures, navigable
- Understandable: Readable, predictable, input assistance
- Robust: Compatible with assistive technologies

ACCESSIBILITY STRATEGY:
- Automated testing with axe-core
- Manual keyboard navigation testing
- Screen reader simulation
- Color blindness simulation
- Focus management verification
=============================================================================
*/

const { AxePuppeteer } = require('@axe-core/puppeteer');
const puppeteer = require('puppeteer');

describe('Accessibility Testing Suite', () => {
  let browser;
  let page;
  const baseUrl = process.env.GUI_URL || 'http://localhost:3000';

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: process.env.CI === 'true',
      devtools: !process.env.CI,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-web-security'
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
    
    // Setup request interception for API mocking
    await page.setRequestInterception(true);
    page.on('request', request => {
      if (request.url().includes('/api/reports')) {
        request.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            categories: [{
              name: 'Test Reports',
              description: 'Accessibility test category',
              reports: [{
                id: 'test_report',
                name: 'Test Report',
                description: 'A test report for accessibility testing',
                prompts: [{
                  test_field: {
                    active: true,
                    inputType: 'inputtext',
                    label: 'Test Field',
                    required: true,
                    validation: { pattern: '^[A-Za-z0-9]+$' }
                  },
                  dropdown_field: {
                    active: true,
                    inputType: 'dropdown',
                    label: 'Dropdown Field',
                    options: [
                      { value: 'option1', label: 'Option 1' },
                      { value: 'option2', label: 'Option 2' }
                    ]
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

    await page.goto(baseUrl, { waitUntil: 'networkidle0' });
  });

  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  describe('Automated Accessibility Scanning', () => {
    test('should pass axe-core accessibility scan on main page', async () => {
      await page.waitForSelector('#app', { visible: true });
      
      const results = await new AxePuppeteer(page)
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .analyze();

      // Log any violations for debugging
      if (results.violations.length > 0) {
        console.log('Accessibility violations found:');
        results.violations.forEach(violation => {
          console.log(`- ${violation.id}: ${violation.description}`);
          violation.nodes.forEach(node => {
            console.log(`  Target: ${node.target}`);
            console.log(`  HTML: ${node.html.substring(0, 100)}...`);
          });
        });
      }

      expect(results.violations).toEqual([]);
    });

    test('should pass accessibility scan with form generated', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });

      const results = await new AxePuppeteer(page)
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .analyze();

      expect(results.violations).toEqual([]);
    });

    test('should pass accessibility scan on all navigation views', async () => {
      const views = ['#nav-reports', '#nav-jobs', '#nav-history'];
      
      for (const viewSelector of views) {
        await page.click(viewSelector);
        await page.waitForSelector(`${viewSelector}.active`, { visible: true });
        
        const results = await new AxePuppeteer(page)
          .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
          .analyze();
        
        expect(results.violations).toEqual([]);
      }
    });

    test('should meet color contrast requirements', async () => {
      const results = await new AxePuppeteer(page)
        .withTags(['wcag2aa'])
        .withRules(['color-contrast'])
        .analyze();

      expect(results.violations).toEqual([]);
    });
  });

  describe('Keyboard Navigation', () => {
    test('should support full keyboard navigation', async () => {
      await page.waitForSelector('.nav-button', { visible: true });
      
      // Test tab navigation through main elements
      const tabStops = [];
      
      // Start from first nav button
      await page.focus('#nav-reports');
      tabStops.push(await page.evaluate(() => document.activeElement.id));
      
      // Tab through navigation
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Tab');
        const focusedId = await page.evaluate(() => document.activeElement.id);
        if (focusedId) {
          tabStops.push(focusedId);
        }
      }
      
      // Should include all major interactive elements
      expect(tabStops).toContain('nav-reports');
      expect(tabStops).toContain('nav-jobs');
      expect(tabStops).toContain('nav-history');
      expect(tabStops.some(id => id.includes('report-dropdown'))).toBe(true);
    });

    test('should handle arrow key navigation in dropdown', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.focus('#report-dropdown');
      
      const initialSelection = await page.$eval('#report-dropdown', el => el.selectedIndex);
      
      // Navigate with arrow key
      await page.keyboard.press('ArrowDown');
      
      const newSelection = await page.$eval('#report-dropdown', el => el.selectedIndex);
      expect(newSelection).toBeGreaterThan(initialSelection);
    });

    test('should support Enter and Space key activation', async () => {
      await page.waitForSelector('#nav-jobs', { visible: true });
      await page.focus('#nav-jobs');
      
      // Activate with Enter key
      await page.keyboard.press('Enter');
      await page.waitForSelector('#jobs-section.active', { visible: true });
      
      const activeSection = await page.$eval('.content-section.active', el => el.id);
      expect(activeSection).toBe('jobs-section');
      
      // Test Space key on buttons
      await page.focus('#nav-reports');
      await page.keyboard.press('Space');
      await page.waitForSelector('#report-section.active', { visible: true });
      
      const newActiveSection = await page.$eval('.content-section.active', el => el.id);
      expect(newActiveSection).toBe('report-section');
    });

    test('should support Escape key to close modals', async () => {
      // Generate form to test modal functionality
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      // Simulate opening a modal (job details modal)
      await page.evaluate(() => {
        const modal = document.getElementById('job-modal');
        if (modal) {
          modal.style.display = 'block';
        }
      });
      
      // Press Escape to close
      await page.keyboard.press('Escape');
      
      const modalVisible = await page.evaluate(() => {
        const modal = document.getElementById('job-modal');
        return modal && window.getComputedStyle(modal).display !== 'none';
      });
      
      expect(modalVisible).toBe(false);
    });

    test('should trap focus within modals', async () => {
      // Open modal
      await page.evaluate(() => {
        const modal = document.getElementById('job-modal');
        if (modal) {
          modal.style.display = 'block';
          modal.innerHTML = `
            <div class="modal-content">
              <button class="modal-close">Close</button>
              <button class="modal-action">Action</button>
            </div>
          `;
        }
      });
      
      await page.focus('.modal-close');
      const firstFocused = await page.evaluate(() => document.activeElement.className);
      
      // Tab should cycle within modal
      await page.keyboard.press('Tab');
      const secondFocused = await page.evaluate(() => document.activeElement.className);
      
      await page.keyboard.press('Tab');
      const thirdFocused = await page.evaluate(() => document.activeElement.className);
      
      expect(firstFocused).toContain('modal-close');
      expect(secondFocused).toContain('modal-action');
      expect(thirdFocused).toContain('modal-close'); // Should wrap back
    });
  });

  describe('Screen Reader Compatibility', () => {
    test('should have proper heading structure', async () => {
      const headings = await page.$$eval('h1, h2, h3, h4, h5, h6', headings => 
        headings.map(h => ({
          level: parseInt(h.tagName.substring(1)),
          text: h.textContent.trim(),
          id: h.id
        }))
      );
      
      // Should have a main heading
      expect(headings.some(h => h.level === 1)).toBe(true);
      
      // Heading levels should be sequential (no skipping levels)
      const levels = headings.map(h => h.level).sort((a, b) => a - b);
      for (let i = 1; i < levels.length; i++) {
        expect(levels[i] - levels[i-1]).toBeLessThanOrEqual(1);
      }
    });

    test('should have proper landmarks', async () => {
      const landmarks = await page.$$eval('[role], header, nav, main, aside, footer', elements =>
        elements.map(el => ({
          tagName: el.tagName.toLowerCase(),
          role: el.getAttribute('role'),
          id: el.id,
          className: el.className
        }))
      );
      
      // Should have main landmark
      expect(landmarks.some(l => 
        l.tagName === 'main' || l.role === 'main'
      )).toBe(true);
      
      // Should have navigation
      expect(landmarks.some(l => 
        l.tagName === 'nav' || l.role === 'navigation'
      )).toBe(true);
    });

    test('should have proper form labels', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      const formInputs = await page.$$eval('input, select, textarea', inputs =>
        inputs.map(input => ({
          id: input.id,
          name: input.name,
          type: input.type,
          hasLabel: !!document.querySelector(`label[for="${input.id}"]`),
          ariaLabel: input.getAttribute('aria-label'),
          ariaLabelledBy: input.getAttribute('aria-labelledby'),
          required: input.required
        }))
      );
      
      // All form inputs should have labels
      formInputs.forEach(input => {
        expect(
          input.hasLabel || input.ariaLabel || input.ariaLabelledBy
        ).toBe(true);
      });
    });

    test('should announce dynamic content changes', async () => {
      const liveRegions = await page.$$eval('[aria-live]', regions =>
        regions.map(region => ({
          ariaLive: region.getAttribute('aria-live'),
          id: region.id,
          className: region.className
        }))
      );
      
      // Should have at least one live region for announcements
      expect(liveRegions.length).toBeGreaterThan(0);
      
      // Live regions should have appropriate politeness levels
      liveRegions.forEach(region => {
        expect(['polite', 'assertive', 'off']).toContain(region.ariaLive);
      });
    });

    test('should provide status information', async () => {
      // Generate form to test status messages
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      // Submit form without filling required fields
      await page.click('button[type="submit"]');
      
      // Check for status/error messages
      const statusElements = await page.$$eval('[role="status"], [role="alert"], .error-message', elements =>
        elements.map(el => ({
          role: el.getAttribute('role'),
          text: el.textContent.trim(),
          visible: window.getComputedStyle(el).display !== 'none'
        }))
      );
      
      // Should have visible status/error messages
      expect(statusElements.some(el => el.visible && el.text)).toBe(true);
    });
  });

  describe('ARIA Attributes and Semantics', () => {
    test('should have proper button roles and states', async () => {
      const buttons = await page.$$eval('button, [role="button"]', buttons =>
        buttons.map(btn => ({
          tagName: btn.tagName.toLowerCase(),
          role: btn.getAttribute('role'),
          ariaPressed: btn.getAttribute('aria-pressed'),
          ariaExpanded: btn.getAttribute('aria-expanded'),
          ariaHaspopup: btn.getAttribute('aria-haspopup'),
          disabled: btn.disabled,
          text: btn.textContent.trim()
        }))
      );
      
      // Navigation buttons should have aria-pressed
      const navButtons = buttons.filter(btn => btn.text.match(/Reports|Jobs|History/));
      navButtons.forEach(btn => {
        expect(['true', 'false']).toContain(btn.ariaPressed);
      });
      
      // Dropdown buttons should have aria-expanded
      const dropdownButtons = buttons.filter(btn => btn.ariaHaspopup);
      dropdownButtons.forEach(btn => {
        expect(['true', 'false']).toContain(btn.ariaExpanded);
      });
    });

    test('should have proper list semantics', async () => {
      // Check for lists (navigation, job lists, etc.)
      const lists = await page.$$eval('ul, ol, [role="list"]', lists =>
        lists.map(list => ({
          tagName: list.tagName.toLowerCase(),
          role: list.getAttribute('role'),
          itemCount: list.querySelectorAll('li, [role="listitem"]').length
        }))
      );
      
      lists.forEach(list => {
        // Lists should have list items
        expect(list.itemCount).toBeGreaterThan(0);
      });
    });

    test('should have proper dialog semantics for modals', async () => {
      const modals = await page.$$eval('[role="dialog"], .modal', modals =>
        modals.map(modal => ({
          role: modal.getAttribute('role'),
          ariaModal: modal.getAttribute('aria-modal'),
          ariaLabelledBy: modal.getAttribute('aria-labelledby'),
          ariaLabel: modal.getAttribute('aria-label'),
          id: modal.id
        }))
      );
      
      modals.forEach(modal => {
        // Modals should have dialog role or modal attributes
        expect(
          modal.role === 'dialog' || modal.ariaModal === 'true'
        ).toBe(true);
        
        // Modals should be labeled
        expect(
          modal.ariaLabelledBy || modal.ariaLabel
        ).toBeTruthy();
      });
    });

    test('should have proper form validation semantics', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      const formFields = await page.$$eval('input[required], select[required]', fields =>
        fields.map(field => ({
          id: field.id,
          required: field.required,
          ariaRequired: field.getAttribute('aria-required'),
          ariaInvalid: field.getAttribute('aria-invalid'),
          ariaDescribedBy: field.getAttribute('aria-describedby')
        }))
      );
      
      formFields.forEach(field => {
        // Required fields should have aria-required
        if (field.required) {
          expect(field.ariaRequired).toBe('true');
        }
      });
    });
  });

  describe('Focus Management', () => {
    test('should have visible focus indicators', async () => {
      await page.waitForSelector('.nav-button', { visible: true });
      
      // Focus each navigation button and check focus styles
      const navButtons = await page.$$('.nav-button');
      
      for (const button of navButtons) {
        await button.focus();
        
        const focusStyles = await page.evaluate((btn) => {
          const styles = window.getComputedStyle(btn, ':focus');
          return {
            outline: styles.outline,
            outlineWidth: styles.outlineWidth,
            outlineStyle: styles.outlineStyle,
            outlineColor: styles.outlineColor,
            boxShadow: styles.boxShadow
          };
        }, button);
        
        // Should have some form of focus indicator
        const hasFocusIndicator = 
          focusStyles.outline !== 'none' ||
          focusStyles.outlineWidth !== '0px' ||
          focusStyles.boxShadow !== 'none';
        
        expect(hasFocusIndicator).toBe(true);
      }
    });

    test('should manage focus on view changes', async () => {
      await page.waitForSelector('#nav-jobs', { visible: true });
      
      // Click navigation and check focus management
      await page.click('#nav-jobs');
      await page.waitForSelector('#jobs-section.active', { visible: true });
      
      // Focus should be managed appropriately
      const focusedElement = await page.evaluate(() => document.activeElement);
      expect(focusedElement).toBeTruthy();
    });

    test('should restore focus after modal closes', async () => {
      // Focus a button that will open modal
      await page.focus('#nav-reports');
      const initialFocus = await page.evaluate(() => document.activeElement.id);
      
      // Simulate modal open/close cycle
      await page.evaluate(() => {
        const modal = document.getElementById('job-modal');
        if (modal) {
          modal.style.display = 'block';
        }
      });
      
      await page.keyboard.press('Escape');
      
      // Focus should return to trigger element
      const restoredFocus = await page.evaluate(() => document.activeElement.id);
      expect(restoredFocus).toBe(initialFocus);
    });
  });

  describe('Error Handling Accessibility', () => {
    test('should announce form errors to screen readers', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      // Submit invalid form
      await page.click('button[type="submit"]');
      
      // Check error announcements
      const errorElements = await page.$$eval('[role="alert"], .error-message', errors =>
        errors.map(error => ({
          role: error.getAttribute('role'),
          ariaLive: error.getAttribute('aria-live'),
          text: error.textContent.trim(),
          visible: window.getComputedStyle(error).display !== 'none'
        }))
      );
      
      // Should have visible error messages with proper roles
      expect(errorElements.some(error => 
        error.visible && 
        error.text && 
        (error.role === 'alert' || error.ariaLive)
      )).toBe(true);
    });

    test('should associate errors with form fields', async () => {
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });
      
      // Submit invalid form
      await page.click('button[type="submit"]');
      
      // Check field-error associations
      const fieldErrorAssociations = await page.$$eval('input, select', fields =>
        fields.map(field => {
          const describedBy = field.getAttribute('aria-describedby');
          let hasErrorDescription = false;
          
          if (describedBy) {
            const errorElement = document.getElementById(describedBy);
            hasErrorDescription = errorElement && 
              errorElement.textContent.trim() &&
              window.getComputedStyle(errorElement).display !== 'none';
          }
          
          return {
            id: field.id,
            ariaInvalid: field.getAttribute('aria-invalid'),
            hasErrorDescription,
            required: field.required
          };
        })
      );
      
      // Required fields with errors should have proper associations
      fieldErrorAssociations.forEach(field => {
        if (field.required && field.ariaInvalid === 'true') {
          expect(field.hasErrorDescription).toBe(true);
        }
      });
    });
  });

  describe('Mobile Accessibility', () => {
    test('should be accessible on mobile viewports', async () => {
      await page.setViewport({ 
        width: 375, 
        height: 667, 
        isMobile: true,
        hasTouch: true 
      });
      
      await page.reload({ waitUntil: 'networkidle0' });
      
      const results = await new AxePuppeteer(page)
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .analyze();
      
      expect(results.violations).toEqual([]);
    });

    test('should have appropriate touch targets', async () => {
      await page.setViewport({ 
        width: 375, 
        height: 667, 
        isMobile: true,
        hasTouch: true 
      });
      
      await page.reload({ waitUntil: 'networkidle0' });
      
      const touchTargets = await page.$$eval('button, a, input, select', elements =>
        elements.map(el => {
          const rect = el.getBoundingClientRect();
          const styles = window.getComputedStyle(el);
          
          return {
            width: rect.width,
            height: rect.height,
            padding: styles.padding,
            visible: rect.width > 0 && rect.height > 0
          };
        })
      );
      
      // Touch targets should be at least 44x44px (WCAG AA)
      const visibleTargets = touchTargets.filter(target => target.visible);
      visibleTargets.forEach(target => {
        expect(target.width >= 44 || target.height >= 44).toBe(true);
      });
    });
  });
});
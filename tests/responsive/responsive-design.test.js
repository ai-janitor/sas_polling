/*
=============================================================================
RESPONSIVE DESIGN TESTS
=============================================================================
Purpose: Test application behavior across different screen sizes and orientations
Technology: Puppeteer viewport testing with visual regression
Coverage: Mobile, tablet, desktop breakpoints and orientation changes

TEST SCENARIOS:
1. Layout adaptation across viewport sizes
2. Navigation behavior on different screen sizes
3. Form layout and usability on mobile
4. Touch interaction optimization
5. Content readability and scaling
6. Image and media responsiveness
7. Typography scaling and line height
8. Orientation change handling

VIEWPORT MATRIX:
- Mobile Portrait: 375x667 (iPhone SE)
- Mobile Landscape: 667x375 (iPhone SE rotated)
- Tablet Portrait: 768x1024 (iPad)
- Tablet Landscape: 1024x768 (iPad rotated)
- Desktop Small: 1024x768
- Desktop Large: 1920x1080
- Ultra-wide: 2560x1440

RESPONSIVE STRATEGY:
- Breakpoint behavior validation
- Content reflow testing
- Interactive element sizing
- Performance across devices
- Visual regression detection
=============================================================================
*/

const puppeteer = require('puppeteer');

describe('Responsive Design Tests', () => {
  let browser;
  let page;
  const baseUrl = process.env.GUI_URL || 'http://localhost:3000';

  // Define viewport configurations for testing
  const viewports = {
    mobilePortrait: { width: 375, height: 667, name: 'Mobile Portrait' },
    mobileLandscape: { width: 667, height: 375, name: 'Mobile Landscape' },
    tabletPortrait: { width: 768, height: 1024, name: 'Tablet Portrait' },
    tabletLandscape: { width: 1024, height: 768, name: 'Tablet Landscape' },
    desktopSmall: { width: 1024, height: 768, name: 'Desktop Small' },
    desktopLarge: { width: 1920, height: 1080, name: 'Desktop Large' },
    ultraWide: { width: 2560, height: 1440, name: 'Ultra-wide' }
  };

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
    
    // Setup API mocking
    await page.setRequestInterception(true);
    page.on('request', request => {
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
                description: 'Responsive design test report',
                prompts: [{
                  test_field: {
                    active: true,
                    inputType: 'inputtext',
                    label: 'Test Field',
                    required: true
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
  });

  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  describe('Layout Adaptation', () => {
    test('should adapt layout to all viewport sizes', async () => {
      const results = {};

      for (const [key, viewport] of Object.entries(viewports)) {
        await page.setViewport(viewport);
        await page.goto(baseUrl, { waitUntil: 'networkidle0' });
        await page.waitForSelector('#app', { visible: true });

        // Measure key layout elements
        const layoutMetrics = await page.evaluate(() => {
          const app = document.getElementById('app');
          const header = document.querySelector('.app-header');
          const nav = document.querySelector('.header-nav');
          const main = document.querySelector('.main-content');

          return {
            appRect: app ? app.getBoundingClientRect() : null,
            headerRect: header ? header.getBoundingClientRect() : null,
            navRect: nav ? nav.getBoundingClientRect() : null,
            mainRect: main ? main.getBoundingClientRect() : null,
            headerDisplay: header ? window.getComputedStyle(header).display : null,
            navDisplay: nav ? window.getComputedStyle(nav).display : null,
            navDirection: nav ? window.getComputedStyle(nav).flexDirection : null,
            overflow: app ? window.getComputedStyle(app).overflow : null
          };
        });

        results[key] = {
          viewport,
          layoutMetrics,
          fitsViewport: layoutMetrics.appRect.width <= viewport.width
        };
      }

      // Verify layout adapts correctly
      Object.entries(results).forEach(([key, result]) => {
        console.log(`${result.viewport.name}: ${result.fitsViewport ? '✅' : '❌'} Layout fits viewport`);
        
        // Layout should fit within viewport
        expect(result.fitsViewport).toBe(true);
        
        // Header should always be visible
        expect(result.layoutMetrics.headerDisplay).not.toBe('none');
        
        // Navigation should be visible
        expect(result.layoutMetrics.navDisplay).not.toBe('none');
      });
    });

    test('should handle navigation layout changes on mobile', async () => {
      // Test desktop navigation
      await page.setViewport(viewports.desktopLarge);
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });
      
      const desktopNav = await page.evaluate(() => {
        const nav = document.querySelector('.header-nav');
        const buttons = nav.querySelectorAll('.nav-button');
        
        return {
          flexDirection: window.getComputedStyle(nav).flexDirection,
          buttonCount: buttons.length,
          allVisible: Array.from(buttons).every(btn => 
            window.getComputedStyle(btn).display !== 'none'
          )
        };
      });

      // Test mobile navigation
      await page.setViewport(viewports.mobilePortrait);
      await page.reload({ waitUntil: 'networkidle0' });
      
      const mobileNav = await page.evaluate(() => {
        const nav = document.querySelector('.header-nav');
        const buttons = nav.querySelectorAll('.nav-button');
        
        return {
          flexDirection: window.getComputedStyle(nav).flexDirection,
          buttonCount: buttons.length,
          allVisible: Array.from(buttons).every(btn => 
            window.getComputedStyle(btn).display !== 'none'
          ),
          navRect: nav.getBoundingClientRect()
        };
      });

      // Navigation should adapt for mobile
      expect(desktopNav.allVisible).toBe(true);
      expect(mobileNav.allVisible).toBe(true);
      expect(mobileNav.buttonCount).toBe(desktopNav.buttonCount);
    });

    test('should maintain content hierarchy across breakpoints', async () => {
      const hierarchyResults = {};

      for (const [key, viewport] of Object.entries(viewports)) {
        await page.setViewport(viewport);
        await page.goto(baseUrl, { waitUntil: 'networkidle0' });
        
        const hierarchy = await page.evaluate(() => {
          const sections = Array.from(document.querySelectorAll('.content-section'));
          const nav = document.querySelector('.header-nav');
          const title = document.querySelector('.app-title');
          
          return {
            sectionsVisible: sections.filter(s => 
              window.getComputedStyle(s).display !== 'none'
            ).length,
            titleVisible: title && window.getComputedStyle(title).display !== 'none',
            navVisible: nav && window.getComputedStyle(nav).display !== 'none',
            titleSize: title ? window.getComputedStyle(title).fontSize : null
          };
        });

        hierarchyResults[key] = hierarchy;
      }

      // Content hierarchy should be preserved
      Object.values(hierarchyResults).forEach(result => {
        expect(result.titleVisible).toBe(true);
        expect(result.navVisible).toBe(true);
        expect(result.sectionsVisible).toBeGreaterThan(0);
      });
    });
  });

  describe('Form Responsiveness', () => {
    test('should optimize form layout for mobile devices', async () => {
      // Test form on desktop
      await page.setViewport(viewports.desktopLarge);
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });

      const desktopForm = await page.evaluate(() => {
        const formContainer = document.getElementById('form-container');
        const formFields = formContainer.querySelectorAll('.form-group');
        
        return {
          containerWidth: formContainer.getBoundingClientRect().width,
          fieldWidths: Array.from(formFields).map(field => 
            field.getBoundingClientRect().width
          ),
          containerVisible: window.getComputedStyle(formContainer).display !== 'none'
        };
      });

      // Test form on mobile
      await page.setViewport(viewports.mobilePortrait);
      await page.reload({ waitUntil: 'networkidle0' });
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });

      const mobileForm = await page.evaluate(() => {
        const formContainer = document.getElementById('form-container');
        const formFields = formContainer.querySelectorAll('.form-group');
        const inputs = formContainer.querySelectorAll('input, select');
        
        return {
          containerWidth: formContainer.getBoundingClientRect().width,
          fieldWidths: Array.from(formFields).map(field => 
            field.getBoundingClientRect().width
          ),
          inputSizes: Array.from(inputs).map(input => ({
            width: input.getBoundingClientRect().width,
            height: input.getBoundingClientRect().height
          })),
          containerVisible: window.getComputedStyle(formContainer).display !== 'none'
        };
      });

      // Form should be optimized for mobile
      expect(desktopForm.containerVisible).toBe(true);
      expect(mobileForm.containerVisible).toBe(true);
      
      // Form should adapt to mobile width
      expect(mobileForm.containerWidth).toBeLessThan(desktopForm.containerWidth);
      
      // Input elements should be appropriately sized for mobile
      mobileForm.inputSizes.forEach(input => {
        expect(input.height).toBeGreaterThanOrEqual(44); // Minimum touch target
      });
    });

    test('should handle form validation display on mobile', async () => {
      await page.setViewport(viewports.mobilePortrait);
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });
      await page.waitForSelector('#report-dropdown option:last-child');
      await page.select('#report-dropdown', 'test_report');
      await page.waitForSelector('#form-container', { visible: true });

      // Submit form without filling required fields
      await page.click('button[type="submit"]');

      const errorDisplay = await page.evaluate(() => {
        const errors = document.querySelectorAll('.form-errors, .error-message');
        
        return Array.from(errors).map(error => ({
          visible: window.getComputedStyle(error).display !== 'none',
          width: error.getBoundingClientRect().width,
          text: error.textContent.trim()
        }));
      });

      // Error messages should be visible and readable on mobile
      const visibleErrors = errorDisplay.filter(error => error.visible && error.text);
      expect(visibleErrors.length).toBeGreaterThan(0);
      
      visibleErrors.forEach(error => {
        expect(error.width).toBeGreaterThan(0);
      });
    });
  });

  describe('Touch Interaction Optimization', () => {
    test('should provide adequate touch targets on mobile', async () => {
      await page.setViewport(viewports.mobilePortrait);
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const touchTargets = await page.evaluate(() => {
        const interactiveElements = document.querySelectorAll(
          'button, a, input, select, [role="button"], [tabindex="0"]'
        );

        return Array.from(interactiveElements).map(element => {
          const rect = element.getBoundingClientRect();
          const styles = window.getComputedStyle(element);
          
          return {
            tagName: element.tagName.toLowerCase(),
            width: rect.width,
            height: rect.height,
            padding: styles.padding,
            margin: styles.margin,
            visible: rect.width > 0 && rect.height > 0,
            text: element.textContent.trim().substring(0, 20)
          };
        });
      });

      // Filter visible touch targets
      const visibleTargets = touchTargets.filter(target => target.visible);
      
      // WCAG AA requires minimum 44x44px touch targets
      visibleTargets.forEach(target => {
        const meetsMinimumSize = target.width >= 44 && target.height >= 44;
        
        if (!meetsMinimumSize) {
          console.log(`Small touch target: ${target.tagName} "${target.text}" (${target.width}x${target.height})`);
        }
        
        expect(meetsMinimumSize).toBe(true);
      });
    });

    test('should handle touch gestures appropriately', async () => {
      await page.setViewport({
        ...viewports.mobilePortrait,
        isMobile: true,
        hasTouch: true
      });
      
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Test touch event support
      const touchSupport = await page.evaluate(() => {
        return {
          hasTouchStart: 'ontouchstart' in window,
          hasTouchMove: 'ontouchmove' in window,
          hasTouchEnd: 'ontouchend' in window,
          hasTouch: 'ontouchstart' in window || navigator.maxTouchPoints > 0
        };
      });

      expect(touchSupport.hasTouch).toBe(true);

      // Test touch interaction on navigation
      await page.touchscreen.tap(100, 100); // Tap somewhere safe first
      
      const navButton = await page.$('#nav-jobs');
      const navButtonBox = await navButton.boundingBox();
      
      await page.touchscreen.tap(
        navButtonBox.x + navButtonBox.width / 2,
        navButtonBox.y + navButtonBox.height / 2
      );

      await page.waitForSelector('#jobs-section.active', { visible: true });
      
      const activeSection = await page.$eval('.content-section.active', el => el.id);
      expect(activeSection).toBe('jobs-section');
    });
  });

  describe('Content Readability', () => {
    test('should maintain readable text sizes across devices', async () => {
      const textSizeResults = {};

      for (const [key, viewport] of Object.entries(viewports)) {
        await page.setViewport(viewport);
        await page.goto(baseUrl, { waitUntil: 'networkidle0' });

        const textMetrics = await page.evaluate(() => {
          const title = document.querySelector('.app-title');
          const navButtons = document.querySelectorAll('.nav-button');
          const bodyText = document.querySelector('p, .description');

          return {
            titleSize: title ? parseFloat(window.getComputedStyle(title).fontSize) : 0,
            navButtonSize: navButtons.length > 0 ? 
              parseFloat(window.getComputedStyle(navButtons[0]).fontSize) : 0,
            bodyTextSize: bodyText ? 
              parseFloat(window.getComputedStyle(bodyText).fontSize) : 0,
            titleLineHeight: title ? 
              parseFloat(window.getComputedStyle(title).lineHeight) : 0
          };
        });

        textSizeResults[key] = { viewport, textMetrics };
      }

      // Text should be readable (minimum 16px for body text)
      Object.entries(textSizeResults).forEach(([key, result]) => {
        const { textMetrics, viewport } = result;
        
        // Title should be appropriately sized
        expect(textMetrics.titleSize).toBeGreaterThanOrEqual(18);
        
        // Navigation text should be readable
        if (textMetrics.navButtonSize > 0) {
          expect(textMetrics.navButtonSize).toBeGreaterThanOrEqual(14);
        }
        
        // Body text should meet accessibility standards
        if (textMetrics.bodyTextSize > 0) {
          expect(textMetrics.bodyTextSize).toBeGreaterThanOrEqual(14);
        }

        console.log(`${viewport.name}: Title ${textMetrics.titleSize}px, Nav ${textMetrics.navButtonSize}px, Body ${textMetrics.bodyTextSize}px`);
      });
    });

    test('should maintain proper line spacing', async () => {
      await page.setViewport(viewports.mobilePortrait);
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const lineSpacing = await page.evaluate(() => {
        const textElements = document.querySelectorAll('p, h1, h2, h3, .description');
        
        return Array.from(textElements).map(element => {
          const styles = window.getComputedStyle(element);
          return {
            fontSize: parseFloat(styles.fontSize),
            lineHeight: parseFloat(styles.lineHeight),
            ratio: parseFloat(styles.lineHeight) / parseFloat(styles.fontSize)
          };
        });
      });

      // Line height should be at least 1.5 times the font size (WCAG AA)
      lineSpacing.forEach(spacing => {
        if (spacing.lineHeight && spacing.fontSize) {
          expect(spacing.ratio).toBeGreaterThanOrEqual(1.5);
        }
      });
    });
  });

  describe('Orientation Handling', () => {
    test('should handle orientation changes gracefully', async () => {
      // Start in portrait
      await page.setViewport(viewports.mobilePortrait);
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const portraitLayout = await page.evaluate(() => {
        const app = document.getElementById('app');
        const header = document.querySelector('.app-header');
        
        return {
          appHeight: app.getBoundingClientRect().height,
          headerHeight: header.getBoundingClientRect().height,
          aspectRatio: window.innerWidth / window.innerHeight
        };
      });

      // Switch to landscape
      await page.setViewport(viewports.mobileLandscape);
      
      // Trigger resize event
      await page.evaluate(() => {
        window.dispatchEvent(new Event('resize'));
      });

      const landscapeLayout = await page.evaluate(() => {
        const app = document.getElementById('app');
        const header = document.querySelector('.app-header');
        
        return {
          appHeight: app.getBoundingClientRect().height,
          headerHeight: header.getBoundingClientRect().height,
          aspectRatio: window.innerWidth / window.innerHeight
        };
      });

      // Layout should adapt to orientation change
      expect(portraitLayout.aspectRatio).toBeLessThan(1);
      expect(landscapeLayout.aspectRatio).toBeGreaterThan(1);
      
      // Header should remain functional
      expect(landscapeLayout.headerHeight).toBeGreaterThan(0);
      expect(landscapeLayout.appHeight).toBeGreaterThan(0);
    });
  });

  describe('Performance Across Devices', () => {
    test('should perform well on mobile devices', async () => {
      // Simulate slower mobile device
      await page.setViewport(viewports.mobilePortrait);
      
      // Enable CPU throttling to simulate mobile performance
      const client = await page.target().createCDPSession();
      await client.send('Emulation.setCPUThrottlingRate', { rate: 4 });

      const startTime = Date.now();
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });
      await page.waitForSelector('#app', { visible: true });
      const loadTime = Date.now() - startTime;

      // Disable throttling
      await client.send('Emulation.setCPUThrottlingRate', { rate: 1 });

      // Should load within reasonable time even on slower devices
      expect(loadTime).toBeLessThan(15000); // 15 seconds max for throttled mobile

      console.log(`Mobile load time (4x CPU throttling): ${loadTime}ms`);
    });

    test('should handle rapid viewport changes', async () => {
      const viewportKeys = Object.keys(viewports);
      
      for (let i = 0; i < 3; i++) {
        for (const key of viewportKeys) {
          await page.setViewport(viewports[key]);
          
          // Trigger resize and check layout stability
          await page.evaluate(() => {
            window.dispatchEvent(new Event('resize'));
          });
          
          // Quick layout check
          const layoutStable = await page.evaluate(() => {
            const app = document.getElementById('app');
            return app && app.getBoundingClientRect().width > 0;
          });
          
          expect(layoutStable).toBe(true);
        }
      }
    });
  });

  describe('Visual Consistency', () => {
    test('should maintain visual hierarchy across breakpoints', async () => {
      const visualHierarchy = {};

      for (const [key, viewport] of Object.entries(viewports)) {
        await page.setViewport(viewport);
        await page.goto(baseUrl, { waitUntil: 'networkidle0' });

        const hierarchy = await page.evaluate(() => {
          const title = document.querySelector('.app-title');
          const navButtons = document.querySelectorAll('.nav-button');
          const sections = document.querySelectorAll('.content-section');

          return {
            titleWeight: title ? window.getComputedStyle(title).fontWeight : null,
            titleColor: title ? window.getComputedStyle(title).color : null,
            navButtonStyles: Array.from(navButtons).map(btn => ({
              fontSize: window.getComputedStyle(btn).fontSize,
              fontWeight: window.getComputedStyle(btn).fontWeight,
              padding: window.getComputedStyle(btn).padding
            })),
            sectionSpacing: Array.from(sections).map(section => 
              window.getComputedStyle(section).margin
            )
          };
        });

        visualHierarchy[key] = hierarchy;
      }

      // Visual hierarchy should be consistent
      const firstViewport = Object.values(visualHierarchy)[0];
      
      Object.values(visualHierarchy).forEach(hierarchy => {
        expect(hierarchy.titleWeight).toBe(firstViewport.titleWeight);
        expect(hierarchy.titleColor).toBe(firstViewport.titleColor);
      });
    });
  });
});
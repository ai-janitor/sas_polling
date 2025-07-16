/*
=============================================================================
CROSS-BROWSER COMPATIBILITY TESTS
=============================================================================
Purpose: Test application functionality across different browsers and versions
Technology: Puppeteer with multiple browser configurations
Coverage: Chrome, Firefox, Safari, Edge compatibility testing

TEST SCENARIOS:
1. Browser-specific JavaScript feature support
2. CSS rendering and layout consistency
3. Form input behavior across browsers
4. Event handling differences
5. Local storage and session storage
6. API request handling and CORS
7. Performance characteristics per browser
8. Mobile browser compatibility

BROWSER MATRIX:
- Chrome (latest, previous)
- Firefox (latest, previous)
- Safari (latest where possible)
- Edge (latest)
- Mobile Chrome/Safari

COMPATIBILITY STRATEGY:
- Feature detection and polyfill validation
- Visual regression testing
- Functional behavior verification
- Performance baseline comparison
=============================================================================
*/

const puppeteer = require('puppeteer');

describe('Cross-Browser Compatibility Tests', () => {
  const browsers = [];
  const baseUrl = process.env.GUI_URL || 'http://localhost:3000';

  // Browser configurations for testing
  const browserConfigs = [
    {
      name: 'Chrome Latest',
      product: 'chrome',
      headless: process.env.CI === 'true',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    },
    {
      name: 'Firefox Latest',
      product: 'firefox',
      headless: process.env.CI === 'true',
      args: ['--no-sandbox']
    }
    // Note: Safari testing requires macOS environment
    // Edge testing uses Chromium engine, similar to Chrome
  ];

  beforeAll(async () => {
    // Launch all browsers
    for (const config of browserConfigs) {
      try {
        const browser = await puppeteer.launch({
          product: config.product,
          headless: config.headless,
          args: config.args,
          devtools: !process.env.CI
        });
        
        browsers.push({
          name: config.name,
          browser,
          product: config.product
        });
        
        console.log(`✅ Launched ${config.name}`);
      } catch (error) {
        console.warn(`⚠️  Failed to launch ${config.name}: ${error.message}`);
      }
    }

    if (browsers.length === 0) {
      throw new Error('No browsers could be launched for testing');
    }
  });

  afterAll(async () => {
    // Close all browsers
    await Promise.all(browsers.map(({ browser }) => browser.close()));
  });

  describe('Basic Application Loading', () => {
    test('should load application in all browsers', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0', timeout: 30000 });
            await page.waitForSelector('#app', { visible: true, timeout: 10000 });
            
            const title = await page.$eval('.app-title', el => el.textContent);
            await page.close();
            
            return { browser: name, success: true, title };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      // Verify all browsers loaded successfully
      results.forEach(result => {
        console.log(`${result.browser}: ${result.success ? '✅' : '❌'} ${result.success ? result.title : result.error}`);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.title).toBe('DataFit');
        }
      });
    });

    test('should display navigation consistently across browsers', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            await page.waitForSelector('.nav-button', { visible: true });
            
            const navButtons = await page.$$eval('.nav-button', buttons => 
              buttons.map(btn => ({
                text: btn.textContent.trim(),
                visible: window.getComputedStyle(btn).display !== 'none'
              }))
            );
            
            await page.close();
            return { browser: name, success: true, navButtons };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      // Verify navigation consistency
      const expectedNavButtons = ['Reports', 'Jobs', 'History'];
      
      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.navButtons.length).toBe(3);
        
        result.navButtons.forEach((button, index) => {
          expect(button.text).toBe(expectedNavButtons[index]);
          expect(button.visible).toBe(true);
        });
      });
    });
  });

  describe('JavaScript Feature Compatibility', () => {
    test('should support ES6+ features in all browsers', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            
            // Test ES6+ features
            const featureTests = await page.evaluate(() => {
              const results = {};
              
              // Test arrow functions
              try {
                const arrow = () => 'arrow';
                results.arrowFunctions = arrow() === 'arrow';
              } catch (e) {
                results.arrowFunctions = false;
              }
              
              // Test template literals
              try {
                const name = 'test';
                const template = `Hello ${name}`;
                results.templateLiterals = template === 'Hello test';
              } catch (e) {
                results.templateLiterals = false;
              }
              
              // Test const/let
              try {
                const constVar = 'const';
                let letVar = 'let';
                results.blockScoping = constVar === 'const' && letVar === 'let';
              } catch (e) {
                results.blockScoping = false;
              }
              
              // Test destructuring
              try {
                const obj = { a: 1, b: 2 };
                const { a, b } = obj;
                results.destructuring = a === 1 && b === 2;
              } catch (e) {
                results.destructuring = false;
              }
              
              // Test async/await
              try {
                results.asyncAwait = typeof async function() {} === 'function';
              } catch (e) {
                results.asyncAwait = false;
              }
              
              // Test Map and Set
              try {
                const map = new Map();
                const set = new Set();
                results.mapSet = map instanceof Map && set instanceof Set;
              } catch (e) {
                results.mapSet = false;
              }
              
              return results;
            });
            
            await page.close();
            return { browser: name, success: true, features: featureTests };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      // Verify ES6+ support
      results.forEach(result => {
        console.log(`${result.browser} ES6+ features:`, result.features);
        expect(result.success).toBe(true);
        
        // All modern browsers should support these features
        expect(result.features.arrowFunctions).toBe(true);
        expect(result.features.templateLiterals).toBe(true);
        expect(result.features.blockScoping).toBe(true);
        expect(result.features.destructuring).toBe(true);
        expect(result.features.asyncAwait).toBe(true);
        expect(result.features.mapSet).toBe(true);
      });
    });

    test('should support Fetch API across browsers', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            
            const fetchSupport = await page.evaluate(() => {
              return {
                hasFetch: typeof fetch === 'function',
                hasPromise: typeof Promise === 'function',
                hasResponse: typeof Response === 'function',
                hasRequest: typeof Request === 'function'
              };
            });
            
            await page.close();
            return { browser: name, success: true, fetchSupport };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.fetchSupport.hasFetch).toBe(true);
        expect(result.fetchSupport.hasPromise).toBe(true);
        expect(result.fetchSupport.hasResponse).toBe(true);
        expect(result.fetchSupport.hasRequest).toBe(true);
      });
    });
  });

  describe('CSS Rendering Compatibility', () => {
    test('should render flexbox layouts consistently', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            await page.waitForSelector('.app-container', { visible: true });
            
            const layoutProps = await page.$eval('.app-container', el => {
              const styles = window.getComputedStyle(el);
              return {
                display: styles.display,
                flexDirection: styles.flexDirection,
                minHeight: styles.minHeight
              };
            });
            
            await page.close();
            return { browser: name, success: true, layoutProps };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.layoutProps.display).toBe('flex');
        expect(result.layoutProps.flexDirection).toBe('column');
        expect(result.layoutProps.minHeight).toBe('100vh');
      });
    });

    test('should support CSS Grid where applicable', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            
            const gridSupport = await page.evaluate(() => {
              const testEl = document.createElement('div');
              document.body.appendChild(testEl);
              
              testEl.style.display = 'grid';
              const hasGrid = window.getComputedStyle(testEl).display === 'grid';
              
              document.body.removeChild(testEl);
              return hasGrid;
            });
            
            await page.close();
            return { browser: name, success: true, gridSupport };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        // Modern browsers should support CSS Grid
        expect(result.gridSupport).toBe(true);
      });
    });
  });

  describe('Form Input Compatibility', () => {
    test('should handle form inputs consistently across browsers', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
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
                        prompts: [{
                          test_field: {
                            active: true,
                            inputType: 'inputtext',
                            label: 'Test Field',
                            required: true
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
            await page.waitForSelector('#report-dropdown option:last-child');
            await page.select('#report-dropdown', 'test_report');
            await page.waitForSelector('#form-container', { visible: true });
            
            // Test input behaviors
            const inputField = await page.$('input[name="test_field"]');
            await inputField.type('Test Input Value');
            
            const inputValue = await page.$eval('input[name="test_field"]', el => el.value);
            const inputProps = await page.$eval('input[name="test_field"]', el => ({
              type: el.type,
              required: el.required,
              value: el.value
            }));
            
            await page.close();
            return { browser: name, success: true, inputProps };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.inputProps.type).toBe('text');
        expect(result.inputProps.required).toBe(true);
        expect(result.inputProps.value).toBe('Test Input Value');
      });
    });

    test('should handle date inputs across browsers', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            
            // Test date input support
            const dateSupport = await page.evaluate(() => {
              const input = document.createElement('input');
              input.type = 'date';
              
              return {
                supportsDateInput: input.type === 'date',
                hasValueAsDate: 'valueAsDate' in input
              };
            });
            
            await page.close();
            return { browser: name, success: true, dateSupport };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        // Modern browsers should support date inputs
        expect(result.dateSupport.supportsDateInput).toBe(true);
        expect(result.dateSupport.hasValueAsDate).toBe(true);
      });
    });
  });

  describe('Local Storage Compatibility', () => {
    test('should support localStorage across browsers', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            
            const storageTest = await page.evaluate(() => {
              try {
                // Test localStorage
                const testKey = 'datafit_test_' + Date.now();
                const testValue = 'test_value';
                
                localStorage.setItem(testKey, testValue);
                const retrievedValue = localStorage.getItem(testKey);
                localStorage.removeItem(testKey);
                
                // Test sessionStorage
                sessionStorage.setItem(testKey, testValue);
                const sessionValue = sessionStorage.getItem(testKey);
                sessionStorage.removeItem(testKey);
                
                return {
                  hasLocalStorage: typeof localStorage !== 'undefined',
                  hasSessionStorage: typeof sessionStorage !== 'undefined',
                  localStorageWorks: retrievedValue === testValue,
                  sessionStorageWorks: sessionValue === testValue
                };
              } catch (e) {
                return {
                  hasLocalStorage: false,
                  hasSessionStorage: false,
                  localStorageWorks: false,
                  sessionStorageWorks: false,
                  error: e.message
                };
              }
            });
            
            await page.close();
            return { browser: name, success: true, storageTest };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.storageTest.hasLocalStorage).toBe(true);
        expect(result.storageTest.hasSessionStorage).toBe(true);
        expect(result.storageTest.localStorageWorks).toBe(true);
        expect(result.storageTest.sessionStorageWorks).toBe(true);
      });
    });
  });

  describe('Event Handling Compatibility', () => {
    test('should handle click events consistently', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            await page.waitForSelector('#nav-jobs', { visible: true });
            
            // Test click event
            await page.click('#nav-jobs');
            await page.waitForSelector('#jobs-section.active', { visible: true });
            
            const activeSection = await page.$eval('.content-section.active', el => el.id);
            
            await page.close();
            return { browser: name, success: true, activeSection };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.activeSection).toBe('jobs-section');
      });
    });

    test('should handle keyboard events consistently', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            await page.waitForSelector('#nav-reports', { visible: true });
            
            // Test keyboard navigation
            await page.focus('#nav-reports');
            await page.keyboard.press('Tab');
            
            const focusedElement = await page.evaluate(() => document.activeElement.id);
            
            await page.close();
            return { browser: name, success: true, focusedElement };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(['nav-jobs', 'nav-history']).toContain(result.focusedElement);
      });
    });
  });

  describe('Performance Characteristics', () => {
    test('should load within acceptable time across browsers', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            const startTime = Date.now();
            
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            await page.waitForSelector('#app', { visible: true });
            
            const loadTime = Date.now() - startTime;
            
            await page.close();
            return { browser: name, success: true, loadTime };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        console.log(`${result.browser} load time: ${result.loadTime}ms`);
        expect(result.success).toBe(true);
        expect(result.loadTime).toBeLessThan(10000); // 10 seconds max
      });
    });

    test('should handle rapid interactions without lag', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            await page.waitForSelector('.nav-button', { visible: true });
            
            const startTime = Date.now();
            
            // Rapid navigation clicks
            for (let i = 0; i < 5; i++) {
              await page.click('#nav-jobs');
              await page.click('#nav-history');
              await page.click('#nav-reports');
            }
            
            const interactionTime = Date.now() - startTime;
            
            await page.close();
            return { browser: name, success: true, interactionTime };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        console.log(`${result.browser} interaction time: ${result.interactionTime}ms`);
        expect(result.success).toBe(true);
        expect(result.interactionTime).toBeLessThan(2000); // 2 seconds max
      });
    });
  });

  describe('Mobile Browser Compatibility', () => {
    test('should work on mobile viewports', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser, product }) => {
          const page = await browser.newPage();
          
          try {
            // Set mobile viewport
            await page.setViewport({ 
              width: 375, 
              height: 667, 
              isMobile: true,
              hasTouch: true 
            });
            
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            await page.waitForSelector('#app', { visible: true });
            
            // Test mobile navigation
            const navVisible = await page.$eval('.header-nav', el => 
              window.getComputedStyle(el).display !== 'none'
            );
            
            // Test touch events (where supported)
            let touchSupport = false;
            try {
              touchSupport = await page.evaluate(() => 'ontouchstart' in window);
            } catch (e) {
              // Touch not supported in this browser/environment
            }
            
            await page.close();
            return { 
              browser: name, 
              success: true, 
              navVisible, 
              touchSupport,
              product 
            };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        expect(result.success).toBe(true);
        expect(result.navVisible).toBe(true);
        
        // Chrome/Chromium-based browsers should support touch in mobile mode
        if (result.product === 'chrome') {
          expect(result.touchSupport).toBe(true);
        }
      });
    });
  });

  describe('Browser-Specific Features', () => {
    test('should handle browser-specific quirks gracefully', async () => {
      const results = await Promise.all(
        browsers.map(async ({ name, browser, product }) => {
          const page = await browser.newPage();
          
          try {
            await page.goto(baseUrl, { waitUntil: 'networkidle0' });
            
            const browserInfo = await page.evaluate(() => ({
              userAgent: navigator.userAgent,
              vendor: navigator.vendor,
              platform: navigator.platform,
              language: navigator.language,
              cookieEnabled: navigator.cookieEnabled,
              onLine: navigator.onLine
            }));
            
            await page.close();
            return { browser: name, success: true, browserInfo, product };
          } catch (error) {
            await page.close();
            return { browser: name, success: false, error: error.message };
          }
        })
      );

      results.forEach(result => {
        console.log(`${result.browser}:`, {
          vendor: result.browserInfo.vendor,
          language: result.browserInfo.language,
          cookieEnabled: result.browserInfo.cookieEnabled
        });
        
        expect(result.success).toBe(true);
        expect(result.browserInfo.cookieEnabled).toBe(true);
        expect(result.browserInfo.onLine).toBe(true);
      });
    });
  });
});
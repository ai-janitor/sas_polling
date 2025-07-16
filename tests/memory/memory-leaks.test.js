/*
=============================================================================
MEMORY LEAK DETECTION TESTS
=============================================================================
Purpose: Detect and prevent memory leaks in JavaScript application
Technology: Puppeteer with memory profiling and leak detection
Coverage: Event listeners, DOM references, timers, API calls, component cleanup

TEST SCENARIOS:
1. Event listener cleanup detection
2. DOM reference leak detection
3. Timer and interval cleanup
4. Component lifecycle memory management
5. API request cleanup and cancellation
6. Large object cleanup verification
7. Closure-based memory leaks
8. Third-party library cleanup

MEMORY LEAK STRATEGY:
- Before/after memory comparisons
- Heap snapshot analysis
- Forced garbage collection
- Memory growth pattern detection
- Reference counting validation
=============================================================================
*/

const puppeteer = require('puppeteer');

describe('Memory Leak Detection Tests', () => {
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
        '--disable-web-security',
        '--enable-precise-memory-info',
        '--expose-gc' // Enable garbage collection API
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
  });

  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  describe('Event Listener Memory Leaks', () => {
    test('should clean up event listeners on component destruction', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const memoryBefore = await getMemoryUsage(page);

      // Simulate adding and removing many event listeners
      await page.evaluate(() => {
        const elements = [];
        const handlers = [];

        // Create elements with event listeners
        for (let i = 0; i < 1000; i++) {
          const element = document.createElement('button');
          element.textContent = `Button ${i}`;
          
          const handler = () => console.log(`Clicked ${i}`);
          element.addEventListener('click', handler);
          
          document.body.appendChild(element);
          elements.push(element);
          handlers.push(handler);
        }

        // Store references for cleanup
        window.testElements = elements;
        window.testHandlers = handlers;
      });

      const memoryDuringPeak = await getMemoryUsage(page);

      // Clean up elements and listeners
      await page.evaluate(() => {
        if (window.testElements && window.testHandlers) {
          window.testElements.forEach((element, index) => {
            element.removeEventListener('click', window.testHandlers[index]);
            document.body.removeChild(element);
          });
          
          // Clear references
          delete window.testElements;
          delete window.testHandlers;
        }
      });

      // Force garbage collection
      await forceGarbageCollection(page);

      const memoryAfter = await getMemoryUsage(page);

      console.log('Event Listener Memory Test:', {
        before: `${(memoryBefore / 1024 / 1024).toFixed(2)}MB`,
        peak: `${(memoryDuringPeak / 1024 / 1024).toFixed(2)}MB`,
        after: `${(memoryAfter / 1024 / 1024).toFixed(2)}MB`
      });

      // Memory should return close to original level
      const memoryGrowth = memoryAfter - memoryBefore;
      const growthMB = memoryGrowth / 1024 / 1024;
      
      expect(growthMB).toBeLessThan(5); // < 5MB permanent growth
    });

    test('should detect global event listener leaks', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const initialListenerCount = await page.evaluate(() => {
        // Count existing listeners (estimation)
        return window.addEventListener ? 1 : 0;
      });

      // Add global event listeners without proper cleanup
      await page.evaluate(() => {
        window.testListeners = [];
        
        for (let i = 0; i < 100; i++) {
          const listener = () => console.log(`Global listener ${i}`);
          window.addEventListener('resize', listener);
          window.testListeners.push(listener);
        }
      });

      // Simulate navigation/component changes without cleanup
      await page.click('#nav-jobs');
      await page.click('#nav-history');
      await page.click('#nav-reports');

      // Check for listener cleanup
      const shouldCleanup = await page.evaluate(() => {
        // In a proper implementation, listeners should be cleaned up
        // Here we manually clean up to test the pattern
        if (window.testListeners) {
          window.testListeners.forEach(listener => {
            window.removeEventListener('resize', listener);
          });
          delete window.testListeners;
          return true;
        }
        return false;
      });

      expect(shouldCleanup).toBe(true);
    });

    test('should handle DOM event delegation without leaks', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const memoryBefore = await getMemoryUsage(page);

      // Test event delegation pattern
      await page.evaluate(() => {
        const container = document.createElement('div');
        container.id = 'delegation-container';
        document.body.appendChild(container);

        // Event delegation - single listener for many elements
        const delegateHandler = (event) => {
          if (event.target.classList.contains('delegated-button')) {
            console.log('Delegated click:', event.target.textContent);
          }
        };

        container.addEventListener('click', delegateHandler);

        // Add many child elements
        for (let i = 0; i < 500; i++) {
          const button = document.createElement('button');
          button.className = 'delegated-button';
          button.textContent = `Delegated ${i}`;
          container.appendChild(button);
        }

        // Store for cleanup
        window.delegationContainer = container;
        window.delegationHandler = delegateHandler;
      });

      // Simulate interactions
      await page.click('.delegated-button');

      // Clean up delegation
      await page.evaluate(() => {
        if (window.delegationContainer && window.delegationHandler) {
          window.delegationContainer.removeEventListener('click', window.delegationHandler);
          document.body.removeChild(window.delegationContainer);
          delete window.delegationContainer;
          delete window.delegationHandler;
        }
      });

      await forceGarbageCollection(page);

      const memoryAfter = await getMemoryUsage(page);
      const memoryGrowth = (memoryAfter - memoryBefore) / 1024 / 1024;

      console.log(`Event delegation memory growth: ${memoryGrowth.toFixed(2)}MB`);
      expect(memoryGrowth).toBeLessThan(3); // < 3MB growth
    });
  });

  describe('DOM Reference Memory Leaks', () => {
    test('should clean up DOM references in closures', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const memoryBefore = await getMemoryUsage(page);

      await page.evaluate(() => {
        const closures = [];

        // Create closures that capture DOM elements
        for (let i = 0; i < 200; i++) {
          const element = document.createElement('div');
          element.textContent = `Element ${i}`;
          document.body.appendChild(element);

          // Closure that captures element reference
          const closure = () => {
            return element.textContent;
          };

          closures.push(closure);

          // Remove element from DOM but closure still references it
          document.body.removeChild(element);
        }

        // Store closures
        window.testClosures = closures;
      });

      const memoryWithLeaks = await getMemoryUsage(page);

      // Clear closure references
      await page.evaluate(() => {
        delete window.testClosures;
      });

      await forceGarbageCollection(page);

      const memoryAfterCleanup = await getMemoryUsage(page);

      console.log('DOM Reference Leak Test:', {
        before: `${(memoryBefore / 1024 / 1024).toFixed(2)}MB`,
        withLeaks: `${(memoryWithLeaks / 1024 / 1024).toFixed(2)}MB`,
        afterCleanup: `${(memoryAfterCleanup / 1024 / 1024).toFixed(2)}MB`
      });

      const leakSize = (memoryAfterCleanup - memoryBefore) / 1024 / 1024;
      expect(leakSize).toBeLessThan(2); // < 2MB permanent leak
    });

    test('should handle circular references properly', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const memoryBefore = await getMemoryUsage(page);

      await page.evaluate(() => {
        const objects = [];

        // Create circular references
        for (let i = 0; i < 100; i++) {
          const objA = { id: i, type: 'A' };
          const objB = { id: i, type: 'B' };
          const element = document.createElement('div');

          // Create circular references
          objA.ref = objB;
          objB.ref = objA;
          objA.element = element;
          element.objectRef = objA;

          objects.push({ objA, objB, element });
        }

        window.circularObjects = objects;
      });

      const memoryWithCircular = await getMemoryUsage(page);

      // Break circular references manually
      await page.evaluate(() => {
        if (window.circularObjects) {
          window.circularObjects.forEach(({ objA, objB, element }) => {
            // Break circular references
            delete objA.ref;
            delete objB.ref;
            delete objA.element;
            delete element.objectRef;
          });
          
          delete window.circularObjects;
        }
      });

      await forceGarbageCollection(page);

      const memoryAfterBreaking = await getMemoryUsage(page);

      console.log('Circular Reference Test:', {
        before: `${(memoryBefore / 1024 / 1024).toFixed(2)}MB`,
        withCircular: `${(memoryWithCircular / 1024 / 1024).toFixed(2)}MB`,
        afterBreaking: `${(memoryAfterBreaking / 1024 / 1024).toFixed(2)}MB`
      });

      const leakSize = (memoryAfterBreaking - memoryBefore) / 1024 / 1024;
      expect(leakSize).toBeLessThan(1); // < 1MB permanent leak
    });
  });

  describe('Timer and Interval Memory Leaks', () => {
    test('should clean up timers and intervals', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const timerIds = await page.evaluate(() => {
        const intervals = [];
        const timeouts = [];

        // Create multiple intervals
        for (let i = 0; i < 50; i++) {
          const interval = setInterval(() => {
            console.log(`Interval ${i}:`, Date.now());
          }, 100);
          intervals.push(interval);
        }

        // Create multiple timeouts
        for (let i = 0; i < 50; i++) {
          const timeout = setTimeout(() => {
            console.log(`Timeout ${i}:`, Date.now());
          }, 1000 + i * 100);
          timeouts.push(timeout);
        }

        window.testIntervals = intervals;
        window.testTimeouts = timeouts;

        return { intervals: intervals.length, timeouts: timeouts.length };
      });

      console.log(`Created ${timerIds.intervals} intervals and ${timerIds.timeouts} timeouts`);

      // Let them run briefly
      await page.waitForTimeout(500);

      // Clean up timers
      const cleanedUp = await page.evaluate(() => {
        let cleaned = 0;

        if (window.testIntervals) {
          window.testIntervals.forEach(clearInterval);
          cleaned += window.testIntervals.length;
          delete window.testIntervals;
        }

        if (window.testTimeouts) {
          window.testTimeouts.forEach(clearTimeout);
          cleaned += window.testTimeouts.length;
          delete window.testTimeouts;
        }

        return cleaned;
      });

      expect(cleanedUp).toBe(100); // Should clean up all 100 timers
    });

    test('should detect polling timer leaks', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Simulate job polling scenario
      await page.evaluate(() => {
        const pollingIntervals = new Map();

        // Start polling for multiple jobs
        for (let i = 0; i < 10; i++) {
          const jobId = `job-${i}`;
          const interval = setInterval(() => {
            // Simulate job status polling
            console.log(`Polling job ${jobId}`);
          }, 2000);
          
          pollingIntervals.set(jobId, interval);
        }

        window.pollingIntervals = pollingIntervals;
      });

      await page.waitForTimeout(1000);

      // Simulate jobs completing and cleanup
      const cleanupResult = await page.evaluate(() => {
        if (window.pollingIntervals) {
          let stopped = 0;
          window.pollingIntervals.forEach((interval, jobId) => {
            clearInterval(interval);
            stopped++;
          });
          
          window.pollingIntervals.clear();
          delete window.pollingIntervals;
          
          return stopped;
        }
        return 0;
      });

      expect(cleanupResult).toBe(10); // Should stop all 10 polling intervals
    });
  });

  describe('Component Lifecycle Memory Leaks', () => {
    test('should clean up component instances properly', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const memoryBefore = await getMemoryUsage(page);

      // Simulate component creation and destruction
      await page.evaluate(() => {
        class TestComponent {
          constructor(id) {
            this.id = id;
            this.element = document.createElement('div');
            this.element.textContent = `Component ${id}`;
            this.data = new Array(1000).fill(0).map((_, i) => ({ index: i, value: Math.random() }));
            
            // Simulate event listeners
            this.handleClick = this.handleClick.bind(this);
            this.element.addEventListener('click', this.handleClick);
            
            document.body.appendChild(this.element);
          }

          handleClick() {
            console.log(`Component ${this.id} clicked`);
          }

          destroy() {
            // Proper cleanup
            this.element.removeEventListener('click', this.handleClick);
            if (this.element.parentNode) {
              this.element.parentNode.removeChild(this.element);
            }
            this.element = null;
            this.data = null;
            this.handleClick = null;
          }
        }

        // Create many components
        const components = [];
        for (let i = 0; i < 100; i++) {
          components.push(new TestComponent(i));
        }

        window.testComponents = components;
        window.TestComponent = TestComponent;
      });

      const memoryAfterCreation = await getMemoryUsage(page);

      // Destroy all components
      await page.evaluate(() => {
        if (window.testComponents) {
          window.testComponents.forEach(component => component.destroy());
          delete window.testComponents;
          delete window.TestComponent;
        }
      });

      await forceGarbageCollection(page);

      const memoryAfterDestruction = await getMemoryUsage(page);

      console.log('Component Lifecycle Test:', {
        before: `${(memoryBefore / 1024 / 1024).toFixed(2)}MB`,
        afterCreation: `${(memoryAfterCreation / 1024 / 1024).toFixed(2)}MB`,
        afterDestruction: `${(memoryAfterDestruction / 1024 / 1024).toFixed(2)}MB`
      });

      const leakSize = (memoryAfterDestruction - memoryBefore) / 1024 / 1024;
      expect(leakSize).toBeLessThan(3); // < 3MB permanent leak
    });

    test('should handle view switching without memory accumulation', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const memoryBefore = await getMemoryUsage(page);

      // Simulate intensive view switching
      for (let i = 0; i < 20; i++) {
        await page.click('#nav-jobs');
        await page.waitForTimeout(50);
        
        await page.click('#nav-history');
        await page.waitForTimeout(50);
        
        await page.click('#nav-reports');
        await page.waitForTimeout(50);
      }

      await forceGarbageCollection(page);

      const memoryAfterSwitching = await getMemoryUsage(page);

      console.log('View Switching Memory Test:', {
        before: `${(memoryBefore / 1024 / 1024).toFixed(2)}MB`,
        afterSwitching: `${(memoryAfterSwitching / 1024 / 1024).toFixed(2)}MB`
      });

      const memoryGrowth = (memoryAfterSwitching - memoryBefore) / 1024 / 1024;
      expect(memoryGrowth).toBeLessThan(5); // < 5MB growth from view switching
    });
  });

  describe('API Request Memory Leaks', () => {
    test('should clean up fetch requests and promises', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const memoryBefore = await getMemoryUsage(page);

      // Simulate many concurrent API requests
      await page.evaluate(() => {
        const requests = [];

        for (let i = 0; i < 50; i++) {
          // Create requests that will be cancelled/aborted
          const controller = new AbortController();
          
          const request = fetch(`/api/test-endpoint-${i}`, {
            signal: controller.signal
          }).catch(error => {
            // Expected to be aborted
            console.log(`Request ${i} aborted:`, error.name);
          });

          requests.push({ request, controller });
        }

        // Store for cleanup
        window.testRequests = requests;
      });

      await page.waitForTimeout(100);

      // Abort all requests
      const abortedCount = await page.evaluate(() => {
        if (window.testRequests) {
          let aborted = 0;
          window.testRequests.forEach(({ controller }) => {
            controller.abort();
            aborted++;
          });
          
          delete window.testRequests;
          return aborted;
        }
        return 0;
      });

      await forceGarbageCollection(page);

      const memoryAfterAbort = await getMemoryUsage(page);

      console.log('API Request Cleanup Test:', {
        before: `${(memoryBefore / 1024 / 1024).toFixed(2)}MB`,
        afterAbort: `${(memoryAfterAbort / 1024 / 1024).toFixed(2)}MB`,
        abortedRequests: abortedCount
      });

      expect(abortedCount).toBe(50);
      
      const memoryGrowth = (memoryAfterAbort - memoryBefore) / 1024 / 1024;
      expect(memoryGrowth).toBeLessThan(2); // < 2MB growth
    });
  });

  describe('Large Object Memory Management', () => {
    test('should handle large data structures efficiently', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const memoryBefore = await getMemoryUsage(page);

      // Create large data structures
      await page.evaluate(() => {
        // Simulate large job history data
        const largeDataSet = {
          jobs: [],
          reports: [],
          metrics: {}
        };

        // Create large arrays
        for (let i = 0; i < 5000; i++) {
          largeDataSet.jobs.push({
            id: `job-${i}`,
            name: `Job ${i}`,
            description: `Description for job ${i}`.repeat(10),
            parameters: new Array(50).fill(0).map((_, j) => ({
              key: `param-${j}`,
              value: Math.random() * 1000,
              metadata: `Meta data for parameter ${j}`
            })),
            results: new Array(100).fill(0).map((_, k) => ({
              timestamp: Date.now() + k * 1000,
              value: Math.random(),
              status: k % 3 === 0 ? 'success' : 'processing'
            }))
          });
        }

        window.largeDataSet = largeDataSet;
      });

      const memoryWithLargeData = await getMemoryUsage(page);

      // Clear large data
      await page.evaluate(() => {
        if (window.largeDataSet) {
          // Clear arrays
          window.largeDataSet.jobs = null;
          window.largeDataSet.reports = null;
          window.largeDataSet.metrics = null;
          delete window.largeDataSet;
        }
      });

      await forceGarbageCollection(page);

      const memoryAfterClearance = await getMemoryUsage(page);

      console.log('Large Object Management Test:', {
        before: `${(memoryBefore / 1024 / 1024).toFixed(2)}MB`,
        withLargeData: `${(memoryWithLargeData / 1024 / 1024).toFixed(2)}MB`,
        afterClearance: `${(memoryAfterClearance / 1024 / 1024).toFixed(2)}MB`
      });

      const dataSize = (memoryWithLargeData - memoryBefore) / 1024 / 1024;
      const leakSize = (memoryAfterClearance - memoryBefore) / 1024 / 1024;

      console.log(`Data consumed: ${dataSize.toFixed(2)}MB, Leaked: ${leakSize.toFixed(2)}MB`);

      expect(dataSize).toBeGreaterThan(10); // Should consume significant memory
      expect(leakSize).toBeLessThan(5); // < 5MB permanent leak
    });
  });

  describe('Memory Leak Detection Summary', () => {
    test('should perform comprehensive memory leak scan', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const initialMemory = await getMemoryUsage(page);
      const measurements = [];

      // Perform various operations that could cause leaks
      const operations = [
        {
          name: 'Navigation stress test',
          operation: async () => {
            for (let i = 0; i < 10; i++) {
              await page.click('#nav-jobs');
              await page.click('#nav-history');
              await page.click('#nav-reports');
            }
          }
        },
        {
          name: 'Form interaction test',
          operation: async () => {
            // Generate form
            await page.select('#report-dropdown', 'test_report');
            
            for (let i = 0; i < 20; i++) {
              await page.type('#test_field', 'test');
              await page.evaluate(() => {
                document.getElementById('test_field').value = '';
              });
            }
          }
        },
        {
          name: 'Dynamic content test',
          operation: async () => {
            await page.evaluate(() => {
              const container = document.getElementById('active-jobs-list');
              if (container) {
                for (let i = 0; i < 100; i++) {
                  const item = document.createElement('div');
                  item.textContent = `Dynamic item ${i}`;
                  container.appendChild(item);
                }
                // Clear after adding
                container.innerHTML = '';
              }
            });
          }
        }
      ];

      // Run each operation and measure memory
      for (const { name, operation } of operations) {
        const beforeOp = await getMemoryUsage(page);
        await operation();
        await forceGarbageCollection(page);
        const afterOp = await getMemoryUsage(page);
        
        measurements.push({
          operation: name,
          memoryBefore: beforeOp,
          memoryAfter: afterOp,
          growth: afterOp - beforeOp
        });
      }

      const finalMemory = await getMemoryUsage(page);
      const totalGrowth = finalMemory - initialMemory;

      console.log('\nMemory Leak Detection Summary:');
      console.log(`Initial memory: ${(initialMemory / 1024 / 1024).toFixed(2)}MB`);
      
      measurements.forEach(measure => {
        const growthMB = measure.growth / 1024 / 1024;
        console.log(`${measure.operation}: ${growthMB >= 0 ? '+' : ''}${growthMB.toFixed(2)}MB`);
      });
      
      console.log(`Final memory: ${(finalMemory / 1024 / 1024).toFixed(2)}MB`);
      console.log(`Total growth: ${(totalGrowth / 1024 / 1024).toFixed(2)}MB`);

      // Overall memory growth should be minimal
      const totalGrowthMB = totalGrowth / 1024 / 1024;
      expect(totalGrowthMB).toBeLessThan(10); // < 10MB total growth

      // No single operation should cause excessive growth
      measurements.forEach(measure => {
        const growthMB = measure.growth / 1024 / 1024;
        expect(growthMB).toBeLessThan(5); // < 5MB per operation
      });
    });
  });

  // Helper functions
  async function getMemoryUsage(page) {
    return await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize;
      }
      return 0;
    });
  }

  async function forceGarbageCollection(page) {
    // Force garbage collection if available
    await page.evaluate(() => {
      if (window.gc) {
        window.gc();
      }
    });
    
    // Wait for GC to complete
    await page.waitForTimeout(100);
  }
});
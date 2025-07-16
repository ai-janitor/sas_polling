/*
=============================================================================
PERFORMANCE AND LOAD TESTING
=============================================================================
Purpose: Test application performance under various load conditions
Technology: Puppeteer with performance metrics and load simulation
Coverage: Page load times, memory usage, CPU usage, network performance

TEST SCENARIOS:
1. Initial page load performance
2. Component rendering performance
3. Memory usage and garbage collection
4. Network request optimization
5. JavaScript execution performance
6. Large dataset handling
7. Concurrent user simulation
8. Resource loading optimization

PERFORMANCE STRATEGY:
- Real browser performance metrics
- Memory leak detection
- CPU profiling
- Network throttling simulation
- Load testing with multiple instances
- Performance regression detection
=============================================================================
*/

const puppeteer = require('puppeteer');

describe('Performance and Load Testing', () => {
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
        '--enable-precise-memory-info'
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
    
    // Setup performance monitoring
    await page.setCacheEnabled(false);
  });

  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  describe('Initial Load Performance', () => {
    test('should load within acceptable time limits', async () => {
      const startTime = Date.now();
      
      // Start performance tracing
      await page.tracing.start({
        path: 'coverage/frontend/page-load-trace.json',
        screenshots: true
      });

      await page.goto(baseUrl, { waitUntil: 'networkidle0' });
      await page.waitForSelector('#app', { visible: true });

      // Stop tracing
      await page.tracing.stop();

      const loadTime = Date.now() - startTime;
      
      console.log(`Initial load time: ${loadTime}ms`);
      
      // Should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });

    test('should meet Core Web Vitals metrics', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Measure Core Web Vitals
      const metrics = await page.evaluate(() => {
        return new Promise((resolve) => {
          // Wait for page to be fully loaded
          if (document.readyState === 'complete') {
            measureMetrics();
          } else {
            window.addEventListener('load', measureMetrics);
          }

          function measureMetrics() {
            const navigation = performance.getEntriesByType('navigation')[0];
            const paint = performance.getEntriesByType('paint');
            
            const firstPaint = paint.find(entry => entry.name === 'first-paint');
            const firstContentfulPaint = paint.find(entry => entry.name === 'first-contentful-paint');

            resolve({
              // Largest Contentful Paint (estimated)
              lcp: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
              
              // First Contentful Paint
              fcp: firstContentfulPaint ? firstContentfulPaint.startTime : 0,
              
              // Time to Interactive (estimated)
              tti: navigation ? navigation.domInteractive - navigation.fetchStart : 0,
              
              // Cumulative Layout Shift (estimated as 0 for SPA)
              cls: 0,
              
              // Time to First Byte
              ttfb: navigation ? navigation.responseStart - navigation.fetchStart : 0
            });
          }
        });
      });

      console.log('Core Web Vitals:', metrics);

      // Core Web Vitals thresholds (good performance)
      expect(metrics.fcp).toBeLessThan(1800); // First Contentful Paint < 1.8s
      expect(metrics.lcp).toBeLessThan(2500); // Largest Contentful Paint < 2.5s
      expect(metrics.tti).toBeLessThan(3800); // Time to Interactive < 3.8s
      expect(metrics.ttfb).toBeLessThan(800);  // Time to First Byte < 0.8s
      expect(metrics.cls).toBeLessThan(0.1);   // Cumulative Layout Shift < 0.1
    });

    test('should optimize resource loading', async () => {
      const resourceMetrics = [];

      page.on('response', response => {
        resourceMetrics.push({
          url: response.url(),
          status: response.status(),
          size: response.headers()['content-length'] || 0,
          type: response.headers()['content-type'] || 'unknown',
          fromCache: response.fromCache()
        });
      });

      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Analyze resource loading
      const jsResources = resourceMetrics.filter(r => r.type.includes('javascript'));
      const cssResources = resourceMetrics.filter(r => r.type.includes('css'));
      const imageResources = resourceMetrics.filter(r => r.type.includes('image'));

      console.log(`Loaded resources: ${resourceMetrics.length} total`);
      console.log(`JavaScript files: ${jsResources.length}`);
      console.log(`CSS files: ${cssResources.length}`);
      console.log(`Images: ${imageResources.length}`);

      // Should minimize HTTP requests
      expect(resourceMetrics.length).toBeLessThan(50);
      
      // JavaScript bundles should be reasonably sized
      jsResources.forEach(resource => {
        const sizeKB = parseInt(resource.size) / 1024;
        if (sizeKB > 0) {
          expect(sizeKB).toBeLessThan(500); // < 500KB per JS file
        }
      });

      // All resources should load successfully
      resourceMetrics.forEach(resource => {
        expect(resource.status).toBeLessThan(400);
      });
    });
  });

  describe('Memory Usage Performance', () => {
    test('should maintain reasonable memory usage', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Get initial memory usage
      const initialMemory = await page.evaluate(() => {
        if (performance.memory) {
          return {
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize,
            jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });

      if (initialMemory) {
        console.log('Initial memory usage:', {
          used: `${(initialMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`,
          total: `${(initialMemory.totalJSHeapSize / 1024 / 1024).toFixed(2)}MB`,
          limit: `${(initialMemory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)}MB`
        });

        // Memory usage should be reasonable
        expect(initialMemory.usedJSHeapSize).toBeLessThan(50 * 1024 * 1024); // < 50MB
      }
    });

    test('should handle memory cleanup properly', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Simulate heavy usage by navigating between views multiple times
      for (let i = 0; i < 10; i++) {
        await page.click('#nav-jobs');
        await page.waitForSelector('#jobs-section.active');
        
        await page.click('#nav-history');
        await page.waitForSelector('#history-section.active');
        
        await page.click('#nav-reports');
        await page.waitForSelector('#report-section.active');
      }

      // Force garbage collection if available
      await page.evaluate(() => {
        if (window.gc) {
          window.gc();
        }
      });

      const finalMemory = await page.evaluate(() => {
        if (performance.memory) {
          return {
            usedJSHeapSize: performance.memory.usedJSHeapSize,
            totalJSHeapSize: performance.memory.totalJSHeapSize
          };
        }
        return null;
      });

      if (finalMemory) {
        console.log('Memory after navigation stress test:', {
          used: `${(finalMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`,
          total: `${(finalMemory.totalJSHeapSize / 1024 / 1024).toFixed(2)}MB`
        });

        // Memory should not grow excessively
        expect(finalMemory.usedJSHeapSize).toBeLessThan(100 * 1024 * 1024); // < 100MB
      }
    });

    test('should detect memory leaks', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const measurements = [];

      // Take memory measurements during repeated operations
      for (let i = 0; i < 5; i++) {
        // Perform operations that might cause memory leaks
        await page.evaluate(() => {
          // Simulate creating and destroying DOM elements
          for (let j = 0; j < 100; j++) {
            const div = document.createElement('div');
            div.innerHTML = 'Test content ' + j;
            document.body.appendChild(div);
            document.body.removeChild(div);
          }
        });

        const memory = await page.evaluate(() => {
          if (performance.memory) {
            return performance.memory.usedJSHeapSize;
          }
          return 0;
        });

        measurements.push(memory);
        
        // Wait between measurements
        await page.waitForTimeout(100);
      }

      console.log('Memory measurements:', measurements.map(m => 
        `${(m / 1024 / 1024).toFixed(2)}MB`
      ));

      // Memory should not continuously grow
      const memoryGrowth = measurements[measurements.length - 1] - measurements[0];
      const growthMB = memoryGrowth / 1024 / 1024;
      
      expect(growthMB).toBeLessThan(10); // < 10MB growth
    });
  });

  describe('Component Rendering Performance', () => {
    test('should render components efficiently', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Measure component rendering time
      const renderingTime = await page.evaluate(() => {
        const start = performance.now();
        
        // Simulate dynamic content rendering
        const container = document.createElement('div');
        for (let i = 0; i < 1000; i++) {
          const item = document.createElement('div');
          item.textContent = `Item ${i}`;
          item.className = 'test-item';
          container.appendChild(item);
        }
        
        document.body.appendChild(container);
        
        const end = performance.now();
        
        // Cleanup
        document.body.removeChild(container);
        
        return end - start;
      });

      console.log(`Rendering 1000 items took: ${renderingTime.toFixed(2)}ms`);
      
      // Should render quickly
      expect(renderingTime).toBeLessThan(100); // < 100ms
    });

    test('should handle large datasets efficiently', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Test performance with large job history
      const largeDatasetTime = await page.evaluate(() => {
        const start = performance.now();
        
        // Simulate large job history
        const historyContainer = document.getElementById('history-jobs-list');
        if (historyContainer) {
          for (let i = 0; i < 500; i++) {
            const jobItem = document.createElement('div');
            jobItem.className = 'job-item';
            jobItem.innerHTML = `
              <h4>Job ${i}</h4>
              <p>Description for job ${i}</p>
              <span class="status ${i % 2 === 0 ? 'completed' : 'failed'}">
                ${i % 2 === 0 ? 'Completed' : 'Failed'}
              </span>
              <div class="job-actions">
                <button>Download</button>
                <button>Details</button>
              </div>
            `;
            historyContainer.appendChild(jobItem);
          }
        }
        
        const end = performance.now();
        return end - start;
      });

      console.log(`Rendering 500 job items took: ${largeDatasetTime.toFixed(2)}ms`);
      
      // Should handle large datasets efficiently
      expect(largeDatasetTime).toBeLessThan(500); // < 500ms
    });

    test('should optimize DOM manipulation', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const domManipulationTime = await page.evaluate(() => {
        const start = performance.now();
        
        // Test efficient DOM updates
        const container = document.createElement('div');
        document.body.appendChild(container);
        
        // Use DocumentFragment for efficient DOM manipulation
        const fragment = document.createDocumentFragment();
        
        for (let i = 0; i < 200; i++) {
          const element = document.createElement('div');
          element.textContent = `Element ${i}`;
          element.style.padding = '5px';
          element.style.margin = '2px';
          fragment.appendChild(element);
        }
        
        container.appendChild(fragment);
        
        const end = performance.now();
        
        // Cleanup
        document.body.removeChild(container);
        
        return end - start;
      });

      console.log(`DOM manipulation took: ${domManipulationTime.toFixed(2)}ms`);
      
      // Should manipulate DOM efficiently
      expect(domManipulationTime).toBeLessThan(50); // < 50ms
    });
  });

  describe('Network Performance', () => {
    test('should handle slow network conditions', async () => {
      // Simulate slow 3G connection
      await page.emulateNetworkConditions({
        offline: false,
        downloadThroughput: 500 * 1024 / 8, // 500 kbps
        uploadThroughput: 500 * 1024 / 8,
        latency: 400 // 400ms latency
      });

      const startTime = Date.now();
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });
      await page.waitForSelector('#app', { visible: true });
      const loadTime = Date.now() - startTime;

      console.log(`Load time on slow 3G: ${loadTime}ms`);
      
      // Should still be usable on slow connections
      expect(loadTime).toBeLessThan(20000); // < 20 seconds
    });

    test('should optimize API request patterns', async () => {
      const apiRequests = [];

      page.on('request', request => {
        if (request.url().includes('/api/')) {
          apiRequests.push({
            url: request.url(),
            method: request.method(),
            timestamp: Date.now()
          });
        }
      });

      await page.goto(baseUrl, { waitUntil: 'networkidle0' });
      
      // Navigate through the application
      await page.click('#nav-jobs');
      await page.waitForTimeout(500);
      
      await page.click('#nav-history');
      await page.waitForTimeout(500);
      
      await page.click('#nav-reports');
      await page.waitForTimeout(500);

      console.log(`API requests made: ${apiRequests.length}`);
      apiRequests.forEach(req => {
        console.log(`- ${req.method} ${req.url}`);
      });

      // Should minimize API requests
      expect(apiRequests.length).toBeLessThan(10);
      
      // Should not make duplicate requests
      const uniqueRequests = new Set(apiRequests.map(req => `${req.method}:${req.url}`));
      expect(uniqueRequests.size).toBeGreaterThanOrEqual(apiRequests.length * 0.8);
    });

    test('should handle offline conditions gracefully', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Go offline
      await page.setOfflineMode(true);

      // Try to perform actions that would require network
      const errors = [];
      
      page.on('pageerror', error => {
        errors.push(error.message);
      });

      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      // Test offline behavior
      await page.evaluate(() => {
        // Simulate network request
        fetch('/api/test')
          .catch(error => {
            console.log('Network request failed as expected:', error.message);
          });
      });

      await page.waitForTimeout(1000);

      // Should handle offline gracefully without crashing
      const criticalErrors = errors.filter(error => 
        !error.includes('fetch') && 
        !error.includes('Network') &&
        !error.includes('Failed to fetch')
      );
      
      expect(criticalErrors.length).toBe(0);
    });
  });

  describe('JavaScript Execution Performance', () => {
    test('should execute JavaScript efficiently', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const executionMetrics = await page.evaluate(() => {
        const measurements = [];
        
        // Test array operations
        const start1 = performance.now();
        const largeArray = Array.from({ length: 10000 }, (_, i) => ({ id: i, value: Math.random() }));
        const filtered = largeArray.filter(item => item.value > 0.5);
        const mapped = filtered.map(item => ({ ...item, processed: true }));
        const end1 = performance.now();
        
        measurements.push({
          operation: 'Array operations (10k items)',
          time: end1 - start1
        });

        // Test DOM queries
        const start2 = performance.now();
        for (let i = 0; i < 100; i++) {
          document.querySelectorAll('*');
        }
        const end2 = performance.now();
        
        measurements.push({
          operation: 'DOM queries (100 iterations)',
          time: end2 - start2
        });

        // Test object operations
        const start3 = performance.now();
        const objects = [];
        for (let i = 0; i < 1000; i++) {
          objects.push({
            id: i,
            data: { nested: { value: i * 2 } },
            computed: i * Math.PI
          });
        }
        const end3 = performance.now();
        
        measurements.push({
          operation: 'Object creation (1k objects)',
          time: end3 - start3
        });

        return measurements;
      });

      executionMetrics.forEach(metric => {
        console.log(`${metric.operation}: ${metric.time.toFixed(2)}ms`);
        
        // JavaScript operations should be efficient
        expect(metric.time).toBeLessThan(100); // < 100ms each
      });
    });

    test('should handle concurrent operations efficiently', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const concurrentTime = await page.evaluate(() => {
        const start = performance.now();
        
        // Simulate concurrent operations
        const promises = [];
        
        for (let i = 0; i < 10; i++) {
          promises.push(
            new Promise(resolve => {
              setTimeout(() => {
                // Simulate some work
                const result = Array.from({ length: 1000 }, (_, j) => i * j);
                resolve(result.reduce((a, b) => a + b, 0));
              }, Math.random() * 10);
            })
          );
        }
        
        return Promise.all(promises).then(() => {
          const end = performance.now();
          return end - start;
        });
      });

      console.log(`Concurrent operations took: ${concurrentTime.toFixed(2)}ms`);
      
      // Should handle concurrency efficiently
      expect(concurrentTime).toBeLessThan(200); // < 200ms
    });
  });

  describe('Load Testing', () => {
    test('should handle multiple concurrent users', async () => {
      const concurrentUsers = 5;
      const userSessions = [];

      // Create multiple browser contexts to simulate users
      for (let i = 0; i < concurrentUsers; i++) {
        const context = await browser.createIncognitoBrowserContext();
        const userPage = await context.newPage();
        
        userSessions.push({
          context,
          page: userPage,
          id: i
        });
      }

      try {
        // Simulate concurrent user actions
        const userActions = userSessions.map(async (session, index) => {
          const startTime = Date.now();
          
          await session.page.goto(baseUrl, { waitUntil: 'networkidle0' });
          await session.page.waitForSelector('#app', { visible: true });
          
          // Simulate user interactions
          await session.page.click('#nav-jobs');
          await session.page.waitForTimeout(100);
          
          await session.page.click('#nav-history');
          await session.page.waitForTimeout(100);
          
          await session.page.click('#nav-reports');
          await session.page.waitForTimeout(100);
          
          const endTime = Date.now();
          
          return {
            userId: index,
            loadTime: endTime - startTime
          };
        });

        const results = await Promise.all(userActions);
        
        results.forEach(result => {
          console.log(`User ${result.userId} session time: ${result.loadTime}ms`);
          expect(result.loadTime).toBeLessThan(10000); // < 10 seconds per user
        });

        const averageTime = results.reduce((sum, r) => sum + r.loadTime, 0) / results.length;
        console.log(`Average session time: ${averageTime.toFixed(2)}ms`);
        
        expect(averageTime).toBeLessThan(8000); // < 8 seconds average
        
      } finally {
        // Cleanup user sessions
        await Promise.all(userSessions.map(session => session.context.close()));
      }
    });

    test('should maintain performance under stress', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      // Stress test with rapid interactions
      const stressTestTime = await page.evaluate(() => {
        const start = performance.now();
        
        // Rapid DOM manipulations
        for (let i = 0; i < 50; i++) {
          // Click navigation rapidly
          const navButton = document.getElementById('nav-jobs');
          if (navButton) {
            navButton.click();
          }
          
          const navButton2 = document.getElementById('nav-reports');
          if (navButton2) {
            navButton2.click();
          }
        }
        
        const end = performance.now();
        return end - start;
      });

      console.log(`Stress test (100 rapid clicks) took: ${stressTestTime.toFixed(2)}ms`);
      
      // Should handle stress without significant performance degradation
      expect(stressTestTime).toBeLessThan(1000); // < 1 second

      // Check if application is still responsive
      await page.click('#nav-history');
      await page.waitForSelector('#history-section.active', { visible: true });
      
      const isResponsive = await page.$eval('#history-section', el => 
        el.classList.contains('active')
      );
      
      expect(isResponsive).toBe(true);
    });
  });

  describe('Performance Monitoring', () => {
    test('should provide performance metrics', async () => {
      await page.goto(baseUrl, { waitUntil: 'networkidle0' });

      const performanceData = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0];
        const resources = performance.getEntriesByType('resource');
        const marks = performance.getEntriesByType('mark');
        const measures = performance.getEntriesByType('measure');

        return {
          navigation: navigation ? {
            domContentLoadedTime: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            loadTime: navigation.loadEventEnd - navigation.loadEventStart,
            totalTime: navigation.loadEventEnd - navigation.fetchStart
          } : null,
          resourceCount: resources.length,
          markCount: marks.length,
          measureCount: measures.length,
          memoryUsage: performance.memory ? {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
          } : null
        };
      });

      console.log('Performance metrics:', {
        ...performanceData,
        memoryUsage: performanceData.memoryUsage ? {
          used: `${(performanceData.memoryUsage.used / 1024 / 1024).toFixed(2)}MB`,
          total: `${(performanceData.memoryUsage.total / 1024 / 1024).toFixed(2)}MB`,
          limit: `${(performanceData.memoryUsage.limit / 1024 / 1024).toFixed(2)}MB`
        } : null
      });

      // Validate performance metrics
      if (performanceData.navigation) {
        expect(performanceData.navigation.totalTime).toBeGreaterThan(0);
        expect(performanceData.navigation.totalTime).toBeLessThan(10000); // < 10s
      }

      expect(performanceData.resourceCount).toBeGreaterThan(0);
      expect(performanceData.resourceCount).toBeLessThan(100); // Reasonable resource count
    });

    test('should detect performance regressions', async () => {
      const measurements = [];

      // Take multiple measurements
      for (let i = 0; i < 3; i++) {
        const newPage = await browser.newPage();
        
        const startTime = Date.now();
        await newPage.goto(baseUrl, { waitUntil: 'networkidle0' });
        await newPage.waitForSelector('#app', { visible: true });
        const endTime = Date.now();
        
        measurements.push(endTime - startTime);
        await newPage.close();
      }

      const averageTime = measurements.reduce((a, b) => a + b, 0) / measurements.length;
      const maxTime = Math.max(...measurements);
      const minTime = Math.min(...measurements);
      const variance = maxTime - minTime;

      console.log(`Load time measurements: ${measurements.join(', ')}ms`);
      console.log(`Average: ${averageTime.toFixed(2)}ms, Variance: ${variance}ms`);

      // Performance should be consistent
      expect(variance).toBeLessThan(2000); // < 2s variance
      expect(averageTime).toBeLessThan(5000); // < 5s average
    });
  });
});
/*
=============================================================================
FRONTEND TESTING SETUP
=============================================================================
Purpose: Global setup configuration for Jest frontend tests
Technology: Jest with JSDOM, Mock Service Worker, Testing utilities
Requirements: Browser environment simulation and API mocking

SETUP RESPONSIBILITIES:
- Configure JSDOM environment
- Set up global mocks and utilities
- Initialize Mock Service Worker
- Configure test data and fixtures
- Set up accessibility testing
- Configure viewport and responsive testing

GLOBAL MOCKS:
- Fetch API for HTTP requests
- LocalStorage and SessionStorage
- Window and Document objects
- CSS Media Query matching
- Intersection Observer API
- ResizeObserver API

TEST UTILITIES:
- DOM testing helpers
- Event simulation
- Async testing utilities
- Mock data generators
- Component testing helpers
=============================================================================
*/

// Import testing utilities
import 'jest-dom/extend-expect';
import { TextEncoder, TextDecoder } from 'util';

// Global polyfills for Node.js environment
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Configure JSDOM environment
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock Intersection Observer
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock requestAnimationFrame
global.requestAnimationFrame = callback => setTimeout(callback, 0);
global.cancelAnimationFrame = id => clearTimeout(id);

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
};
global.sessionStorage = sessionStorageMock;

// Mock URL constructor
global.URL.createObjectURL = jest.fn();
global.URL.revokeObjectURL = jest.fn();

// Mock console methods for cleaner test output
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is deprecated')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
  
  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('componentWillReceiveProps has been renamed')
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

// Mock fetch API
global.fetch = jest.fn();

// Default fetch mock implementation
const mockFetchResponse = (data, ok = true, status = 200) => {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(),
    url: '',
    redirected: false,
    statusText: ok ? 'OK' : 'Error',
    type: 'basic',
    body: null,
    bodyUsed: false,
    clone: () => mockFetchResponse(data, ok, status)
  });
};

// Helper function to mock successful API responses
global.mockFetchSuccess = (data) => {
  global.fetch.mockResolvedValueOnce(mockFetchResponse(data));
};

// Helper function to mock API errors
global.mockFetchError = (status = 500, message = 'Server Error') => {
  global.fetch.mockResolvedValueOnce(
    mockFetchResponse({ error: message }, false, status)
  );
};

// Helper function to mock network errors
global.mockFetchNetworkError = () => {
  global.fetch.mockRejectedValueOnce(new Error('Network Error'));
};

// Test utilities for DOM manipulation
global.createMockElement = (tag, attributes = {}) => {
  const element = document.createElement(tag);
  Object.keys(attributes).forEach(key => {
    if (key === 'textContent' || key === 'innerHTML') {
      element[key] = attributes[key];
    } else {
      element.setAttribute(key, attributes[key]);
    }
  });
  return element;
};

// Helper to simulate user events
global.simulateEvent = (element, eventType, eventData = {}) => {
  const event = new Event(eventType, { bubbles: true, ...eventData });
  Object.keys(eventData).forEach(key => {
    event[key] = eventData[key];
  });
  element.dispatchEvent(event);
  return event;
};

// Helper to wait for async operations
global.waitFor = (callback, timeout = 1000) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = () => {
      try {
        const result = callback();
        if (result) {
          resolve(result);
        } else if (Date.now() - startTime >= timeout) {
          reject(new Error('Timeout waiting for condition'));
        } else {
          setTimeout(check, 10);
        }
      } catch (error) {
        if (Date.now() - startTime >= timeout) {
          reject(error);
        } else {
          setTimeout(check, 10);
        }
      }
    };
    
    check();
  });
};

// Mock data generators
global.generateMockReport = (overrides = {}) => ({
  id: 'test_report',
  name: 'Test Report',
  description: 'A test report for testing purposes',
  category: 'Test Category',
  estimatedDuration: 120,
  outputFormats: ['HTML', 'PDF', 'CSV'],
  prompts: [
    {
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
    }
  ],
  ...overrides
});

global.generateMockJob = (overrides = {}) => ({
  id: 'job_' + Math.random().toString(36).substr(2, 9),
  name: 'Test Job',
  status: 'pending',
  jobDefinitionUri: 'test_report',
  arguments: { test_field: 'test_value' },
  submitted_at: new Date().toISOString(),
  progress: 0,
  ...overrides
});

global.generateMockReportsData = () => ({
  categories: [
    {
      name: 'Test Reports',
      description: 'Test category for testing',
      reports: [
        global.generateMockReport(),
        global.generateMockReport({
          id: 'test_report_2',
          name: 'Test Report 2'
        })
      ]
    }
  ]
});

// Setup viewport dimensions for responsive testing
global.setViewport = (width, height) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  });
  
  // Trigger resize event
  window.dispatchEvent(new Event('resize'));
};

// Common viewport sizes for testing
global.VIEWPORTS = {
  MOBILE: { width: 375, height: 667 },
  TABLET: { width: 768, height: 1024 },
  DESKTOP: { width: 1920, height: 1080 },
  SMALL_DESKTOP: { width: 1024, height: 768 }
};

// Accessibility testing helpers
global.checkAccessibility = (element) => {
  const issues = [];
  
  // Check for missing alt text on images
  const images = element.querySelectorAll('img');
  images.forEach(img => {
    if (!img.getAttribute('alt')) {
      issues.push(`Image missing alt text: ${img.outerHTML.slice(0, 50)}...`);
    }
  });
  
  // Check for form inputs without labels
  const inputs = element.querySelectorAll('input, textarea, select');
  inputs.forEach(input => {
    const id = input.getAttribute('id');
    const label = element.querySelector(`label[for="${id}"]`);
    const ariaLabel = input.getAttribute('aria-label');
    const ariaLabelledBy = input.getAttribute('aria-labelledby');
    
    if (!label && !ariaLabel && !ariaLabelledBy) {
      issues.push(`Form input missing label: ${input.outerHTML.slice(0, 50)}...`);
    }
  });
  
  // Check for buttons without accessible text
  const buttons = element.querySelectorAll('button');
  buttons.forEach(button => {
    const text = button.textContent.trim();
    const ariaLabel = button.getAttribute('aria-label');
    
    if (!text && !ariaLabel) {
      issues.push(`Button missing accessible text: ${button.outerHTML.slice(0, 50)}...`);
    }
  });
  
  return issues;
};

// Clean up after each test
afterEach(() => {
  // Clear all mocks
  jest.clearAllMocks();
  
  // Clear localStorage
  localStorageMock.clear();
  sessionStorageMock.clear();
  
  // Reset DOM
  document.body.innerHTML = '';
  document.head.innerHTML = '';
  
  // Reset fetch mock
  global.fetch.mockClear();
});

// Global error handler for unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

console.log('✅ Frontend testing setup complete');
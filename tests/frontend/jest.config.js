/*
=============================================================================
JEST CONFIGURATION FOR FRONTEND TESTING
=============================================================================
Purpose: Configure Jest testing framework for JavaScript components
Technology: Jest with JSDOM for browser environment simulation
Coverage: Unit tests, integration tests, and component testing

STRICT REQUIREMENTS:
- 80% JavaScript code coverage minimum
- Browser environment simulation with JSDOM
- Mock API responses and external dependencies
- Test vanilla JavaScript components without frameworks
- Support ES6+ syntax and modules
- Comprehensive error handling testing

TEST ENVIRONMENTS:
- JSDOM for browser simulation
- Node.js for utility functions
- Puppeteer integration for E2E tests
- Mock service workers for API testing

COVERAGE REQUIREMENTS:
- Line coverage: 80%
- Branch coverage: 80%
- Function coverage: 80%
- Statement coverage: 80%

TEST TYPES:
1. Unit tests - Individual functions and classes
2. Component tests - UI component behavior
3. Integration tests - Component interactions
4. API tests - Frontend-backend communication
5. E2E tests - Complete user workflows
=============================================================================
*/

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Root directory for tests
  rootDir: '../../',
  
  // Test directories
  testMatch: [
    '<rootDir>/tests/frontend/**/*.test.js',
    '<rootDir>/tests/integration/**/*.test.js'
  ],
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/tests/frontend/setup.js'
  ],
  
  // Module directories
  moduleDirectories: [
    'node_modules',
    '<rootDir>/gui',
    '<rootDir>/gui/components'
  ],
  
  // Coverage configuration
  collectCoverage: true,
  coverageDirectory: '<rootDir>/coverage/frontend',
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'clover'
  ],
  
  // Coverage thresholds (80% minimum)
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    // Per-file thresholds for critical components
    '<rootDir>/gui/app.js': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    '<rootDir>/gui/components/': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  
  // Files to include in coverage
  collectCoverageFrom: [
    'gui/**/*.js',
    '!gui/node_modules/**',
    '!gui/coverage/**',
    '!**/vendor/**',
    '!**/dist/**'
  ],
  
  // Transform configuration for ES6+ modules
  transform: {
    '^.+\\.js$': 'babel-jest'
  },
  
  // Module name mapping for aliases
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/gui/$1',
    '^@components/(.*)$': '<rootDir>/gui/components/$1',
    '^@styles/(.*)$': '<rootDir>/gui/styles/$1'
  },
  
  // Mock configuration
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
  
  // Globals available in tests
  globals: {
    'ENV': 'test',
    'API_BASE_URL': 'http://localhost:5000/api'
  },
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output
  verbose: true,
  
  // Detect open handles
  detectOpenHandles: true,
  
  // Force exit after tests
  forceExit: true,
  
  // Error handling
  errorOnDeprecated: true,
  
  // Watch plugins for development
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ],
  
  // Reporter configuration
  reporters: [
    'default',
    [
      'jest-html-reporter',
      {
        pageTitle: 'DataFit Frontend Test Report',
        outputPath: '<rootDir>/coverage/frontend/test-report.html',
        includeFailureMsg: true,
        includeSuiteFailure: true
      }
    ]
  ],
  
  // Test result processor
  testResultsProcessor: '<rootDir>/tests/frontend/processors/junit-processor.js'
};
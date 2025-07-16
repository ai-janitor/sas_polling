/*
=============================================================================
JUNIT TEST RESULTS PROCESSOR
=============================================================================
Purpose: Process Jest test results and generate JUnit XML reports
Technology: Jest test results processor for CI/CD integration
Output: JUnit XML format for integration with CI/CD systems

STRICT REQUIREMENTS:
- Generate valid JUnit XML format
- Include test timing and failure details
- Support multiple test suites
- Proper error message formatting
- CI/CD system compatibility

JUNIT XML STRUCTURE:
- testsuites: Root element with summary statistics
- testsuite: Individual test suite with metadata
- testcase: Individual test cases with timing
- failure/error: Test failure details
- skipped: Skipped test information

OUTPUT FEATURES:
- Test execution timing
- Failure stack traces
- Test suite organization
- Coverage integration
- Proper XML escaping
=============================================================================
*/

const fs = require('fs');
const path = require('path');
const { create } = require('xmlbuilder2');

/**
 * Process Jest test results and generate JUnit XML report
 * @param {Object} testResults - Jest test results object
 * @returns {Object} Processed test results
 */
function processTestResults(testResults) {
  const {
    testResults: suites,
    numTotalTests,
    numPassedTests,
    numFailedTests,
    numPendingTests,
    startTime,
    success
  } = testResults;

  // Calculate total execution time
  const totalTime = suites.reduce((total, suite) => {
    return total + (suite.perfStats.end - suite.perfStats.start);
  }, 0) / 1000; // Convert to seconds

  // Create JUnit XML structure
  const junitXml = create({ version: '1.0', encoding: 'UTF-8' })
    .ele('testsuites', {
      name: 'DataFit Frontend Tests',
      tests: numTotalTests,
      failures: numFailedTests,
      errors: 0,
      skipped: numPendingTests,
      time: totalTime.toFixed(3),
      timestamp: new Date(startTime).toISOString()
    });

  // Process each test suite
  suites.forEach((suite, index) => {
    processSuite(junitXml, suite, index);
  });

  // Generate XML string
  const xmlString = junitXml.end({ prettyPrint: true });

  // Write to file
  const outputDir = path.join(process.cwd(), 'coverage', 'frontend');
  const outputFile = path.join(outputDir, 'junit.xml');

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Write JUnit XML file
  fs.writeFileSync(outputFile, xmlString, 'utf8');

  console.log(`✅ JUnit XML report generated: ${outputFile}`);

  return testResults;
}

/**
 * Process individual test suite
 * @param {Object} junitXml - XML builder root element
 * @param {Object} suite - Jest test suite results
 * @param {number} index - Suite index
 */
function processSuite(junitXml, suite, index) {
  const {
    testFilePath,
    numFailingTests,
    numPassingTests,
    numPendingTests,
    testResults: tests,
    perfStats
  } = suite;

  // Calculate suite execution time
  const suiteTime = (perfStats.end - perfStats.start) / 1000;

  // Get relative path for cleaner display
  const relativePath = path.relative(process.cwd(), testFilePath);
  
  // Create testsuite element
  const testSuite = junitXml.ele('testsuite', {
    name: relativePath,
    tests: tests.length,
    failures: numFailingTests,
    errors: 0,
    skipped: numPendingTests,
    time: suiteTime.toFixed(3),
    timestamp: new Date(perfStats.start).toISOString(),
    id: index,
    package: getPackageName(relativePath)
  });

  // Add properties if any
  testSuite.ele('properties');

  // Process each test case
  tests.forEach(test => {
    processTestCase(testSuite, test, relativePath);
  });

  // Add system-out and system-err if needed
  if (suite.console && suite.console.length > 0) {
    const systemOut = testSuite.ele('system-out');
    const consoleOutput = suite.console
      .map(log => `[${log.type.toUpperCase()}] ${log.message}`)
      .join('\n');
    systemOut.txt(escapeXml(consoleOutput));
  }

  const systemErr = testSuite.ele('system-err');
  const errors = tests
    .filter(test => test.status === 'failed')
    .map(test => test.failureMessages.join('\n'))
    .join('\n');
  
  if (errors) {
    systemErr.txt(escapeXml(errors));
  }
}

/**
 * Process individual test case
 * @param {Object} testSuite - XML testsuite element
 * @param {Object} test - Jest test result
 * @param {string} suitePath - Test suite file path
 */
function processTestCase(testSuite, test, suitePath) {
  const {
    title,
    fullName,
    status,
    duration,
    failureMessages,
    location
  } = test;

  // Create testcase element
  const testCase = testSuite.ele('testcase', {
    name: title,
    classname: generateClassName(suitePath, test.ancestorTitles),
    time: duration ? (duration / 1000).toFixed(3) : '0.000'
  });

  // Add location if available
  if (location) {
    testCase.att('file', location.path);
    testCase.att('line', location.line);
  }

  // Handle different test statuses
  switch (status) {
    case 'failed':
      const failure = testCase.ele('failure', {
        message: extractErrorMessage(failureMessages[0] || 'Test failed'),
        type: 'AssertionError'
      });
      
      const fullStackTrace = failureMessages.join('\n\n');
      failure.txt(escapeXml(fullStackTrace));
      break;

    case 'pending':
      testCase.ele('skipped', {
        message: 'Test skipped'
      });
      break;

    case 'todo':
      testCase.ele('skipped', {
        message: 'Test marked as todo'
      });
      break;

    case 'passed':
      // No additional elements needed for passed tests
      break;

    default:
      console.warn(`Unknown test status: ${status}`);
  }
}

/**
 * Generate class name from file path and test hierarchy
 * @param {string} filePath - Test file path
 * @param {Array} ancestorTitles - Test describe block titles
 * @returns {string} Generated class name
 */
function generateClassName(filePath, ancestorTitles = []) {
  // Remove file extension and convert to class-like name
  const fileName = path.basename(filePath, path.extname(filePath));
  const packageName = getPackageName(filePath);
  
  // Combine package, file, and describe blocks
  const parts = [packageName, fileName, ...ancestorTitles].filter(Boolean);
  
  return parts
    .map(part => part.replace(/[^a-zA-Z0-9]/g, '_'))
    .join('.');
}

/**
 * Extract package name from file path
 * @param {string} filePath - File path
 * @returns {string} Package name
 */
function getPackageName(filePath) {
  const pathParts = filePath.split(path.sep);
  
  // Look for tests directory and extract meaningful package
  const testsIndex = pathParts.findIndex(part => part === 'tests');
  
  if (testsIndex >= 0 && testsIndex < pathParts.length - 1) {
    return pathParts.slice(testsIndex + 1, -1).join('.');
  }
  
  // Fallback to directory containing the test file
  return pathParts.slice(-2, -1)[0] || 'tests';
}

/**
 * Extract error message from failure message
 * @param {string} failureMessage - Full failure message
 * @returns {string} Extracted error message
 */
function extractErrorMessage(failureMessage) {
  if (!failureMessage) return 'Test failed';
  
  // Try to extract just the error message (first line usually)
  const lines = failureMessage.split('\n');
  const errorLine = lines.find(line => 
    line.includes('Error:') || 
    line.includes('expect(') ||
    line.includes('AssertionError')
  );
  
  if (errorLine) {
    // Clean up the error message
    return errorLine
      .replace(/^\s*at\s+.*/, '') // Remove stack trace lines
      .replace(/^\s*Error:\s*/, '') // Remove Error: prefix
      .trim();
  }
  
  // Fallback to first non-empty line
  return lines.find(line => line.trim()) || 'Test failed';
}

/**
 * Escape XML special characters
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeXml(text) {
  if (!text) return '';
  
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, ''); // Remove control characters
}

/**
 * Add custom properties to test suite
 * @param {Object} propertiesElement - XML properties element
 * @param {Object} suite - Test suite data
 */
function addCustomProperties(propertiesElement, suite) {
  // Add coverage information if available
  if (suite.coverage) {
    propertiesElement.ele('property', {
      name: 'coverage.lines',
      value: suite.coverage.lines?.pct || '0'
    });
    
    propertiesElement.ele('property', {
      name: 'coverage.functions',
      value: suite.coverage.functions?.pct || '0'
    });
    
    propertiesElement.ele('property', {
      name: 'coverage.branches',
      value: suite.coverage.branches?.pct || '0'
    });
    
    propertiesElement.ele('property', {
      name: 'coverage.statements',
      value: suite.coverage.statements?.pct || '0'
    });
  }

  // Add test environment information
  propertiesElement.ele('property', {
    name: 'test.environment',
    value: 'jsdom'
  });
  
  propertiesElement.ele('property', {
    name: 'test.framework',
    value: 'jest'
  });
  
  propertiesElement.ele('property', {
    name: 'test.type',
    value: 'frontend'
  });
}

module.exports = processTestResults;
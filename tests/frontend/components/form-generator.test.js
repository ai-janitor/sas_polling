/*
=============================================================================
FORM GENERATOR COMPONENT TESTS
=============================================================================
Purpose: Test dynamic form generation from JSON schema and validation
Component: FormGenerator class from gui/components/form-generator.js
Coverage: Form generation, validation, input types, accessibility

TEST SCENARIOS:
1. Form generation from schema
2. Input type handling (text, dropdown, date, checkbox, radio)
3. Form validation and error display
4. Dynamic field updates and dependencies
5. Accessibility compliance
6. Data serialization and extraction
7. Form reset and cleanup
8. Edge cases and error handling

MOCK STRATEGY:
- Mock form schemas with various input types
- Mock DOM form elements and interactions
- Test validation rules and error messages
- Test form data extraction and serialization
=============================================================================
*/

describe('FormGenerator', () => {
  let formGenerator;
  let mockContainer;

  beforeEach(() => {
    // Setup DOM container
    document.body.innerHTML = `
      <div id="form-container">
        <form id="dynamic-form" class="report-form">
          <div class="form-fields"></div>
          <div class="form-actions">
            <button type="submit" class="btn btn-primary">Submit</button>
            <button type="button" class="btn btn-secondary" id="reset-form">Reset</button>
          </div>
        </form>
        <div class="form-errors"></div>
      </div>
    `;

    mockContainer = document.getElementById('form-container');

    // Import and create component instance
    const { FormGenerator } = require('../../../gui/components/form-generator.js');
    formGenerator = new FormGenerator(mockContainer);
  });

  afterEach(() => {
    if (formGenerator && formGenerator.destroy) {
      formGenerator.destroy();
    }
  });

  describe('Initialization', () => {
    test('should initialize with container element', () => {
      expect(formGenerator.container).toBe(mockContainer);
      expect(formGenerator.form).toBeDefined();
      expect(formGenerator.fieldsContainer).toBeDefined();
      expect(formGenerator.currentSchema).toBeNull();
    });

    test('should setup form element references', () => {
      const form = document.getElementById('dynamic-form');
      const fieldsContainer = document.querySelector('.form-fields');

      expect(form).toBeDefined();
      expect(fieldsContainer).toBeDefined();
    });

    test('should initialize validation state', () => {
      expect(formGenerator.validationErrors).toEqual([]);
      expect(formGenerator.isValid).toBe(true);
    });
  });

  describe('Form Generation', () => {
    test('should generate form from report schema', () => {
      const mockReport = global.generateMockReport();
      
      formGenerator.generateForm(mockReport);

      const fieldsContainer = document.querySelector('.form-fields');
      expect(fieldsContainer.children.length).toBeGreaterThan(0);
      expect(formGenerator.currentSchema).toEqual(mockReport);
    });

    test('should handle empty schema', () => {
      const emptyReport = { prompts: [] };
      
      formGenerator.generateForm(emptyReport);

      const fieldsContainer = document.querySelector('.form-fields');
      expect(fieldsContainer.innerHTML).toContain('no-fields');
    });

    test('should handle invalid schema', () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      formGenerator.generateForm(null);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Invalid report schema provided to FormGenerator'
      );

      consoleErrorSpy.mockRestore();
    });

    test('should clear existing form before generating new one', () => {
      const mockReport1 = global.generateMockReport();
      const mockReport2 = global.generateMockReport({ id: 'different_report' });

      formGenerator.generateForm(mockReport1);
      const initialFields = document.querySelector('.form-fields').children.length;

      formGenerator.generateForm(mockReport2);
      const newFields = document.querySelector('.form-fields').children.length;

      expect(newFields).toBeGreaterThan(0);
    });
  });

  describe('Input Type Generation', () => {
    test('should generate text input fields', () => {
      const mockReport = {
        prompts: [{
          text_field: {
            active: true,
            inputType: 'inputtext',
            label: 'Text Field',
            required: true,
            validation: { pattern: '^[A-Za-z]+$' }
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const textInput = document.querySelector('input[type="text"]');
      expect(textInput).toBeTruthy();
      expect(textInput.getAttribute('pattern')).toBe('^[A-Za-z]+$');
      expect(textInput.hasAttribute('required')).toBe(true);
    });

    test('should generate dropdown select fields', () => {
      const mockReport = {
        prompts: [{
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
      };

      formGenerator.generateForm(mockReport);

      const selectElement = document.querySelector('select');
      expect(selectElement).toBeTruthy();
      expect(selectElement.children.length).toBe(3); // Including default option
    });

    test('should generate date input fields', () => {
      const mockReport = {
        prompts: [{
          date_field: {
            active: true,
            inputType: 'date',
            label: 'Date Field',
            validation: {
              min: '2023-01-01',
              max: '2023-12-31'
            }
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const dateInput = document.querySelector('input[type="date"]');
      expect(dateInput).toBeTruthy();
      expect(dateInput.getAttribute('min')).toBe('2023-01-01');
      expect(dateInput.getAttribute('max')).toBe('2023-12-31');
    });

    test('should generate checkbox input fields', () => {
      const mockReport = {
        prompts: [{
          checkbox_field: {
            active: true,
            inputType: 'checkbox',
            label: 'Checkbox Field'
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const checkboxInput = document.querySelector('input[type="checkbox"]');
      expect(checkboxInput).toBeTruthy();
    });

    test('should generate radio button groups', () => {
      const mockReport = {
        prompts: [{
          radio_field: {
            active: true,
            inputType: 'radio',
            label: 'Radio Field',
            options: [
              { value: 'yes', label: 'Yes' },
              { value: 'no', label: 'No' }
            ]
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const radioInputs = document.querySelectorAll('input[type="radio"]');
      expect(radioInputs.length).toBe(2);
      expect(radioInputs[0].getAttribute('name')).toBe('radio_field');
      expect(radioInputs[1].getAttribute('name')).toBe('radio_field');
    });

    test('should generate hidden input fields', () => {
      const mockReport = {
        prompts: [{
          hidden_field: {
            active: true,
            inputType: 'hidden',
            value: 'hidden_value'
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const hiddenInput = document.querySelector('input[type="hidden"]');
      expect(hiddenInput).toBeTruthy();
      expect(hiddenInput.value).toBe('hidden_value');
    });

    test('should skip inactive fields', () => {
      const mockReport = {
        prompts: [{
          inactive_field: {
            active: false,
            inputType: 'inputtext',
            label: 'Inactive Field'
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const fieldsContainer = document.querySelector('.form-fields');
      expect(fieldsContainer.children.length).toBe(0);
    });
  });

  describe('Form Validation', () => {
    beforeEach(() => {
      const mockReport = global.generateMockReport();
      formGenerator.generateForm(mockReport);
    });

    test('should validate required fields', () => {
      const errors = formGenerator.validateForm();

      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].field).toBe('test_field');
      expect(errors[0].message).toContain('required');
    });

    test('should validate field patterns', () => {
      const textInput = document.querySelector('input[type="text"]');
      textInput.value = '123'; // Invalid pattern (should be letters only)

      const errors = formGenerator.validateForm();

      expect(errors.some(error => 
        error.field === 'test_field' && error.message.includes('pattern')
      )).toBe(true);
    });

    test('should validate field length constraints', () => {
      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'ab'; // Too short (min 3 characters)

      const errors = formGenerator.validateForm();

      expect(errors.some(error => 
        error.field === 'test_field' && error.message.includes('minimum')
      )).toBe(true);
    });

    test('should return empty errors for valid form', () => {
      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'ValidInput';

      const errors = formGenerator.validateForm();

      expect(errors).toEqual([]);
    });

    test('should display validation errors in UI', () => {
      formGenerator.validateForm();
      formGenerator.displayValidationErrors();

      const errorContainer = document.querySelector('.form-errors');
      expect(errorContainer.children.length).toBeGreaterThan(0);
    });

    test('should clear validation errors', () => {
      formGenerator.validateForm();
      formGenerator.displayValidationErrors();
      formGenerator.clearValidationErrors();

      const errorContainer = document.querySelector('.form-errors');
      expect(errorContainer.children.length).toBe(0);
    });
  });

  describe('Form Data Extraction', () => {
    beforeEach(() => {
      const mockReport = global.generateMockReport();
      formGenerator.generateForm(mockReport);
    });

    test('should extract form data as JSON', () => {
      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'TestValue';

      const formData = formGenerator.getFormData();

      expect(formData).toEqual({ test_field: 'TestValue' });
    });

    test('should handle checkbox values', () => {
      const mockReport = {
        prompts: [{
          checkbox_field: {
            active: true,
            inputType: 'checkbox',
            label: 'Checkbox Field'
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const checkboxInput = document.querySelector('input[type="checkbox"]');
      checkboxInput.checked = true;

      const formData = formGenerator.getFormData();

      expect(formData.checkbox_field).toBe(true);
    });

    test('should handle radio button values', () => {
      const mockReport = {
        prompts: [{
          radio_field: {
            active: true,
            inputType: 'radio',
            label: 'Radio Field',
            options: [
              { value: 'yes', label: 'Yes' },
              { value: 'no', label: 'No' }
            ]
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const radioInput = document.querySelector('input[type="radio"][value="yes"]');
      radioInput.checked = true;

      const formData = formGenerator.getFormData();

      expect(formData.radio_field).toBe('yes');
    });

    test('should handle empty form data', () => {
      const formData = formGenerator.getFormData();

      expect(formData.test_field).toBe('');
    });
  });

  describe('Form Reset', () => {
    beforeEach(() => {
      const mockReport = global.generateMockReport();
      formGenerator.generateForm(mockReport);
    });

    test('should reset all form fields', () => {
      const textInput = document.querySelector('input[type="text"]');
      textInput.value = 'TestValue';

      formGenerator.resetForm();

      expect(textInput.value).toBe('');
    });

    test('should clear validation errors on reset', () => {
      formGenerator.validateForm();
      formGenerator.displayValidationErrors();
      formGenerator.resetForm();

      const errorContainer = document.querySelector('.form-errors');
      expect(errorContainer.children.length).toBe(0);
    });

    test('should reset form validation state', () => {
      formGenerator.validateForm();
      formGenerator.resetForm();

      expect(formGenerator.validationErrors).toEqual([]);
      expect(formGenerator.isValid).toBe(true);
    });
  });

  describe('Field Dependencies', () => {
    test('should handle conditional field display', () => {
      const mockReport = {
        prompts: [{
          condition_field: {
            active: true,
            inputType: 'dropdown',
            label: 'Condition Field',
            options: [
              { value: 'show', label: 'Show Dependent' },
              { value: 'hide', label: 'Hide Dependent' }
            ]
          },
          dependent_field: {
            active: true,
            inputType: 'inputtext',
            label: 'Dependent Field',
            dependencies: {
              condition_field: 'show'
            }
          }
        }]
      };

      formGenerator.generateForm(mockReport);

      const conditionSelect = document.querySelector('select');
      const dependentField = document.querySelector('input[name="dependent_field"]').closest('.form-group');

      // Initially hidden
      expect(dependentField.style.display).toBe('none');

      // Show when condition met
      conditionSelect.value = 'show';
      global.simulateEvent(conditionSelect, 'change');

      expect(dependentField.style.display).toBe('block');
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      const mockReport = global.generateMockReport();
      formGenerator.generateForm(mockReport);
    });

    test('should have proper labels for all inputs', () => {
      const textInput = document.querySelector('input[type="text"]');
      const label = document.querySelector(`label[for="${textInput.id}"]`);

      expect(label).toBeTruthy();
      expect(label.textContent).toContain('Test Field');
    });

    test('should mark required fields appropriately', () => {
      const textInput = document.querySelector('input[type="text"]');
      const label = document.querySelector(`label[for="${textInput.id}"]`);

      expect(textInput.hasAttribute('required')).toBe(true);
      expect(textInput.getAttribute('aria-required')).toBe('true');
      expect(label.innerHTML).toContain('*');
    });

    test('should associate error messages with fields', () => {
      formGenerator.validateForm();
      formGenerator.displayValidationErrors();

      const textInput = document.querySelector('input[type="text"]');
      const errorId = textInput.getAttribute('aria-describedby');
      const errorElement = document.getElementById(errorId);

      expect(errorElement).toBeTruthy();
      expect(errorElement.getAttribute('role')).toBe('alert');
    });

    test('should provide helpful input descriptions', () => {
      const textInput = document.querySelector('input[type="text"]');
      const helpText = document.querySelector(`#${textInput.id}-help`);

      expect(helpText).toBeTruthy();
      expect(textInput.getAttribute('aria-describedby')).toContain(`${textInput.id}-help`);
    });
  });

  describe('Dynamic Updates', () => {
    test('should update field values programmatically', () => {
      const mockReport = global.generateMockReport();
      formGenerator.generateForm(mockReport);

      formGenerator.setFieldValue('test_field', 'NewValue');

      const textInput = document.querySelector('input[type="text"]');
      expect(textInput.value).toBe('NewValue');
    });

    test('should handle setting values for non-existent fields', () => {
      const mockReport = global.generateMockReport();
      formGenerator.generateForm(mockReport);

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      formGenerator.setFieldValue('non_existent_field', 'value');

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Field non_existent_field not found in form'
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('Error Handling', () => {
    test('should handle missing container element', () => {
      expect(() => {
        new FormGenerator(null);
      }).toThrow('Container element is required');
    });

    test('should handle malformed field schemas', () => {
      const invalidReport = {
        prompts: [{
          invalid_field: {
            // Missing required properties
          }
        }]
      };

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      
      formGenerator.generateForm(invalidReport);

      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Memory Management', () => {
    test('should clean up event listeners on destroy', () => {
      const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener');
      
      formGenerator.destroy();

      expect(removeEventListenerSpy).toHaveBeenCalled();
      removeEventListenerSpy.mockRestore();
    });

    test('should clear form references on destroy', () => {
      formGenerator.destroy();

      expect(formGenerator.currentSchema).toBeNull();
      expect(formGenerator.validationErrors).toEqual([]);
    });
  });
});
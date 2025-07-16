/*
=============================================================================
DYNAMIC FORM GENERATOR COMPONENT
=============================================================================
Purpose: Generate forms dynamically from JSON report schema
Technology: Vanilla JavaScript with template literals
Parent: app.js

STRICT REQUIREMENTS:
- Support all input types: inputtext, dropdown, date, checkbox, radio
- Real-time validation with visual feedback
- Conditional field display based on dependencies
- Accessibility compliance (labels, ARIA attributes)
- Mobile-responsive layout

INPUT TYPE SUPPORT:
1. inputtext: Text input with pattern validation
2. dropdown: Select with options from schema
3. date: Date picker with min/max constraints
4. checkbox: Boolean toggles
5. radio: Single selection from options
6. hidden: Hidden fields (e.g., username)

VALIDATION FEATURES:
- Required field validation
- Pattern matching for text inputs
- Date range validation
- Custom validation rules from schema
- Real-time feedback with error messages

FORM STRUCTURE:
Generated form includes:
- Field labels with required indicators
- Input controls based on schema
- Validation error display areas
- Submit button with loading states
- Reset functionality

METHODS:
- generateForm(reportSchema): Create form from report definition
- validateForm(): Validate all fields and return errors
- getFormData(): Extract form data as JSON
- resetForm(): Clear all fields and errors
- setFieldValue(fieldName, value): Programmatically set field values
=============================================================================
*/

class FormGenerator {
    constructor(app) {
        this.app = app;
        this.currentSchema = null;
        this.formData = {};
        this.validationErrors = {};
        
        this.formContainer = document.getElementById('form-fields');
        this.debounceTimeouts = new Map();
    }

    generateForm(report) {
        if (!report || !report.prompts) {
            console.error('Invalid report schema:', report);
            return;
        }

        this.currentSchema = report;
        this.formData = {};
        this.validationErrors = {};
        
        const fieldsHtml = this.generateFields(report.prompts);
        this.formContainer.innerHTML = fieldsHtml;
        
        this.setupFieldEventListeners();
        this.addJobNameField();
    }

    addJobNameField() {
        const jobNameHtml = `
            <div class="form-group">
                <label for="job_name" class="form-label">Job Name</label>
                <input type="text" 
                       id="job_name" 
                       name="job_name" 
                       class="form-input" 
                       placeholder="Enter a name for this job"
                       value="${this.currentSchema.name} - ${new Date().toLocaleString()}">
                <div class="form-help">Provide a descriptive name for this job</div>
            </div>
        `;
        
        this.formContainer.insertAdjacentHTML('afterbegin', jobNameHtml);
    }

    generateFields(prompts) {
        return prompts.map(promptGroup => {
            return Object.entries(promptGroup).map(([fieldName, config]) => {
                if (config.hide || !config.active) {
                    return '';
                }
                
                return this.generateField(fieldName, config);
            }).join('');
        }).join('');
    }

    generateField(fieldName, config) {
        const fieldId = `field_${fieldName}`;
        const isRequired = config.required;
        const hasError = this.validationErrors[fieldName];
        
        let inputHtml = '';
        
        switch (config.inputType) {
            case 'inputtext':
                inputHtml = this.generateTextInput(fieldId, fieldName, config);
                break;
            case 'dropdown':
                inputHtml = this.generateDropdown(fieldId, fieldName, config);
                break;
            case 'date':
                inputHtml = this.generateDateInput(fieldId, fieldName, config);
                break;
            case 'checkbox':
                inputHtml = this.generateCheckbox(fieldId, fieldName, config);
                break;
            case 'radio':
                inputHtml = this.generateRadio(fieldId, fieldName, config);
                break;
            case 'hidden':
                return this.generateHiddenInput(fieldName, config);
            default:
                inputHtml = this.generateTextInput(fieldId, fieldName, config);
        }

        return `
            <div class="form-group" data-field="${fieldName}">
                <label for="${fieldId}" class="form-label ${isRequired ? 'required' : ''}">
                    ${this.escapeHtml(config.label || fieldName)}
                </label>
                ${inputHtml}
                ${config.help ? `<div class="form-help">${this.escapeHtml(config.help)}</div>` : ''}
                <div class="form-error" id="${fieldId}_error" style="display: none;">
                    <i class="fas fa-exclamation-circle"></i>
                    <span class="error-message"></span>
                </div>
            </div>
        `;
    }

    generateTextInput(fieldId, fieldName, config) {
        const value = this.formData[fieldName] || config.defaultValue || '';
        const validation = config.validation || {};
        
        return `
            <input type="text" 
                   id="${fieldId}" 
                   name="${fieldName}" 
                   class="form-input" 
                   value="${this.escapeHtml(value)}"
                   ${config.required ? 'required' : ''}
                   ${validation.pattern ? `pattern="${validation.pattern}"` : ''}
                   ${validation.minLength ? `minlength="${validation.minLength}"` : ''}
                   ${validation.maxLength ? `maxlength="${validation.maxLength}"` : ''}
                   ${config.placeholder ? `placeholder="${this.escapeHtml(config.placeholder)}"` : ''}
                   aria-describedby="${fieldId}_error">
        `;
    }

    generateDropdown(fieldId, fieldName, config) {
        const value = this.formData[fieldName] || config.defaultValue || '';
        const options = config.options || [];
        
        const optionsHtml = options.map(option => {
            const optionValue = typeof option === 'object' ? option.value : option;
            const optionLabel = typeof option === 'object' ? option.label : option;
            const selected = optionValue === value ? 'selected' : '';
            
            return `<option value="${this.escapeHtml(optionValue)}" ${selected}>
                ${this.escapeHtml(optionLabel)}
            </option>`;
        }).join('');

        return `
            <select id="${fieldId}" 
                    name="${fieldName}" 
                    class="form-select"
                    ${config.required ? 'required' : ''}
                    aria-describedby="${fieldId}_error">
                ${!config.required ? '<option value="">Select an option</option>' : ''}
                ${optionsHtml}
            </select>
        `;
    }

    generateDateInput(fieldId, fieldName, config) {
        const value = this.formData[fieldName] || config.defaultValue || '';
        const validation = config.validation || {};
        
        return `
            <input type="date" 
                   id="${fieldId}" 
                   name="${fieldName}" 
                   class="form-input" 
                   value="${this.escapeHtml(value)}"
                   ${config.required ? 'required' : ''}
                   ${validation.minDate ? `min="${validation.minDate}"` : ''}
                   ${validation.maxDate ? `max="${validation.maxDate}"` : ''}
                   aria-describedby="${fieldId}_error">
        `;
    }

    generateCheckbox(fieldId, fieldName, config) {
        const value = this.formData[fieldName] || config.defaultValue || false;
        const checked = value ? 'checked' : '';
        
        return `
            <div class="checkbox-group">
                <div class="checkbox-item">
                    <input type="checkbox" 
                           id="${fieldId}" 
                           name="${fieldName}" 
                           value="true"
                           ${checked}
                           aria-describedby="${fieldId}_error">
                    <label for="${fieldId}">${this.escapeHtml(config.checkboxLabel || 'Enable')}</label>
                </div>
            </div>
        `;
    }

    generateRadio(fieldId, fieldName, config) {
        const value = this.formData[fieldName] || config.defaultValue || '';
        const options = config.options || [];
        
        const optionsHtml = options.map((option, index) => {
            const optionValue = typeof option === 'object' ? option.value : option;
            const optionLabel = typeof option === 'object' ? option.label : option;
            const radioId = `${fieldId}_${index}`;
            const checked = optionValue === value ? 'checked' : '';
            
            return `
                <div class="radio-item">
                    <input type="radio" 
                           id="${radioId}" 
                           name="${fieldName}" 
                           value="${this.escapeHtml(optionValue)}"
                           ${checked}
                           ${config.required ? 'required' : ''}>
                    <label for="${radioId}">${this.escapeHtml(optionLabel)}</label>
                </div>
            `;
        }).join('');

        return `
            <div class="radio-group" aria-describedby="${fieldId}_error">
                ${optionsHtml}
            </div>
        `;
    }

    generateHiddenInput(fieldName, config) {
        const value = this.formData[fieldName] || config.defaultValue || config.value || '';
        return `
            <input type="hidden" 
                   name="${fieldName}" 
                   value="${this.escapeHtml(value)}">
        `;
    }

    setupFieldEventListeners() {
        const inputs = this.formContainer.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', this.handleFieldBlur.bind(this));
            input.addEventListener('input', this.handleFieldInput.bind(this));
            input.addEventListener('change', this.handleFieldChange.bind(this));
        });
    }

    handleFieldInput(e) {
        const fieldName = e.target.name;
        this.updateFormData(fieldName, e.target);
        
        this.clearTimeout(fieldName);
        this.debounceTimeouts.set(fieldName, setTimeout(() => {
            this.validateField(fieldName);
        }, 300));
    }

    handleFieldBlur(e) {
        const fieldName = e.target.name;
        this.updateFormData(fieldName, e.target);
        this.validateField(fieldName);
    }

    handleFieldChange(e) {
        const fieldName = e.target.name;
        this.updateFormData(fieldName, e.target);
        this.validateField(fieldName);
    }

    updateFormData(fieldName, element) {
        if (element.type === 'checkbox') {
            this.formData[fieldName] = element.checked;
        } else if (element.type === 'radio') {
            if (element.checked) {
                this.formData[fieldName] = element.value;
            }
        } else {
            this.formData[fieldName] = element.value;
        }
    }

    validateField(fieldName) {
        const config = this.getFieldConfig(fieldName);
        if (!config) return;

        const value = this.formData[fieldName];
        const errors = [];

        if (config.required && (!value || value === '')) {
            errors.push('This field is required');
        }

        if (value && config.validation) {
            const validation = config.validation;
            
            if (validation.pattern) {
                const regex = new RegExp(validation.pattern);
                if (!regex.test(value)) {
                    errors.push('Invalid format');
                }
            }
            
            if (validation.minLength && value.length < validation.minLength) {
                errors.push(`Minimum length is ${validation.minLength} characters`);
            }
            
            if (validation.maxLength && value.length > validation.maxLength) {
                errors.push(`Maximum length is ${validation.maxLength} characters`);
            }
            
            if (validation.min && parseFloat(value) < validation.min) {
                errors.push(`Minimum value is ${validation.min}`);
            }
            
            if (validation.max && parseFloat(value) > validation.max) {
                errors.push(`Maximum value is ${validation.max}`);
            }
        }

        this.setFieldError(fieldName, errors.length > 0 ? errors[0] : null);
    }

    getFieldConfig(fieldName) {
        if (!this.currentSchema || !this.currentSchema.prompts) {
            return null;
        }

        for (const promptGroup of this.currentSchema.prompts) {
            if (promptGroup[fieldName]) {
                return promptGroup[fieldName];
            }
        }
        
        return null;
    }

    setFieldError(fieldName, errorMessage) {
        const fieldGroup = this.formContainer.querySelector(`[data-field="${fieldName}"]`);
        if (!fieldGroup) return;

        const input = fieldGroup.querySelector('input, select, textarea');
        const errorDiv = fieldGroup.querySelector('.form-error');
        const errorSpan = errorDiv.querySelector('.error-message');

        if (errorMessage) {
            this.validationErrors[fieldName] = errorMessage;
            input.classList.add('error');
            errorSpan.textContent = errorMessage;
            errorDiv.style.display = 'flex';
            input.setAttribute('aria-invalid', 'true');
        } else {
            delete this.validationErrors[fieldName];
            input.classList.remove('error');
            errorDiv.style.display = 'none';
            input.setAttribute('aria-invalid', 'false');
        }
    }

    validateForm() {
        const errors = [];
        
        if (!this.currentSchema || !this.currentSchema.prompts) {
            return errors;
        }

        for (const promptGroup of this.currentSchema.prompts) {
            for (const [fieldName, config] of Object.entries(promptGroup)) {
                if (config.hide || !config.active) continue;
                
                this.validateField(fieldName);
                
                if (this.validationErrors[fieldName]) {
                    errors.push({
                        field: fieldName,
                        message: this.validationErrors[fieldName]
                    });
                }
            }
        }

        return errors;
    }

    getFormData() {
        const data = { ...this.formData };
        
        const jobNameInput = document.getElementById('job_name');
        if (jobNameInput) {
            data.job_name = jobNameInput.value;
        }

        return data;
    }

    setFieldValue(fieldName, value) {
        this.formData[fieldName] = value;
        
        const input = this.formContainer.querySelector(`[name="${fieldName}"]`);
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = Boolean(value);
            } else if (input.type === 'radio') {
                const radioInputs = this.formContainer.querySelectorAll(`[name="${fieldName}"]`);
                radioInputs.forEach(radio => {
                    radio.checked = radio.value === value;
                });
            } else {
                input.value = value;
            }
            
            this.validateField(fieldName);
        }
    }

    resetForm() {
        this.formData = {};
        this.validationErrors = {};
        
        const inputs = this.formContainer.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
            
            input.classList.remove('error');
            input.setAttribute('aria-invalid', 'false');
        });
        
        const errorDivs = this.formContainer.querySelectorAll('.form-error');
        errorDivs.forEach(div => {
            div.style.display = 'none';
        });
        
        this.clearAllTimeouts();
    }

    clearTimeout(fieldName) {
        const timeoutId = this.debounceTimeouts.get(fieldName);
        if (timeoutId) {
            clearTimeout(timeoutId);
            this.debounceTimeouts.delete(fieldName);
        }
    }

    clearAllTimeouts() {
        this.debounceTimeouts.forEach((timeoutId) => {
            clearTimeout(timeoutId);
        });
        this.debounceTimeouts.clear();
    }

    escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') {
            return String(unsafe);
        }
        
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    destroy() {
        this.clearAllTimeouts();
    }
}
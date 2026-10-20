/* ========================================
   Образовательный центр «Начало»
   Обработка форм (forms.js)
   ======================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // --- Lead Form Handler ---
    const leadForm = document.getElementById('lead-form');
    
    if (leadForm) {
        leadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
            
            // Send data
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Redirect to thank you page
                    window.location.href = '/thankyou.html';
                } else {
                    showFormError(leadForm, data.message || 'Произошла ошибка при отправке. Попробуйте позже.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFormError(leadForm, 'Произошла ошибка при отправке. Попробуйте позже.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            });
        });
    }
    
    // --- Callback Form Handler ---
    const callbackForms = document.querySelectorAll('.modal-form');
    
    callbackForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            const modal = form.closest('.modal');
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
            
            // Send data
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close modal
                    if (modal) {
                        modal.classList.remove('active');
                        document.body.style.overflow = '';
                    }

                    // Redirect to thank you page
                    window.location.href = '/thankyou.html';

                    // Reset form
                    form.reset();
                } else {
                    showFormError(form, data.message || 'Произошла ошибка при отправке. Попробуйте позже.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFormError(form, 'Произошла ошибка при отправке. Попробуйте позже.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            });
        });
    });
    
    // --- Helper: Show Form Error ---
    function showFormError(form, message) {
        // Remove existing error messages
        const existingError = form.querySelector('.form-error-message');
        if (existingError) {
            existingError.remove();
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error-message';
        errorDiv.style.cssText = 'color: #d32f2f; font-size: 0.9rem; margin-bottom: 16px; padding: 12px; background: #ffebee; border-radius: 4px;';
        errorDiv.textContent = message;
        
        form.insertBefore(errorDiv, form.firstChild);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    
    // --- Helper: Show Success Message ---
    function showFormSuccess(form, message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'form-success-message';
        successDiv.style.cssText = 'color: #2e7d32; font-size: 0.9rem; margin-bottom: 16px; padding: 12px; background: #e8f5e9; border-radius: 4px;';
        successDiv.innerHTML = '<i class="fa fa-check-circle"></i> ' + message;
        
        form.insertBefore(successDiv, form.firstChild);
        
        setTimeout(() => {
            successDiv.remove();
        }, 5000);
    }
    
    // --- Track Form Abandonment (Analytics) ---
    const trackedForms = document.querySelectorAll('form');
    
    trackedForms.forEach(form => {
        let formStarted = false;
        
        form.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('input', function() {
                formStarted = true;
            });
        });
        
        form.addEventListener('submit', function() {
            formStarted = false;
            // Track conversion in analytics
            if (typeof ym !== 'undefined' && window.YANDEX_METRIKA_ID) {
                ym(window.YANDEX_METRIKA_ID, 'reachGoal', 'form_submit');
            }
            if (typeof gtag !== 'undefined') {
                gtag('event', 'form_submit', {
                    'event_category': 'forms',
                    'event_label': form.id || 'unnamed'
                });
            }
        });

        window.addEventListener('beforeunload', function() {
            if (formStarted) {
                // Track form abandonment
                if (typeof ym !== 'undefined' && window.YANDEX_METRIKA_ID) {
                    ym(window.YANDEX_METRIKA_ID, 'reachGoal', 'form_abandon');
                }
            }
        });
    });
    
    // --- Auto-hide Error Messages on Input ---
    document.querySelectorAll('form').forEach(form => {
        form.querySelectorAll('input, select, textarea').forEach(field => {
            field.addEventListener('input', function() {
                this.classList.remove('error');
                const error = form.querySelector('.form-error-message');
                if (error) {
                    error.remove();
                }
            });
        });
    });
    
});

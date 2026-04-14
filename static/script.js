document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form[action="/"]');
    const registerForm = document.querySelector('form[action="/registration"]');
    const resetForm = document.querySelector('.form form');

    if (loginForm) {
        loginForm.addEventListener('submit', handleAjaxSubmit);
    }
    if (registerForm) {
        registerForm.addEventListener('submit', handleAjaxSubmit);
    }
    if (resetForm && resetForm.querySelector('input[type="email"]')) {
        resetForm.addEventListener('submit', handleAjaxSubmit);
    }

    addLiveValidation();
});

function handleAjaxSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const url = form.action;
    const formData = new FormData(form);
    
    clearErrors(form);
    clearBanner(form);
    
    if (!validateFormBeforeSubmit(form)) {
        return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.redirect) {
                window.location.href = data.redirect;
            } else if (data.message) {
                showBanner(form, data.message, 'success');
                form.reset();
            }
        } else {
            if (data.errors) {
                showBanner(form, data.errors.join('<br>'), 'error');
            }
        }
    })
    .catch(error => {
        showBanner(form, 'Ошибка соединения с сервером', 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    });
}

function validateFormBeforeSubmit(form) {
    let isValid = true;
    const email = form.querySelector('input[name="email"]');
    const password = form.querySelector('input[name="password"]');
    const name = form.querySelector('input[name="name"]');
    
    if (email && !validateEmail(email.value)) {
        showError(email, 'Введите корректный email');
        isValid = false;
    }
    
    if (password) {
        if (form.action.includes('registration')) {
            const errors = validatePassword(password.value);
            if (errors.length > 0) {
                showError(password, errors.join('; '));
                isValid = false;
            }
        } else {
            if (password.value.trim() === '') {
                showError(password, 'Пароль не может быть пустым');
                isValid = false;
            }
        }
    }
    
    if (name) {
        const nameVal = name.value.trim();
        if (nameVal === '') {
            showError(name, 'Имя обязательно');
            isValid = false;
        } else if (nameVal.length < 2) {
            showError(name, 'Имя должно содержать минимум 2 символа');
            isValid = false;
        } else if (!/^[a-zA-Zа-яА-ЯёЁ\s\-]+$/.test(nameVal)) {
            showError(name, 'Только буквы, пробелы и дефис');
            isValid = false;
        }
    }
    
    return isValid;
}

function validatePassword(pwd) {
    const errors = [];
    if (pwd.length < 8) errors.push('Минимум 8 символов');
    if (!/[A-Z]/.test(pwd)) errors.push('Заглавная буква (A-Z)');
    if (!/[a-z]/.test(pwd)) errors.push('Строчная буква (a-z)');
    if (!/[0-9]/.test(pwd)) errors.push('Цифра');
    if (!/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+$/.test(pwd)) {
        errors.push('Только латиница, цифры и спецсимволы');
    }
    if (/\s/.test(pwd)) errors.push('Без пробелов');
    return errors;
}

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email).toLowerCase());
}

function showError(input, message) {
    input.style.border = '2px solid #ff6b6b';
    input.style.boxShadow = '0 0 10px rgba(255, 107, 107, 0.3)';
    
    let errorSpan = input.parentNode.querySelector('.error-message');
    if (!errorSpan) {
        errorSpan = document.createElement('span');
        errorSpan.className = 'error-message';
        errorSpan.style.cssText = `
            display: block;
            color: #ff6b6b;
            font-size: 12px;
            margin-top: 5px;
            margin-left: 15px;
        `;
        input.parentNode.appendChild(errorSpan);
    }
    errorSpan.textContent = message;
}

function clearErrors(form) {
    form.querySelectorAll('input').forEach(input => {
        input.style.border = '';
        input.style.boxShadow = '';
    });
    form.querySelectorAll('.error-message').forEach(el => el.remove());
}

function showBanner(form, message, type) {
    const existingBanner = form.querySelector('.ajax-banner');
    if (existingBanner) existingBanner.remove();
    
    const banner = document.createElement('div');
    banner.className = 'ajax-banner';
    banner.style.cssText = `
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 14px;
    `;
    
    if (type === 'error') {
        banner.style.background = 'rgba(255, 80, 80, 0.15)';
        banner.style.borderLeft = '4px solid #ff6b6b';
        banner.style.color = '#ff8a8a';
        banner.innerHTML = '<i class="fas fa-exclamation-circle" style="margin-right: 8px;"></i>' + message;
    } else {
        banner.style.background = 'rgba(80, 200, 120, 0.15)';
        banner.style.borderLeft = '4px solid #6fcf97';
        banner.style.color = '#6fcf97';
        banner.innerHTML = '<i class="fas fa-check-circle" style="margin-right: 8px;"></i>' + message;
    }
    
    form.insertBefore(banner, form.firstChild);
}

function clearBanner(form) {
    const banner = form.querySelector('.ajax-banner');
    if (banner) banner.remove();
}

function addLiveValidation() {
    document.querySelectorAll('input[type="email"], input[name="email"]').forEach(input => {
        input.addEventListener('input', function() {
            const isValid = validateEmail(this.value);
            updateLiveFieldStyle(this, !isValid && this.value.length > 0, 'Некорректный email');
        });
    });

    const registerPassword = document.querySelector('form[action="/registration"] input[name="password"]');
    if (registerPassword) {
        registerPassword.addEventListener('input', function() {
            const errors = validatePassword(this.value);
            const hasErrors = errors.length > 0;
            updateLiveFieldStyle(this, hasErrors && this.value.length > 0, errors.join('; '));
            if (!hasErrors && this.value.length >= 8) {
                this.style.border = '2px solid #6fcf97';
            }
        });
    }

    const nameInput = document.querySelector('form[action="/registration"] input[name="name"]');
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            const val = this.value.trim();
            let error = null;
            if (val.length > 0 && val.length < 2) error = 'Минимум 2 символа';
            else if (val.length > 0 && !/^[a-zA-Zа-яА-ЯёЁ\s\-]+$/.test(val)) error = 'Недопустимые символы';
            updateLiveFieldStyle(this, !!error, error);
        });
    }
}

function updateLiveFieldStyle(input, isError, message) {
    const parent = input.parentNode;
    let errorSpan = parent.querySelector('.error-message');
    
    if (isError) {
        input.style.border = '2px solid #ff6b6b';
        if (!errorSpan) {
            errorSpan = document.createElement('span');
            errorSpan.className = 'error-message';
            errorSpan.style.cssText = 'display: block; color: #ff6b6b; font-size: 12px; margin-top: 5px; margin-left: 15px;';
            parent.appendChild(errorSpan);
        }
        errorSpan.textContent = message;
    } else {
        input.style.border = input.value.length > 0 ? '2px solid #6fcf97' : '';
        if (errorSpan) errorSpan.remove();
    }
}
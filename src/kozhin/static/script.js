document.addEventListener(
    'DOMContentLoaded',
    function () {

        const loginForm =
            document.querySelector(
                'form[action="/"]'
            );

        const registerForm =
            document.querySelector(
                'form[action="/registration"]'
            );

        const resetForm =
            document.querySelector(
                'form[action="/password_vosst"]'
            );


        if (loginForm) {

            loginForm.addEventListener(
                'submit',
                handleAjaxSubmit
            );
        }


        if (registerForm) {

            registerForm.addEventListener(
                'submit',
                handleAjaxSubmit
            );
        }


        if (resetForm) {

            resetForm.addEventListener(
                'submit',
                handleAjaxSubmit
            );
        }


        addLiveValidation();
    }
);


async function handleAjaxSubmit(e) {

    e.preventDefault();


    const form = e.target;

    const url = form.action;

    const formData =
        new FormData(form);


    clearErrors(form);

    clearBanner(form);


    if (
        !validateFormBeforeSubmit(form)
    ) {

        return;
    }


    const submitBtn =
        form.querySelector(
            'button[type="submit"]'
        );


    if (!submitBtn) {

        return;
    }


    const originalBtnText =
        submitBtn.innerHTML;


    submitBtn.disabled = true;

    submitBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Отправка...';


    try {

        const response =
            await fetch(
                url,
                {

                    method: 'POST',

                    headers: {

                        'X-Requested-With':
                            'XMLHttpRequest',

                        'Accept':
                            'application/json'
                    },

                    body: formData
                }
            );


        const contentType =
            response.headers.get(
                'content-type'
            ) || '';


        if (
            !contentType.includes(
                'application/json'
            )
        ) {

            throw new Error(
                'Сервер вернул ответ не в формате JSON'
            );
        }


        const data =
            await response.json();


        if (data.success) {


            if (data.redirect) {

                window.location.href =
                    data.redirect;

                return;
            }


            if (data.message) {

                showBanner(
                    form,
                    data.message,
                    'success'
                );

                form.reset();

                resetFormStyles(
                    form
                );
            }


            return;
        }


        if (
            data.errors
            && Array.isArray(
                data.errors
            )
        ) {

            showBanner(
                form,
                data.errors.join('<br>'),
                'error'
            );

        } else if (
            data.error
        ) {

            showBanner(
                form,
                data.error,
                'error'
            );

        } else if (
            data.message
        ) {

            showBanner(
                form,
                data.message,
                'error'
            );

        } else {

            showBanner(
                form,
                'Произошла неизвестная ошибка',
                'error'
            );
        }


    } catch (error) {

        console.error(
            'Ошибка при отправке формы:',
            error
        );


        showBanner(
            form,
            'Не удалось обработать ответ сервера. Попробуйте ещё раз.',
            'error'
        );


    } finally {

        submitBtn.disabled = false;

        submitBtn.innerHTML =
            originalBtnText;
    }
}


function validateFormBeforeSubmit(
    form
) {

    let isValid = true;


    const email =
        form.querySelector(
            'input[name="email"]'
        );


    const password =
        form.querySelector(
            'input[name="password"]'
        );


    const name =
        form.querySelector(
            'input[name="name"]'
        );


    const surname =
        form.querySelector(
            'input[name="surname"]'
        );


    // EMAIL
    if (email) {

        const emailValue =
            email.value.trim();


        if (
            emailValue === ''
        ) {

            showError(
                email,
                'Email обязателен'
            );

            isValid = false;

        } else if (
            !validateEmail(
                emailValue
            )
        ) {

            showError(
                email,
                'Введите корректный email'
            );

            isValid = false;
        }
    }


    // PASSWORD
    if (password) {


        if (
            form.action.includes(
                '/registration'
            )
        ) {

            const errors =
                validatePassword(
                    password.value
                );


            if (
                errors.length > 0
            ) {

                showError(
                    password,
                    errors.join('; ')
                );

                isValid = false;
            }


        } else {


            if (
                password.value.trim()
                === ''
            ) {

                showError(
                    password,
                    'Пароль не может быть пустым'
                );

                isValid = false;
            }
        }
    }


    // NAME
    if (name) {

        const nameVal =
            name.value.trim();


        if (
            nameVal === ''
        ) {

            showError(
                name,
                'Имя обязательно'
            );

            isValid = false;

        } else if (
            nameVal.length < 2
        ) {

            showError(
                name,
                'Имя должно содержать минимум 2 символа'
            );

            isValid = false;

        } else if (
            !validatePersonName(
                nameVal
            )
        ) {

            showError(
                name,
                'Только буквы, пробелы и дефис'
            );

            isValid = false;
        }
    }


    // SURNAME
    if (surname) {

        const surnameVal =
            surname.value.trim();


        if (
            surnameVal === ''
        ) {

            showError(
                surname,
                'Фамилия обязательна'
            );

            isValid = false;

        } else if (
            surnameVal.length < 2
        ) {

            showError(
                surname,
                'Фамилия должна содержать минимум 2 символа'
            );

            isValid = false;

        } else if (
            !validatePersonName(
                surnameVal
            )
        ) {

            showError(
                surname,
                'Только буквы, пробелы и дефис'
            );

            isValid = false;
        }
    }


    return isValid;
}


function validatePersonName(
    value
) {

    return (
        /^[a-zA-Zа-яА-ЯёЁ\s\-]+$/
            .test(value)
    );
}


function validatePassword(
    pwd
) {

    const errors = [];


    if (
        pwd.length < 8
    ) {

        errors.push(
            'Минимум 8 символов'
        );
    }


    if (
        !/[A-Z]/.test(pwd)
    ) {

        errors.push(
            'Заглавная буква (A-Z)'
        );
    }


    if (
        !/[a-z]/.test(pwd)
    ) {

        errors.push(
            'Строчная буква (a-z)'
        );
    }


    if (
        !/[0-9]/.test(pwd)
    ) {

        errors.push(
            'Цифра'
        );
    }


    if (
        !/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+$/
            .test(pwd)
    ) {

        errors.push(
            'Только латиница, цифры и спецсимволы'
        );
    }


    if (
        /\s/.test(pwd)
    ) {

        errors.push(
            'Без пробелов'
        );
    }


    return errors;
}


function validateEmail(
    email
) {

    return (
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            .test(
                String(email)
                    .toLowerCase()
            )
    );
}


function showError(
    input,
    message
) {

    input.style.border =
        '2px solid #ff6b6b';


    input.style.boxShadow =
        '0 0 10px rgba(255, 107, 107, 0.3)';


    const parent =
        input.parentNode;


    let errorSpan =
        parent.querySelector(
            '.error-message'
        );


    if (!errorSpan) {

        errorSpan =
            document.createElement(
                'span'
            );


        errorSpan.className =
            'error-message';


        errorSpan.style.cssText = `
            display: block;
            color: #ff6b6b;
            font-size: 12px;
            margin-top: 5px;
            margin-left: 15px;
        `;


        parent.appendChild(
            errorSpan
        );
    }


    errorSpan.textContent =
        message;
}


function clearErrors(
    form
) {

    form
        .querySelectorAll('input')
        .forEach(
            input => {

                input.style.border =
                    '';

                input.style.boxShadow =
                    '';
            }
        );


    form
        .querySelectorAll(
            '.error-message'
        )
        .forEach(
            el => el.remove()
        );
}


function resetFormStyles(
    form
) {

    clearErrors(form);
}


function showBanner(
    form,
    message,
    type
) {

    const existingBanner =
        form.querySelector(
            '.ajax-banner'
        );


    if (
        existingBanner
    ) {

        existingBanner.remove();
    }


    const banner =
        document.createElement(
            'div'
        );


    banner.className =
        'ajax-banner';


    banner.style.cssText = `
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 14px;
        line-height: 1.5;
    `;


    if (
        type === 'error'
    ) {

        banner.style.background =
            'rgba(255, 80, 80, 0.15)';


        banner.style.borderLeft =
            '4px solid #ff6b6b';


        banner.style.color =
            '#ff8a8a';


        banner.innerHTML =
            '<i class="fas fa-exclamation-circle" style="margin-right: 8px;"></i>'
            + message;


    } else {


        banner.style.background =
            'rgba(80, 200, 120, 0.15)';


        banner.style.borderLeft =
            '4px solid #6fcf97';


        banner.style.color =
            '#6fcf97';


        banner.innerHTML =
            '<i class="fas fa-check-circle" style="margin-right: 8px;"></i>'
            + message;
    }


    form.insertBefore(
        banner,
        form.firstChild
    );
}


function clearBanner(
    form
) {

    const banner =
        form.querySelector(
            '.ajax-banner'
        );


    if (banner) {

        banner.remove();
    }
}


function addLiveValidation() {


    // EMAIL
    document
        .querySelectorAll(
            'input[type="email"], input[name="email"]'
        )
        .forEach(
            input => {

                input.addEventListener(
                    'input',
                    function () {

                        const value =
                            this.value.trim();


                        if (
                            value.length === 0
                        ) {

                            updateLiveFieldStyle(
                                this,
                                false,
                                ''
                            );

                            return;
                        }


                        const isValid =
                            validateEmail(
                                value
                            );


                        updateLiveFieldStyle(
                            this,
                            !isValid,
                            'Некорректный email'
                        );
                    }
                );
            }
        );


    // PASSWORD
    const registerPassword =
        document.querySelector(
            'form[action="/registration"] input[name="password"]'
        );


    if (
        registerPassword
    ) {

        registerPassword
            .addEventListener(
                'input',
                function () {

                    if (
                        this.value.length
                        === 0
                    ) {

                        updateLiveFieldStyle(
                            this,
                            false,
                            ''
                        );

                        return;
                    }


                    const errors =
                        validatePassword(
                            this.value
                        );


                    updateLiveFieldStyle(
                        this,
                        errors.length > 0,
                        errors.join('; ')
                    );
                }
            );
    }


    // NAME
    const nameInput =
        document.querySelector(
            'form[action="/registration"] input[name="name"]'
        );


    if (
        nameInput
    ) {

        addNameLiveValidation(
            nameInput,
            'Имя'
        );
    }


    // SURNAME
    const surnameInput =
        document.querySelector(
            'form[action="/registration"] input[name="surname"]'
        );


    if (
        surnameInput
    ) {

        addNameLiveValidation(
            surnameInput,
            'Фамилия'
        );
    }
}


function addNameLiveValidation(
    input,
    fieldName
) {

    input.addEventListener(
        'input',
        function () {

            const value =
                this.value.trim();


            if (
                value.length === 0
            ) {

                updateLiveFieldStyle(
                    this,
                    false,
                    ''
                );

                return;
            }


            let error = null;


            if (
                value.length < 2
            ) {

                error =
                    `${fieldName}: минимум 2 символа`;

            } else if (
                !validatePersonName(
                    value
                )
            ) {

                error =
                    'Недопустимые символы';
            }


            updateLiveFieldStyle(
                this,
                !!error,
                error
            );
        }
    );
}


function updateLiveFieldStyle(
    input,
    isError,
    message
) {

    const parent =
        input.parentNode;


    let errorSpan =
        parent.querySelector(
            '.error-message'
        );


    if (
        isError
    ) {

        input.style.border =
            '2px solid #ff6b6b';


        input.style.boxShadow =
            '0 0 10px rgba(255, 107, 107, 0.3)';


        if (
            !errorSpan
        ) {

            errorSpan =
                document.createElement(
                    'span'
                );


            errorSpan.className =
                'error-message';


            errorSpan.style.cssText = `
                display: block;
                color: #ff6b6b;
                font-size: 12px;
                margin-top: 5px;
                margin-left: 15px;
            `;


            parent.appendChild(
                errorSpan
            );
        }


        errorSpan.textContent =
            message || 'Ошибка';


    } else {


        if (
            input.value.length > 0
        ) {

            input.style.border =
                '2px solid #6fcf97';


            input.style.boxShadow =
                '0 0 10px rgba(111, 207, 151, 0.2)';


        } else {

            input.style.border =
                '';

            input.style.boxShadow =
                '';
        }


        if (
            errorSpan
        ) {

            errorSpan.remove();
        }
    }
}
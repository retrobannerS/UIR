document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const authTabs = document.querySelectorAll('.auth-tab');
    const passwordToggles = document.querySelectorAll('.toggle-password');

    // --- Tab Switching Logic ---
    authTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetFormId = tab.dataset.tab;

            // Update tab active states
            authTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/hide forms
            loginForm.classList.toggle('active', targetFormId === 'login');
            registerForm.classList.toggle('active', targetFormId === 'register');

            // Clear any previous error messages
            document.getElementById('loginError').textContent = '';
            document.getElementById('registerError').textContent = '';
        });
    });

    // --- Password Visibility Toggle ---
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            const icon = toggle.querySelector('i');
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
        });
    });

    // --- Registration Form Logic ---
    const registerUsernameInput = document.getElementById('registerUsername');
    const registerPasswordInput = document.getElementById('registerPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const registerButton = registerForm.querySelector('button[type="submit"]');
    const usernameHint = document.querySelector('.username-hint');
    const passwordMatchHint = document.querySelector('.password-match-hint');
    const requirements = document.querySelectorAll('.requirement');

    let isUsernameValid = false;
    let isPasswordComplex = false;
    let doPasswordsMatch = false;

    registerButton.disabled = true;

    const updateRegisterButtonState = () => {
        registerButton.disabled = !(isUsernameValid && isPasswordComplex && doPasswordsMatch);
    };

    const updateRequirement = (hintElement, isValid, text) => {
        const icon = hintElement.querySelector('i');
        const span = hintElement.querySelector('span');

        hintElement.style.display = text ? 'flex' : 'none';
        span.textContent = text;

        // Use success/error classes for unified color styling
        hintElement.classList.remove('valid', 'success', 'error');
        if (text) {
            hintElement.classList.add(isValid ? 'success' : 'error');
        }

        if (isValid) {
            icon.className = 'fas fa-check-circle';
        } else {
            // Only show cross icon if there is text, otherwise no icon
            icon.className = text ? 'fas fa-times-circle' : '';
        }
    };

    // Username validation with debounce
    let usernameTimeout;
    const checkUsername = async (username) => {
        const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;

        if (!username) {
            updateRequirement(usernameHint, false, '');
            isUsernameValid = false;
            updateRegisterButtonState();
            return false;
        }

        if (!usernameRegex.test(username)) {
            updateRequirement(usernameHint, false, 'Только латинские буквы, цифры и `_` (3-20 симв.)');
            isUsernameValid = false;
            updateRegisterButtonState();
            return false;
        }

        try {
            const response = await fetch(`/api/v1/users/check-username?username=${encodeURIComponent(username)}`);
            const data = await response.json();

            if (!data.exists) {
                updateRequirement(usernameHint, true, 'Имя пользователя доступно');
                isUsernameValid = true;
                updateRegisterButtonState();
                return true;
            } else {
                updateRequirement(usernameHint, false, 'Имя пользователя уже занято');
                isUsernameValid = false;
                updateRegisterButtonState();
                return false;
            }
        } catch (error) {
            console.error('Error checking username:', error);
            updateRequirement(usernameHint, false, 'Ошибка при проверке имени');
            isUsernameValid = false;
            updateRegisterButtonState();
            return false;
        }
    };

    registerUsernameInput.addEventListener('input', (e) => {
        isUsernameValid = false; // Invalidate while typing/debouncing
        updateRegisterButtonState();
        clearTimeout(usernameTimeout);
        usernameTimeout = setTimeout(() => {
            checkUsername(e.target.value);
        }, 500);
    });

    // Password validation
    const validatePassword = (password) => {
        if (password.length === 0) {
            requirements.forEach(req => {
                req.classList.remove('valid');
                const icon = req.querySelector('i');
                icon.className = 'fas fa-circle';
            });
            isPasswordComplex = false;
            updateRegisterButtonState();
            return false;
        }

        const checks = {
            length: password.length >= 8 && password.length <= 20,
            number: /\d/.test(password),
            latin: /^[a-zA-Z0-9]*$/.test(password)
        };

        let allValid = true;
        requirements.forEach(req => {
            const type = req.dataset.requirement;
            if (checks[type] !== undefined) {
                const isValid = checks[type];
                req.classList.toggle('valid', isValid);
                const icon = req.querySelector('i');
                icon.className = isValid ? 'fas fa-check-circle' : 'fas fa-circle';
                if (!isValid) allValid = false;
            }
        });
        isPasswordComplex = allValid;
        updateRegisterButtonState();
        return allValid;
    };

    // Password match validation
    const validatePasswordMatch = () => {
        const password = registerPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        if (!confirmPassword) {
            updateRequirement(passwordMatchHint, false, '');
            doPasswordsMatch = false;
            updateRegisterButtonState();
            return false;
        }

        const isMatch = password === confirmPassword;
        const text = isMatch ? 'Пароли совпадают' : 'Пароли не совпадают';
        updateRequirement(passwordMatchHint, isMatch, text);
        doPasswordsMatch = isMatch;
        updateRegisterButtonState();
        return isMatch;
    };

    registerPasswordInput.addEventListener('input', (e) => {
        validatePassword(e.target.value);
        validatePasswordMatch();
    });

    confirmPasswordInput.addEventListener('input', validatePasswordMatch);

    // Registration form submission
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = registerUsernameInput.value;
        const password = registerPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        const errorElement = document.getElementById('registerError');

        // Final check on submit, although button state should prevent this.
        const isUsernameReady = await checkUsername(username);
        const isPasswordReady = validatePassword(password);
        const doPasswordsMatch = validatePasswordMatch();

        if (!isUsernameReady || !isPasswordReady || !doPasswordsMatch) {
            errorElement.textContent = 'Пожалуйста, исправьте ошибки в форме.';
            return;
        }

        try {
            const response = await fetch('/api/v1/users/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const data = await response.json();
                errorElement.textContent = data.detail || 'Ошибка при регистрации.';
                return;
            }

            const data = await response.json();
            // Automatically log in after successful registration
            loginUser(username, password, 'loginError'); // Use login error field for feedback
        } catch (error) {
            errorElement.textContent = 'Произошла ошибка сети.';
            console.error('Registration error:', error);
        }
    });


    // --- Login Form Logic ---
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const errorElement = document.getElementById('loginError');
        await loginUser(username, password, 'loginError');
    });

    async function loginUser(username, password, errorElementId) {
        const errorElement = document.getElementById(errorElementId);
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        // Clear previous error message
        errorElement.textContent = '';

        try {
            const response = await fetch('/api/v1/users/login/access-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('accessToken', data.access_token);
                window.location.href = '/queries'; // Redirect to main page
            } else {
                errorElement.textContent = 'Неправильное имя пользователя или пароль';
            }
        } catch (error) {
            errorElement.textContent = 'Произошла ошибка сети.';
            console.error('Login error:', error);
        }
    }
});
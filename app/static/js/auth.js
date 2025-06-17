document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const authTabs = document.querySelectorAll('.auth-tab');
    const passwordToggles = document.querySelectorAll('.password-toggle');

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
            toggle.classList.toggle('fa-eye');
            toggle.classList.toggle('fa-eye-slash');
        });
    });

    // --- Registration Form Logic ---
    const registerUsernameInput = document.getElementById('registerUsername');
    const registerPasswordInput = document.getElementById('registerPassword');
    const usernameHint = document.querySelector('.username-hint');
    const usernameCheck = document.querySelector('.username-check');
    const usernameCross = document.querySelector('.username-cross');
    const requirements = document.querySelectorAll('.requirement');

    // Username validation with debounce
    let usernameTimeout;
    const checkUsername = async (username) => {
        const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
        usernameHint.classList.remove('error', 'success');
        usernameCheck.classList.add('hidden');
        usernameCross.classList.add('hidden');

        if (!username) {
            usernameHint.textContent = 'Введите имя пользователя';
            usernameHint.classList.add('error');
            return false;
        }

        if (!usernameRegex.test(username)) {
            usernameHint.textContent = 'Только латинские буквы, цифры и `_` (3-20 симв.)';
            usernameHint.classList.add('error');
            usernameCross.classList.remove('hidden');
            return false;
        }

        try {
            const response = await fetch(`/api/v1/users/check-username?username=${encodeURIComponent(username)}`);
            const data = await response.json();

            if (!data.exists) {
                usernameHint.textContent = 'Имя пользователя доступно';
                usernameHint.classList.add('success');
                usernameCheck.classList.remove('hidden');
                return true;
            } else {
                usernameHint.textContent = 'Имя пользователя уже занято';
                usernameHint.classList.add('error');
                usernameCross.classList.remove('hidden');
                return false;
            }
        } catch (error) {
            console.error('Error checking username:', error);
            usernameHint.textContent = 'Ошибка при проверке имени';
            usernameHint.classList.add('error');
            return false;
        }
    };

    registerUsernameInput.addEventListener('input', (e) => {
        clearTimeout(usernameTimeout);
        usernameTimeout = setTimeout(() => {
            checkUsername(e.target.value);
        }, 500);
    });

    // Password validation
    const validatePassword = (password) => {
        const checks = {
            length: password.length >= 8 && password.length <= 20,
            number: /\d/.test(password),
            latin: /^[a-zA-Z0-9]*$/.test(password) // Только латиница и цифры, без спецсимволов
        };

        let allValid = true;
        requirements.forEach(req => {
            const type = req.dataset.requirement;
            // Скрываем или показываем требования, которых больше нет в `checks`
            if (checks[type] !== undefined) {
                req.style.display = 'block';
                const isValid = checks[type];
                req.classList.toggle('valid', isValid);
                if (!isValid) allValid = false;
            } else {
                req.style.display = 'none';
            }
        });
        return allValid;
    };

    registerPasswordInput.addEventListener('input', (e) => {
        validatePassword(e.target.value);
    });

    // Registration form submission
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = registerUsernameInput.value;
        const password = registerPasswordInput.value;
        const errorElement = document.getElementById('registerError');

        const isUsernameValid = await checkUsername(username);
        const isPasswordValid = validatePassword(password);

        if (!isUsernameValid || !isPasswordValid) {
            errorElement.textContent = 'Пожалуйста, исправьте ошибки в форме.';
            return;
        }

        try {
            const response = await fetch('/api/v1/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();

            if (response.ok) {
                // Automatically log in after successful registration
                loginUser(username, password, 'loginError'); // Use login error field for feedback
            } else {
                errorElement.textContent = data.detail || 'Ошибка при регистрации.';
            }
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

        try {
            const response = await fetch('/api/v1/login/access-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('accessToken', data.access_token);
                window.location.href = '/queries'; // Redirect to main page
            } else {
                errorElement.textContent = data.detail || 'Неверные учетные данные.';
            }
        } catch (error) {
            errorElement.textContent = 'Произошла ошибка сети.';
            console.error('Login error:', error);
        }
    }
});
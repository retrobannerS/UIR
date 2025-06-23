document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // --- DOM Elements ---
    const avatarPreview = document.getElementById('avatar-preview');
    const avatarPlaceholder = document.getElementById('avatar-placeholder');
    const avatarNickname = document.getElementById('avatar-nickname');
    const avatarUploadInput = document.getElementById('avatar-upload-input');
    const newUsernameInput = document.getElementById('new-username-input');
    const saveUsernameButton = document.getElementById('save-username-button');
    const usernameHint = document.querySelector('.username-hint');
    const usernameStatusIcon = document.getElementById('username-status-icon');
    const passwordChangeForm = document.getElementById('password-change-form');
    const oldPasswordInput = document.getElementById('old-password');
    const newPasswordInput = document.getElementById('new-password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const savePasswordButton = document.getElementById('save-password-button');
    const passwordHint = document.getElementById('password-hint');
    const passwordStrengthMeter = document.getElementById('password-strength-meter');
    const togglePasswordIcons = document.querySelectorAll('.toggle-password');
    const avatarModal = document.getElementById('avatar-modal');
    const modalAvatarImage = document.getElementById('modal-avatar-image');
    const confirmAvatarUploadBtn = document.getElementById('confirm-avatar-upload');
    const cancelAvatarUploadBtn = document.getElementById('cancel-avatar-upload');
    const deleteAvatarBtn = document.getElementById('delete-avatar-btn');
    const openAvatarModalBtn = document.getElementById('open-avatar-modal-btn');
    const usernameForm = document.getElementById('username-change-form');
    const passwordMatchHint = document.querySelector('.password-match-hint');
    const passwordFormMessage = document.getElementById('password-form-message');

    let originalUsername = '';
    let isUsernameValid = false;
    let selectedAvatarFile = null;

    // --- Main Functions ---

    function populateUserData(user) {
        if (!user) return;
        originalUsername = user.username;
        if (avatarNickname) avatarNickname.textContent = user.username;

        // Determine if the delete button should be enabled
        deleteAvatarBtn.disabled = user.is_default_avatar;

        if (user.avatar_url) {
            const avatarUrl = `${user.avatar_url}?t=${new Date().getTime()}`;
            if (avatarPreview) {
                avatarPreview.src = avatarUrl;
                avatarPreview.style.display = 'block';
            }
            if (avatarPlaceholder) {
                avatarPlaceholder.style.display = 'none';
            }
            if (modalAvatarImage) modalAvatarImage.src = avatarUrl;
        } else {
            if (avatarPreview) {
                avatarPreview.src = '';
                avatarPreview.style.display = 'none';
            }
            if (avatarPlaceholder) {
                avatarPlaceholder.style.display = 'flex';
                const firstLetter = user.username.charAt(0).toUpperCase();
                avatarPlaceholder.textContent = firstLetter;

                let hash = 0;
                for (let i = 0; i < user.username.length; i++) {
                    hash = user.username.charCodeAt(i) + ((hash << 5) - hash);
                }
                const colors = ['#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#34495e', '#f1c40f', '#e67e22', '#e74c3c'];
                avatarPlaceholder.style.backgroundColor = colors[Math.abs(hash) % colors.length];
                avatarPlaceholder.style.color = 'white';
                avatarPlaceholder.style.justifyContent = 'center';
                avatarPlaceholder.style.alignItems = 'center';
                avatarPlaceholder.style.fontSize = '48px';
                avatarPlaceholder.style.fontWeight = 'bold';
            }
            if (modalAvatarImage) modalAvatarImage.src = '';
        }
    }

    function setStatus(status, message) {
        usernameHint.textContent = '';
        usernameHint.className = 'input-hint username-hint';
        usernameStatusIcon.className = 'status-icon';
        if (status === 'neutral') return;
        usernameStatusIcon.classList.add('visible');
        if (status === 'success') {
            usernameHint.textContent = message;
            usernameHint.classList.add('success');
            usernameStatusIcon.classList.add('fas', 'fa-check-circle', 'success');
        } else if (status === 'error') {
            usernameHint.textContent = message;
            usernameHint.classList.add('error');
            usernameStatusIcon.classList.add('fas', 'fa-times-circle', 'error');
        }
    }

    async function checkUsername(username) {
        saveUsernameButton.disabled = true;
        isUsernameValid = false;
        setStatus('neutral');
        if (username === originalUsername) return;
        if (!/^[a-zA-Z0-9_]{3,20}$/.test(username)) {
            setStatus('error', 'Только латинские буквы, цифры и _ (3-20 симв.)');
            return;
        }
        try {
            const response = await fetch(`/api/v1/users/check-username?username=${encodeURIComponent(username)}`);
            const data = await response.json();
            if (!data.exists) {
                setStatus('success', 'Имя доступно!');
                saveUsernameButton.disabled = false;
                isUsernameValid = true;
            } else {
                setStatus('error', 'Это имя уже занято.');
            }
        } catch (error) {
            console.error('Error checking username:', error);
            setStatus('error', 'Ошибка при проверке имени.');
        }
    }

    async function updateUsername(e) {
        e.preventDefault();
        if (!isUsernameValid) return;

        if (!confirm('Вы уверены, что хотите сменить имя пользователя?')) {
            return;
        }

        const newUsername = newUsernameInput.value;
        saveUsernameButton.disabled = true;
        saveUsernameButton.textContent = 'Сохранение...';

        try {
            const response = await fetch('/api/v1/users/me/username', {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: newUsername })
            });
            const updatedUser = await response.json();
            if (!response.ok) throw new Error(updatedUser.detail || 'Не удалось обновить имя.');

            setStatus('success', 'Имя успешно обновлено!');
            AppData.user.set(updatedUser);

            newUsernameInput.value = '';
            isUsernameValid = false;

            setTimeout(() => {
                setStatus('neutral');
            }, 3000);

            if (selectedAvatarFile) {
                uploadAvatar();
            }
        } catch (error) {
            setStatus('error', error.message);
            saveUsernameButton.disabled = false;
        } finally {
            saveUsernameButton.textContent = 'Сохранить';
        }
    }

    const updateHint = (hintElement, isValid, text) => {
        if (!hintElement) return;

        hintElement.style.display = text ? 'flex' : 'none';

        hintElement.classList.remove('valid', 'success', 'error');
        if (text) {
            hintElement.classList.add(isValid ? 'success' : 'error');
        }

        let iconClass = '';
        if (text) {
            iconClass = isValid ? 'fas fa-check-circle' : 'fas fa-times-circle';
        }

        hintElement.innerHTML = `<i class="${iconClass}"></i><span>${text}</span>`;
    };

    function validatePasswordStrength(password) {
        const requirementsElements = document.querySelectorAll('#password-change-form .requirement');

        if (password.length === 0) {
            requirementsElements.forEach(req => {
                req.classList.remove('valid');
                const icon = req.querySelector('i');
                icon.className = 'fas fa-circle';
            });
            return false;
        }

        const requirements = {
            length: password.length >= 8 && password.length <= 20,
            number: /\d/.test(password),
            latin: /^[a-zA-Z0-9]*$/.test(password)
        };

        let allValid = true;
        requirementsElements.forEach(req => {
            const type = req.dataset.requirement;
            if (requirements[type] !== undefined) {
                const isValid = requirements[type];
                req.classList.toggle('valid', isValid);
                const icon = req.querySelector('i');
                icon.className = isValid ? 'fas fa-check-circle' : 'fas fa-circle';
                if (!isValid) allValid = false;
            }
        });
        return allValid;
    }

    function validatePasswordForm() {
        const oldPass = oldPasswordInput.value;
        const newPass = newPasswordInput.value;
        const confirmPass = confirmPasswordInput.value;

        const isStrong = validatePasswordStrength(newPass);

        let passwordsMatch = false;
        if (confirmPass.length > 0) {
            passwordsMatch = newPass === confirmPass;
            const text = passwordsMatch ? 'Пароли совпадают' : 'Пароли не совпадают';
            updateHint(passwordMatchHint, passwordsMatch, text);
        } else {
            updateHint(passwordMatchHint, false, '');
        }

        savePasswordButton.disabled = !(oldPass.length > 0 && newPass.length > 0 && isStrong && passwordsMatch);
    }

    async function handlePasswordChange(event) {
        event.preventDefault();
        passwordFormMessage.textContent = '';
        passwordFormMessage.className = 'form-message';
        const oldPassword = oldPasswordInput.value;
        const newPassword = newPasswordInput.value;
        savePasswordButton.disabled = true;
        savePasswordButton.textContent = 'Сохранение...';
        try {
            const response = await fetch('/api/v1/users/me/password', {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
            });
            if (response.status === 204) {
                passwordFormMessage.textContent = 'Пароль успешно обновлён';
                passwordFormMessage.classList.add('success');
                passwordChangeForm.reset();
                validatePasswordStrength('');
                updateHint(passwordMatchHint, false, '');
                setTimeout(() => {
                    passwordFormMessage.textContent = '';
                    passwordFormMessage.className = 'form-message';
                }, 3000);
            } else {
                const errorData = await response.json();
                let errorMessage = errorData.detail || 'Произошла ошибка.';
                if (response.status === 400 && errorData.detail === "Incorrect old password") {
                    errorMessage = "Неверный старый пароль";
                }
                throw new Error(errorMessage);
            }
        } catch (error) {
            passwordFormMessage.textContent = error.message;
            passwordFormMessage.classList.add('error');
        } finally {
            savePasswordButton.disabled = false;
            savePasswordButton.textContent = 'Сохранить пароль';
            validatePasswordForm();
        }
    }

    function openModal() {
        confirmAvatarUploadBtn.disabled = true;
        confirmAvatarUploadBtn.textContent = 'Сохранить';
        modalAvatarImage.src = avatarPreview.src;
        avatarModal.style.display = 'flex';
        avatarUploadInput.value = '';
    }

    function closeModal() {
        avatarModal.style.display = 'none';
        selectedAvatarFile = null;
        avatarUploadInput.value = '';
    }

    async function uploadAvatar() {
        if (!selectedAvatarFile) return;
        confirmAvatarUploadBtn.disabled = true;
        confirmAvatarUploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';

        const formData = new FormData();
        formData.append('file', selectedAvatarFile);

        try {
            const response = await fetch('/api/v1/users/me/avatar', {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Не удалось загрузить аватар.');
            }

            const updatedUser = await response.json();
            AppData.user.set(updatedUser);
            closeModal();

        } catch (error) {
            alert(`Ошибка: ${error.message}`);
        } finally {
            confirmAvatarUploadBtn.disabled = false;
            confirmAvatarUploadBtn.innerHTML = '<i class="fas fa-check"></i> Сохранить';
        }
    }

    async function deleteAvatar() {
        if (!confirm('Вы уверены, что хотите удалить аватар?')) {
            return;
        }

        try {
            const response = await fetch('/api/v1/users/me/avatar', {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Не удалось удалить аватар.');
            }
            const updatedUser = await response.json();
            AppData.user.set(updatedUser);
        } catch (error) {
            alert(`Ошибка: ${error.message}`);
        } finally {
            // The button state will be updated by populateUserData via the event listener
        }
    }

    // --- Event Listeners ---

    if (openAvatarModalBtn) openAvatarModalBtn.addEventListener('click', openModal);
    if (cancelAvatarUploadBtn) cancelAvatarUploadBtn.addEventListener('click', closeModal);
    if (confirmAvatarUploadBtn) confirmAvatarUploadBtn.addEventListener('click', uploadAvatar);
    if (deleteAvatarBtn) deleteAvatarBtn.addEventListener('click', deleteAvatar);
    if (avatarModal) avatarModal.addEventListener('click', (e) => { if (e.target === avatarModal) closeModal(); });

    if (avatarUploadInput) {
        avatarUploadInput.addEventListener('change', () => {
            const file = avatarUploadInput.files[0];
            if (file) {
                selectedAvatarFile = file;
                const reader = new FileReader();
                reader.onload = (e) => { modalAvatarImage.src = e.target.result; };
                reader.readAsDataURL(file);
                confirmAvatarUploadBtn.disabled = false;
            }
        });
    }

    let usernameTimeout;
    if (newUsernameInput) {
        newUsernameInput.addEventListener('input', () => {
            clearTimeout(usernameTimeout);
            usernameTimeout = setTimeout(() => checkUsername(newUsernameInput.value), 500);
        });
    }
    if (usernameForm) usernameForm.addEventListener('submit', updateUsername);

    togglePasswordIcons.forEach(icon => {
        icon.addEventListener('click', () => {
            const passwordInput = icon.previousElementSibling;
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            icon.querySelector('i').classList.toggle('fa-eye');
            icon.querySelector('i').classList.toggle('fa-eye-slash');
        });
    });

    if (passwordChangeForm) {
        [oldPasswordInput, newPasswordInput, confirmPasswordInput].forEach(input => {
            if (input) input.addEventListener('input', validatePasswordForm);
        });
        passwordChangeForm.addEventListener('submit', handlePasswordChange);
    }

    if (newPasswordInput) {
        newPasswordInput.addEventListener('focus', () => {
            document.querySelector('.password-requirements').style.display = 'grid';
        });
    }

    // --- Initialization ---

    document.addEventListener('userDataUpdated', (event) => {
        const user = event.detail;
        if (user) {
            populateUserData(user);
        }
    });

    // Event Listeners
    if (usernameForm) {
        usernameForm.addEventListener('submit', updateUsername);
    }
}); 
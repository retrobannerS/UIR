document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        // This should be handled by main.js, but as a fallback
        window.location.href = '/login';
        return;
    }

    // --- DOM Elements ---
    const avatarPreview = document.getElementById('avatar-preview');
    const avatarNickname = document.getElementById('avatar-nickname');
    const avatarUploadInput = document.getElementById('avatar-upload-input');
    const newUsernameInput = document.getElementById('new-username-input');
    const saveUsernameButton = document.getElementById('save-username-button');
    const usernameHint = document.querySelector('.username-hint');
    const usernameFormMessage = document.getElementById('username-form-message');
    const usernameStatusIcon = document.getElementById('username-status-icon');

    // Password change elements
    const passwordChangeForm = document.getElementById('password-change-form');
    const oldPasswordInput = document.getElementById('old-password');
    const newPasswordInput = document.getElementById('new-password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const savePasswordButton = document.getElementById('save-password-button');
    const passwordHint = document.getElementById('password-hint');

    // Modal elements
    const avatarModal = document.getElementById('avatar-modal');
    const modalAvatarImage = document.getElementById('modal-avatar-image');
    const confirmAvatarUploadBtn = document.getElementById('confirm-avatar-upload');
    const cancelAvatarUploadBtn = document.getElementById('cancel-avatar-upload');
    const deleteAvatarBtn = document.getElementById('delete-avatar-btn');
    const openAvatarModalBtn = document.getElementById('open-avatar-modal-btn');

    let originalUsername = '';
    let isUsernameValid = false;
    let isDefaultAvatar = true;
    let selectedAvatarFile = null; // To store the selected file temporarily

    // --- Functions ---

    function setStatus(status, message) {
        // Clear previous states
        usernameHint.textContent = '';
        usernameHint.className = 'input-hint username-hint';
        usernameStatusIcon.className = 'status-icon';

        if (status === 'neutral') {
            return;
        }

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

    // Load initial user data
    async function loadUserData() {
        try {
            const response = await fetch('/api/v1/users/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error('Failed to load user data');
            const user = await response.json();

            originalUsername = user.username;
            isDefaultAvatar = user.is_default_avatar;
            newUsernameInput.value = user.username;
            avatarNickname.textContent = user.username;

            if (user.avatar_url) {
                const avatarUrl = `${user.avatar_url}?t=${new Date().getTime()}`;
                avatarPreview.src = avatarUrl;
                modalAvatarImage.src = avatarUrl; // Pre-load current avatar into modal
            }
        } catch (error) {
            console.error('Error loading user data:', error);
            usernameFormMessage.textContent = 'Не удалось загрузить данные пользователя.';
            usernameFormMessage.className = 'form-message error';
        }
    }

    // The upload function now takes the file from the stored variable
    async function uploadAvatar() {
        if (!selectedAvatarFile) return;

        confirmAvatarUploadBtn.disabled = true;
        confirmAvatarUploadBtn.textContent = 'Загрузка...';

        const formData = new FormData();
        formData.append('file', selectedAvatarFile);
        try {
            const response = await fetch('/api/v1/users/me/avatar', {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData,
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to upload avatar');
            }

            // On success, reload the page to show the new avatar everywhere
            location.reload();

        } catch (error) {
            console.error('Error uploading avatar:', error);
            // Optionally: show an error message in the modal or on the page
            alert(`Ошибка загрузки: ${error.message}`);
        } finally {
            closeModal();
        }
    }

    async function deleteAvatar() {
        if (!confirm("Вы уверены, что хотите удалить свой аватар?")) {
            return;
        }

        try {
            const response = await fetch('/api/v1/users/me/avatar', {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` },
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to delete avatar');
            }

            // On success, reload the page to show the new default avatar
            location.reload();
        } catch (error) {
            console.error('Error deleting avatar:', error);
            alert(`Ошибка удаления: ${error.message}`);
        }
    }

    function openModal() {
        // Reset state from previous opens
        confirmAvatarUploadBtn.disabled = true;
        confirmAvatarUploadBtn.textContent = 'Сохранить';
        modalAvatarImage.src = avatarPreview.src; // Show current avatar

        avatarModal.style.display = 'flex';
    }

    function closeModal() {
        avatarModal.style.display = 'none';
        selectedAvatarFile = null;
        avatarUploadInput.value = ''; // Reset file input
    }

    async function checkUsername(username) {
        saveUsernameButton.disabled = true;
        isUsernameValid = false;
        setStatus('neutral');

        if (username === originalUsername) {
            return;
        }

        const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
        if (!usernameRegex.test(username)) {
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

    // --- Event Listeners ---

    if (avatarPreview) {
        avatarPreview.addEventListener('click', openModal);
        openAvatarModalBtn.addEventListener('click', openModal);
        cancelAvatarUploadBtn.addEventListener('click', closeModal);
        avatarUploadInput.addEventListener('change', () => {
            const file = avatarUploadInput.files[0];
            if (file) {
                selectedAvatarFile = file;
                const reader = new FileReader();
                reader.onload = (e) => {
                    modalAvatarImage.src = e.target.result;
                };
                reader.readAsDataURL(file);
                confirmAvatarUploadBtn.disabled = false; // Enable save button
            }
        });
        confirmAvatarUploadBtn.addEventListener('click', uploadAvatar);
        deleteAvatarBtn.addEventListener('click', deleteAvatar);
    }

    newUsernameInput.addEventListener('input', () => checkUsername(newUsernameInput.value));
    saveUsernameButton.addEventListener('click', updateUsername);

    // Password change listeners
    passwordChangeForm.addEventListener('submit', handlePasswordChange);
    [oldPasswordInput, newPasswordInput, confirmPasswordInput].forEach(input => {
        input.addEventListener('input', validatePasswordForm);
    });

    // Close modal if clicking on the overlay
    avatarModal.addEventListener('click', (e) => {
        if (e.target === avatarModal) {
            closeModal();
        }
    });

    // Username validation (similar to auth.js)
    let usernameTimeout;
    newUsernameInput.addEventListener('input', () => {
        clearTimeout(usernameTimeout);
        usernameTimeout = setTimeout(() => {
            checkUsername(newUsernameInput.value);
        }, 500);
    });

    // Save username
    document.getElementById('username-change-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!isUsernameValid) return;

        usernameFormMessage.textContent = '';
        try {
            const response = await fetch('/api/v1/users/me', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username: newUsernameInput.value })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to update username');
            }

            const updatedUser = await response.json();
            originalUsername = updatedUser.username;
            usernameFormMessage.textContent = 'Имя пользователя успешно обновлено!';
            usernameFormMessage.className = 'form-message success';
            saveUsernameButton.disabled = true;
            isUsernameValid = false;
            // Also update the avatar in the top bar
            document.querySelector('#user-avatar').textContent = originalUsername.charAt(0).toUpperCase();

            // Перезагружаем страницу, чтобы обновить имя и, возможно, дефолтный аватар
            location.reload();

        } catch (error) {
            console.error('Error updating username:', error);
            usernameFormMessage.textContent = `Ошибка: ${error.message}`;
            usernameFormMessage.className = 'form-message error';
        }
    });

    async function handlePasswordChange(event) {
        event.preventDefault();
        const oldPassword = oldPasswordInput.value;
        const newPassword = newPasswordInput.value;

        // Clear previous hints
        passwordHint.textContent = '';
        passwordHint.className = 'input-hint';

        try {
            const response = await fetch('/api/v1/users/me/password', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    old_password: oldPassword,
                    new_password: newPassword
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Не удалось обновить пароль');
            }

            passwordHint.textContent = 'Пароль успешно обновлен.';
            passwordHint.className = 'input-hint success';
            passwordChangeForm.reset();
            savePasswordButton.disabled = true;

            // Hide success message after a delay
            setTimeout(() => {
                passwordHint.textContent = '';
                passwordHint.className = 'input-hint';
            }, 5000);

        } catch (error) {
            console.error('Error updating password:', error);
            passwordHint.textContent = `Ошибка: ${error.message}`;
            passwordHint.className = 'input-hint error';
        }
    }

    function validatePasswordForm() {
        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        // Basic validation
        if (newPassword.length > 0 && newPassword.length < 8) {
            passwordHint.textContent = 'Новый пароль должен содержать не менее 8 символов.';
            passwordHint.className = 'input-hint error';
        } else if (newPassword.length > 0 && confirmPassword.length > 0 && newPassword !== confirmPassword) {
            passwordHint.textContent = 'Пароли не совпадают.';
            passwordHint.className = 'input-hint error';
        } else {
            passwordHint.textContent = '';
            passwordHint.className = 'input-hint';
        }

        // Enable button only if all fields are filled and passwords match
        const isFormValid = oldPasswordInput.value.length > 0 &&
            newPassword.length >= 8 &&
            newPassword === confirmPassword;

        savePasswordButton.disabled = !isFormValid;
    }

    // --- Initial Load ---
    loadUserData();
}); 
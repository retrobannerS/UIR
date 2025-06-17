document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    const token = localStorage.getItem('accessToken');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Elements
    const submitButton = document.getElementById('submit-button');
    const showSqlButton = document.getElementById('show-sql-button');
    const exportButton = document.getElementById('export-button');
    const queryInput = document.getElementById('query-input');
    const sqlOutput = document.getElementById('sql-output');
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name');
    const uploadButton = document.getElementById('upload-button');
    const tablesList = document.getElementById('tables-list');
    const userAvatar = document.getElementById('user-avatar');
    const logoutButton = document.getElementById('logout-button');
    const userMenu = document.getElementById('user-menu');
    const userProfile = document.querySelector('.user-profile');

    // Load user info
    loadUserInfo();
    // Load tables on page load
    if (tablesList) {
        loadTables();
    }

    // Event Listeners
    if (logoutButton) logoutButton.addEventListener('click', handleLogout);
    if (showSqlButton) showSqlButton.addEventListener('click', toggleSqlView);
    if (exportButton) exportButton.addEventListener('click', handleExport);

    // Handle file input changes only if the element exists
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                fileNameDisplay.textContent = fileInput.files[0].name;
                uploadButton.disabled = false;
            } else {
                fileNameDisplay.textContent = 'Файл не выбран';
                uploadButton.disabled = true;
            }
        });
    }

    // Handle file upload only if the form exists
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const file = fileInput.files[0];
            if (!file) {
                alert('Пожалуйста, выберите файл.');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/v1/tables/upload', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                alert('Таблица успешно загружена!');
                fileInput.value = '';
                fileNameDisplay.textContent = 'Файл не выбран';
                uploadButton.disabled = true;
                await loadTables();
            } catch (error) {
                console.error('Ошибка при загрузке файла:', error);
                alert(`Ошибка при загрузке файла: ${error.message}`);
            }
        });
    }

    // Load tables from the server
    async function loadTables() {
        try {
            const response = await fetch('/api/v1/tables/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const tables = await response.json();
            displayTables(tables);
        } catch (error) {
            console.error('Ошибка при загрузке списка таблиц:', error);
            tablesList.innerHTML = '<p class="error">Ошибка при загрузке списка таблиц</p>';
        }
    }

    // Display tables in the UI
    function displayTables(tables) {
        if (!tables || tables.length === 0) {
            tablesList.innerHTML = '<p class="no-tables">Нет загруженных таблиц</p>';
            return;
        }

        tablesList.innerHTML = tables.map(table => `
            <div class="table-item">
                <span>${table.name}</span>
                <button onclick="deleteTable('${table.name}')">Удалить</button>
            </div>
        `).join('');
    }

    // Delete table
    window.deleteTable = async (tableName) => {
        if (!confirm(`Удалить таблицу "${tableName}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/tables/${tableName}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            await loadTables();
        } catch (error) {
            console.error('Ошибка при удалении таблицы:', error);
            alert('Произошла ошибка при удалении таблицы.');
        }
    };

    // Handle SQL generation only if the button exists
    if (submitButton) {
        submitButton.addEventListener('click', async () => {
            const naturalQuery = queryInput.value;
            if (!naturalQuery) {
                alert('Пожалуйста, введите запрос.');
                return;
            }

            sqlOutput.textContent = 'Генерация...';

            try {
                const response = await fetch('/api/v1/tables/generate-sql', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ query: naturalQuery }),
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                sqlOutput.textContent = data.sql_query;

            } catch (error) {
                console.error('Ошибка при выполнении запроса:', error);
                sqlOutput.textContent = 'Произошла ошибка. Пожалуйста, посмотрите в консоль.';
            }
        });
    }

    // Load user info
    async function loadUserInfo() {
        try {
            const response = await fetch('/api/v1/users/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                // If the token is invalid, redirect to login
                if (response.status === 401 || response.status === 403) {
                    handleLogout();
                }
                throw new Error('Failed to load user info');
            }

            const user = await response.json();

            if (userAvatar) {
                userAvatar.innerHTML = ''; // Очищаем старое содержимое
                if (user.avatar_url) {
                    const avatarImg = document.createElement('img');
                    avatarImg.src = user.avatar_url;
                    avatarImg.alt = user.username;
                    avatarImg.classList.add('user-avatar-img');
                    userAvatar.appendChild(avatarImg);
                } else {
                    // Запасной вариант, если URL аватара отсутствует
                    const firstLetter = user.username.charAt(0).toUpperCase();
                    userAvatar.textContent = firstLetter;
                }
            }

        } catch (error) {
            console.error('Error loading user info:', error);
            handleLogout();
        }
    }

    // Handle logout
    function handleLogout() {
        localStorage.removeItem('accessToken');
        window.location.href = '/login';
    }

    // Toggle SQL view
    function toggleSqlView() {
        const resultBox = document.querySelector('.result-box');
        resultBox.classList.toggle('show-sql');
    }

    // Handle export
    function handleExport() {
        // Implementation for CSV export will go here
        alert('Export functionality will be implemented soon');
    }

    // --- User Menu Dropdown Logic ---
    if (userAvatar && userMenu) {
        userAvatar.addEventListener('click', (event) => {
            // Toggle the dropdown
            userMenu.classList.toggle('show');
        });

        // Close the dropdown if the user clicks outside of it
        window.addEventListener('click', (event) => {
            if (userProfile && !userProfile.contains(event.target) && userMenu.classList.contains('show')) {
                userMenu.classList.remove('show');
            }
        });
    }
}); 
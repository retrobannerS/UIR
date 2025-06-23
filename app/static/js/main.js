document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('accessToken');

    // --- Authentication Check ---
    if (!token && !window.location.pathname.includes('/login')) {
        window.location.href = '/login';
        return;
    }

    if (token && window.location.pathname.includes('/login')) {
        window.location.href = '/queries';
        return;
    }

    // If we are on the login page, we don't need to run the rest of the script
    if (!token) return;

    // --- Page-specific Elements ---
    const userMenu = document.getElementById('user-menu');
    const userAvatarPlaceholder = document.getElementById('user-avatar');
    const logoutButton = document.getElementById('logout-button');
    const userProfile = document.querySelector('.user-profile');
    const queryInput = document.getElementById('query-input');
    const submitButton = document.getElementById('submit-button');
    const sqlOutput = document.getElementById('sql-output');
    const tablesListSidebar = document.getElementById('tables-list-sidebar');
    const noTablesPlaceholder = document.querySelector('.no-tables-placeholder');

    // Modal elements
    const addTableModal = document.getElementById('add-table-modal');
    const cancelUploadBtn = document.getElementById('cancel-upload-btn');
    const confirmUploadBtn = document.getElementById('confirm-upload-btn');
    const fileUploadInput = document.getElementById('file-upload-input');
    const tableNameInput = document.getElementById('table-name-input');
    const addTableBtn = document.getElementById('add-table-btn');
    const tablePreviewContainer = document.getElementById('table-preview-container');
    const tablePreview = document.getElementById('table-preview');
    const tablePreviewPlaceholder = document.getElementById('table-preview-placeholder');
    const uploadErrorMessage = document.getElementById('upload-error-message');
    const previewRowsSelect = document.getElementById('preview-rows-select');

    let selectedTable = null;
    let selectedFile = null;

    // --- Global Functions ---
    function handleLogout() {
        localStorage.removeItem('accessToken');
        window.location.href = '/login';
    }

    function updateTopBarAvatar(user) {
        if (!userAvatarPlaceholder) return;
        userAvatarPlaceholder.innerHTML = ''; // Clear current content

        if (user && user.avatar_url) {
            const avatarImg = document.createElement('img');
            avatarImg.src = `${user.avatar_url}?t=${new Date().getTime()}`;
            avatarImg.alt = user.username;
            avatarImg.className = 'user-avatar-img';
            userAvatarPlaceholder.appendChild(avatarImg);
        } else if (user && user.username) {
            const firstLetter = user.username.charAt(0).toUpperCase();
            userAvatarPlaceholder.textContent = firstLetter;
            let hash = 0;
            for (let i = 0; i < user.username.length; i++) {
                hash = user.username.charCodeAt(i) + ((hash << 5) - hash);
            }
            const colors = ['#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#34495e', '#f1c40f', '#e67e22', '#e74c3c'];
            userAvatarPlaceholder.style.backgroundColor = colors[Math.abs(hash) % colors.length];
            userAvatarPlaceholder.style.color = 'white';
        }
    }

    // --- Table Management ---

    async function loadUserTables() {
        try {
            const token = localStorage.getItem('accessToken');
            const response = await fetch('/api/v1/tables/', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                throw new Error('Could not fetch tables.');
            }

            const tables = await response.json();
            const tableList = document.getElementById('tables-list-sidebar');
            if (!tableList) return;

            tableList.innerHTML = ''; // Clear existing list

            if (tables.length === 0) {
                if (noTablesPlaceholder) noTablesPlaceholder.style.display = 'list-item';
            } else {
                if (noTablesPlaceholder) noTablesPlaceholder.style.display = 'none';

                tables.forEach(table => {
                    const listItem = document.createElement('li');
                    listItem.className = 'table-list-item';
                    listItem.dataset.tableId = table.id;
                    listItem.dataset.tableName = table.table_name;

                    const tableLink = document.createElement('a');
                    tableLink.href = '#';
                    tableLink.className = 'table-list-link';
                    tableLink.textContent = table.table_name;

                    tableLink.onclick = (e) => {
                        e.preventDefault();
                        setActiveTable(listItem);
                    };

                    const actionsDiv = document.createElement('div');
                    actionsDiv.className = 'table-actions';
                    actionsDiv.innerHTML = `
                        <button class="icon-button edit-table-btn" title="Переименовать"><i class="fas fa-pencil-alt"></i></button>
                        <button class="icon-button delete-table-btn" title="Удалить"><i class="fas fa-trash"></i></button>
                    `;

                    actionsDiv.querySelector('.edit-table-btn').onclick = (e) => {
                        e.stopPropagation();
                        handleRenameClick(listItem, table.id, table.table_name);
                    };

                    actionsDiv.querySelector('.delete-table-btn').onclick = (e) => {
                        e.stopPropagation();
                        deleteTable(table.id, table.table_name);
                    };

                    listItem.appendChild(tableLink);
                    listItem.appendChild(actionsDiv);
                    tableList.appendChild(listItem);
                });
            }
        } catch (error) {
            console.error('Error loading user tables:', error);
        }
    }

    function setActiveTable(selectedListItem) {
        const allItems = document.querySelectorAll('#tables-list-sidebar .table-list-item');
        allItems.forEach(item => {
            item.classList.remove('active');
        });

        if (selectedListItem) {
            selectedListItem.classList.add('active');
            const tableName = selectedListItem.dataset.tableName;
            console.log(`Table "${tableName}" is now active.`);
        }
    }

    function validateTableName(name) {
        const trimmedName = name.trim();
        if (trimmedName.length < 3 || trimmedName.length > 50) {
            return "Имя должно содержать от 3 до 50 символов.";
        }
        if (!/^[a-zA-Z0-9_]+$/.test(trimmedName)) {
            return "Имя может содержать только латинские буквы, цифры и символ подчеркивания.";
        }
        return null;
    }

    function handleRenameClick(listItem, tableId, currentName) {
        const tableLink = listItem.querySelector('.table-list-link');
        const actionsDiv = listItem.querySelector('.table-actions');

        // Hide link and actions
        tableLink.style.display = 'none';
        if (actionsDiv) actionsDiv.style.display = 'none';

        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentName;
        input.className = 'rename-input'; // Ensure you have styles for this class

        // Insert input after the link
        listItem.insertBefore(input, tableLink.nextSibling);
        input.focus();
        input.select();

        const saveRename = async () => {
            const newName = input.value.trim();

            // Re-show link and actions
            listItem.removeChild(input);
            tableLink.style.display = '';
            if (actionsDiv) actionsDiv.style.display = '';

            if (newName && newName !== currentName) {
                const validationError = validateTableName(newName);
                if (validationError) {
                    alert(`Ошибка валидации: ${validationError}`);
                    return;
                }

                try {
                    const response = await fetch(`/api/v1/tables/${tableId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({ table_name: newName })
                    });

                    if (!response.ok) {
                        const err = await response.json();
                        // More specific error for unique constraint
                        if (err.detail && err.detail.includes("already exists")) {
                            throw new Error(`Таблица с именем "${newName}" уже существует.`);
                        }
                        throw new Error(err.detail || 'Не удалось переименовать таблицу.');
                    }

                    const updatedTable = await response.json();
                    // On success, update UI from response
                    tableLink.textContent = updatedTable.table_name;
                    listItem.dataset.tableName = updatedTable.table_name;

                } catch (error) {
                    console.error('Rename error:', error);
                    alert(`Ошибка: ${error.message}`);
                }
            }
        };

        input.addEventListener('blur', saveRename);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                input.blur(); // Trigger save
            } else if (e.key === 'Escape') {
                // Restore original view without saving
                listItem.removeChild(input);
                tableLink.style.display = '';
                if (actionsDiv) actionsDiv.style.display = '';
            }
        });
    }

    async function deleteTable(tableId, tableName) {
        if (!confirm(`Вы уверены, что хотите удалить таблицу "${tableName}"?`)) return;

        try {
            const response = await fetch(`/api/v1/tables/${tableId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Не удалось удалить таблицу.');
            }

            if (selectedTable === tableName) {
                selectedTable = null;
                localStorage.removeItem('selectedTableName');
            }

            loadUserTables(); // Refresh the list
        } catch (error) {
            console.error('Error deleting table:', error);
            alert(`Ошибка: ${error.message}`);
        }
    }

    // --- Modal Logic ---
    function openModal() {
        addTableModal.style.display = 'flex';
        tablePreviewPlaceholder.style.display = 'block';
        tablePreview.style.display = 'none';
    }

    function closeModal() {
        addTableModal.style.display = 'none';
        resetUploadForm();
    }

    function resetUploadForm() {
        selectedFile = null;
        fileUploadInput.value = '';
        tableNameInput.value = '';
        tableNameInput.disabled = true;
        confirmUploadBtn.disabled = true;
        uploadErrorMessage.style.display = 'none';
        uploadErrorMessage.textContent = '';

        // Reset and hide preview
        tablePreview.style.display = 'none';
        tablePreview.querySelector('thead').innerHTML = '';
        tablePreview.querySelector('tbody').innerHTML = '';

        // Show placeholder
        tablePreviewPlaceholder.style.display = 'block';
    }

    async function handleFileSelect(file) {
        if (!file) return;

        selectedFile = file;
        const baseName = file.name.substring(0, file.name.lastIndexOf('.'));
        tableNameInput.value = baseName;
        tableNameInput.disabled = false;

        // Immediately check the default name
        const validationError = validateTableName(baseName);
        if (validationError) {
            uploadErrorMessage.textContent = validationError;
            uploadErrorMessage.style.display = 'block';
            confirmUploadBtn.disabled = true;
        } else {
            uploadErrorMessage.style.display = 'none';
            confirmUploadBtn.disabled = false;
        }

        // Show loading state for preview
        tablePreviewPlaceholder.innerHTML = '<i class="fas fa-spinner fa-spin"></i><p>Загрузка предпросмотра...</p>';
        tablePreviewPlaceholder.style.display = 'flex';
        tablePreview.style.display = 'none';

        const formData = new FormData();
        formData.append('file', file);

        if (previewRowsSelect) {
            const previewRows = previewRowsSelect.value;
            formData.append('preview_rows', previewRows);
        }

        try {
            const response = await fetch('/api/v1/tables/preview', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                const errorMessage = err.detail || 'Не удалось создать предпросмотр.';
                uploadErrorMessage.textContent = errorMessage;
                uploadErrorMessage.style.display = 'block';

                // Reset state
                fileUploadInput.value = '';
                selectedFile = null;
                tableNameInput.value = '';
                tableNameInput.disabled = true;
                confirmUploadBtn.disabled = true;
                tablePreview.style.display = 'none';
                tablePreviewPlaceholder.style.display = 'block';
                return;
            }

            const { header, data } = await response.json();

            // Show table preview, hide placeholder
            tablePreviewPlaceholder.style.display = 'none';
            tablePreview.style.display = 'table';

            const thead = tablePreview.querySelector('thead');
            const tbody = tablePreview.querySelector('tbody');
            thead.innerHTML = '';
            tbody.innerHTML = '';

            const headerRow = document.createElement('tr');
            header.forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);

            data.forEach(rowData => {
                const row = document.createElement('tr');
                rowData.forEach(cellData => {
                    const td = document.createElement('td');
                    td.textContent = cellData;
                    row.appendChild(td);
                });
                tbody.appendChild(row);
            });

            tableNameInput.disabled = false; // Enable input
            confirmUploadBtn.disabled = false;
        } catch (error) {
            console.error('Error during preview:', error);
            uploadErrorMessage.textContent = 'Произошла ошибка при создании предпросмотра.';
            uploadErrorMessage.style.display = 'block';

            // Reset state
            fileUploadInput.value = '';
            selectedFile = null;
            tableNameInput.value = '';
            tableNameInput.disabled = true;
            confirmUploadBtn.disabled = true;
            tablePreview.style.display = 'none';
            tablePreviewPlaceholder.style.display = 'block';
        }
    }

    function onPreviewSettingsChange() {
        const file = fileUploadInput.files[0];
        if (file) {
            handleFileSelect(file);
        }
    }

    async function uploadFile() {
        if (!selectedFile || !tableNameInput.value) {
            alert('Пожалуйста, выберите файл и укажите имя таблицы.');
            return;
        }

        const validationError = validateTableName(tableNameInput.value);
        if (validationError) {
            uploadErrorMessage.textContent = validationError;
            uploadErrorMessage.style.display = 'block';
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        const tableName = tableNameInput.value.trim();
        if (tableName) {
            formData.append('table_name', tableName);
        }

        try {
            const response = await fetch('/api/v1/tables/upload', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                const errorMessage = err.detail || 'Не удалось загрузить файл.';
                uploadErrorMessage.textContent = errorMessage;
                uploadErrorMessage.style.display = 'block';
                throw new Error(errorMessage);
            }
            // Success
            closeModal();
            loadUserTables();

        } catch (error) {
            console.error('Upload error:', error);
            if (!uploadErrorMessage.textContent) {
                uploadErrorMessage.textContent = 'Произошла непредвиденная ошибка при загрузке.';
                uploadErrorMessage.style.display = 'block';
            }
        } finally {
            confirmUploadBtn.disabled = false;
            confirmUploadBtn.innerHTML = '<i class="fas fa-check"></i> Загрузить';
        }
    }

    async function handleSubmitQuery() {
        const naturalQuery = queryInput.value.trim();
        if (!naturalQuery) {
            sqlOutput.textContent = 'Пожалуйста, введите запрос.';
            return;
        }
        if (!selectedTable) {
            sqlOutput.textContent = 'Пожалуйста, выберите таблицу из списка слева.';
            return;
        }
        sqlOutput.textContent = 'Генерация SQL...';
        try {
            const response = await fetch('/api/v1/query/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    natural_language_query: naturalQuery,
                    table_name: selectedTable
                })
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка при генерации SQL.');
            }
            const data = await response.json();
            sqlOutput.textContent = data.sql_query;
        } catch (error) {
            console.error('Error submitting query:', error);
            sqlOutput.textContent = `Ошибка: ${error.message}`;
        }
    }

    // --- Initialization ---

    document.addEventListener('userDataUpdated', (event) => {
        const user = event.detail;
        if (user) {
            updateTopBarAvatar(user);
        }
    });

    if (tablesListSidebar) {
        loadUserTables();
    }

    // --- Event Listeners ---
    if (userProfile) {
        userProfile.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('show');
        });
        logoutButton.addEventListener('click', handleLogout);
    }

    // Close dropdown when clicking outside
    window.addEventListener('click', (e) => {
        if (userMenu && !userMenu.contains(e.target) && !userProfile.contains(e.target)) {
            userMenu.classList.remove('show');
        }
    });

    if (addTableBtn) {
        addTableBtn.addEventListener('click', openModal);
    }

    // Modal listeners
    if (addTableModal) {
        // Close modal on overlay click
        window.addEventListener('click', (event) => {
            if (event.target === addTableModal) {
                closeModal();
            }
        });

        // Wire up modal buttons
        confirmUploadBtn.addEventListener('click', uploadFile);
        cancelUploadBtn.addEventListener('click', closeModal);

        if (previewRowsSelect) {
            previewRowsSelect.addEventListener('change', onPreviewSettingsChange);
        }

        // The 'Выбрать файл' is a label for this input, so clicking it works automatically
        fileUploadInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });

        // Drag and drop listeners on the modal content area
        addTableModal.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            tablePreviewContainer.classList.add('drag-over');
        });

        addTableModal.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            tablePreviewContainer.classList.remove('drag-over');
        });

        addTableModal.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            tablePreviewContainer.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                fileUploadInput.files = e.dataTransfer.files;
                handleFileSelect(e.dataTransfer.files[0]);
            }
        });
    }

    if (queryInput) {
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSubmitQuery();
            }
        });
        // ... (весь код до этого момента) ...

        submitButton.addEventListener('click', handleSubmitQuery);
    }

    // Add event listener for table name input
    tableNameInput.addEventListener('input', () => {
        const validationError = validateTableName(tableNameInput.value);
        if (validationError) {
            uploadErrorMessage.textContent = validationError;
            uploadErrorMessage.style.display = 'block';
            confirmUploadBtn.disabled = true;
        } else {
            uploadErrorMessage.style.display = 'none';
            // Only enable if a file is also selected
            if (selectedFile) {
                confirmUploadBtn.disabled = false;
            }
        }
    });

    // --- Initial Load ---
    fetchAndSetUserData(); // From user-data.js
    loadUserTables();

});
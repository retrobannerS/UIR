// This module centralizes user data management for the entire application.
// It fetches user data once, stores it, and provides a single source of truth.
// It uses custom events to notify other parts of the application about data updates.

const AppData = {
    user: {
        _data: null,
        _promise: null,

        // Fetches user data from the API. Returns a promise that resolves with the user data.
        // It ensures data is fetched only once and caches the promise.
        async get() {
            if (this._promise) {
                return this._promise;
            }

            const token = localStorage.getItem('accessToken');
            if (!token) {
                return Promise.resolve(null);
            }

            this._promise = (async () => {
                try {
                    const response = await fetch('/api/v1/users/me', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });

                    if (!response.ok) {
                        if (response.status === 401 || response.status === 403) {
                            localStorage.removeItem('accessToken');
                            window.location.href = '/login';
                        }
                        throw new Error(`Failed to fetch user data: ${response.statusText}`);
                    }

                    const userData = await response.json();
                    this._data = userData;
                    document.dispatchEvent(new CustomEvent('userDataUpdated', { detail: this._data }));
                    return this._data;

                } catch (error) {
                    console.error('User data fetch error:', error);
                    this._promise = null; // Allow retry on failure
                    return null;
                }
            })();

            return this._promise;
        },

        // Updates the local user data and notifies listeners.
        // This is called after a successful update operation (e.g., changing username or avatar).
        set(newUserData) {
            this._data = newUserData;
            // We create a new resolved promise with the fresh data for any subsequent calls to get().
            this._promise = Promise.resolve(this._data);
            document.dispatchEvent(new CustomEvent('userDataUpdated', { detail: this._data }));
        },
    }
};

// Trigger the initial fetch as soon as the script loads.
AppData.user.get(); 
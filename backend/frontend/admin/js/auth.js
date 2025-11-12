class AuthAdmin {
    constructor() {
        this.token = null;
        this.currentUser = null;
        this.apiBaseUrl = '/api'; // ✅ Always use relative API path, works on Render & localhost

        // Decide whether to show login or dashboard
        if (window.location.pathname === '/admin/login.html' || window.location.pathname.endsWith('/admin/login')) {
            this.initLogin();
        } else {
            this.checkAuthentication();
        }
    }

    // ✅ Initialize login page listeners
    initLogin() {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // Auto-redirect if already logged in
        this.token = sessionStorage.getItem('admin_token');
        if (this.token) {
            window.location.href = '/admin';
        }
    }

    // ✅ Handle login form submission
    async handleLogin() {
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value.trim();
        const submitBtn = document.querySelector('#loginForm button[type="submit"]');

        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span> Signing In...</span>';
        submitBtn.disabled = true;

        try {
            const response = await fetch(`${this.apiBaseUrl}/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.access_token;
                this.currentUser = data.user;

                // Save login data
                sessionStorage.setItem('admin_token', this.token);
                sessionStorage.setItem('admin_user', JSON.stringify(this.currentUser));

                // Redirect to admin dashboard
                window.location.href = '/admin';
            } else {
                this.showNotification(data.error || 'Invalid credentials', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    // ✅ Check authentication before showing dashboard
    checkAuthentication() {
        this.token = sessionStorage.getItem('admin_token');
        this.currentUser = JSON.parse(sessionStorage.getItem('admin_user') || 'null');

        if (!this.token || !this.currentUser) {
            window.location.href = '/admin/login.html';
            return;
        }

        this.initDashboard();
    }

    // ✅ Initialize dashboard (show name, bind logout)
    initDashboard() {
        const adminNameElement = document.getElementById('current-admin-name');
        if (adminNameElement && this.currentUser) {
            adminNameElement.textContent = this.currentUser.name;
        }

        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    // ✅ Logout
    logout() {
        sessionStorage.removeItem('admin_token');
        sessionStorage.removeItem('admin_user');
        this.showNotification('Logged out successfully', 'success');
        setTimeout(() => {
            window.location.href = '/admin/login.html';
        }, 800);
    }

    // ✅ Make API calls with JWT
    async makeAuthenticatedRequest(url, options = {}) {
        if (!this.token) {
            this.checkAuthentication();
            throw new Error('Not authenticated');
        }

        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
                ...options.headers,
            },
        };

        const response = await fetch(`${this.apiBaseUrl}${url}`, {
            ...defaultOptions,
            ...options,
        });

        if (response.status === 401) {
            this.logout();
            throw new Error('Authentication expired');
        }

        return response;
    }

    // ✅ Custom notification UI
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-transform duration-300 ${
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'success' ? 'bg-green-500 text-white' :
            'bg-blue-500 text-white'
        }`;

        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas fa-${type === 'error' ? 'exclamation-triangle' :
                    type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 4000);
    }
}

// ✅ Initialize authentication on page load
const auth = new AuthAdmin();

class AuthSuperAdmin {
    constructor() {
        this.token = null;
        this.currentUser = null;

        // If on login page → run login mode
        if (window.location.pathname.includes('/super_admin/login')) {
            this.initLogin();
        } else {
            this.checkAuthentication();
        }
    }

    // ------------------------------
    // LOGIN PAGE INITIALIZATION
    // ------------------------------
    initLogin() {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // Already logged in?
        this.token = sessionStorage.getItem('super_admin_token');
        if (this.token) {
            window.location.href = '/super_admin';
        }
    }

    // ------------------------------
    // LOGIN HANDLER
    // ------------------------------
    async handleLogin() {
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value.trim();
        const submitBtn = document.querySelector('#loginForm button[type="submit"]');

        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/superadmin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                sessionStorage.setItem('super_admin_token', data.access_token);
                sessionStorage.setItem('super_admin_user', JSON.stringify(data.user));

                window.location.href = '/super_admin';
            } else {
                this.showNotification(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Network error. Try again.', 'error');
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    // ------------------------------
    // CHECK AUTH FOR DASHBOARD
    // ------------------------------
    checkAuthentication() {
        this.token = sessionStorage.getItem('super_admin_token');
        this.currentUser = JSON.parse(sessionStorage.getItem('super_admin_user') || 'null');

        if (!this.token || !this.currentUser) {
            window.location.href = '/super_admin/login.html';
            return;
        }

        this.initDashboard();
    }

    // ------------------------------
    // INITIALIZE DASHBOARD
    // ------------------------------
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

    // ------------------------------
    // LOGOUT
    // ------------------------------
    logout() {
        sessionStorage.removeItem('super_admin_token');
        sessionStorage.removeItem('super_admin_user');
        window.location.href = '/super_admin/login.html';
    }

    // ------------------------------
    // AUTH API REQUEST
    // ------------------------------
    async makeAuthenticatedRequest(url, options = {}) {
        if (!this.token) {
            this.logout();
            throw new Error('Not authenticated');
        }

        const response = await fetch(`/api${url}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options
        });

        if (response.status === 401) {
            this.logout();
            throw new Error('Session expired');
        }

        return response;
    }

    // ------------------------------
    // NOTIFICATION HANDLER
    // ------------------------------
    showNotification(message, type = 'info') {
        const box = document.createElement('div');
        box.className = `
            fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50
            transition-all duration-300
            ${type === 'error' ? 'bg-red-500 text-white' :
              type === 'success' ? 'bg-green-500 text-white' :
              'bg-blue-500 text-white'}
        `;

        box.innerHTML = `
            <div class="flex items-center gap-3">
                <i class="fas fa-${
                    type === 'error' ? 'exclamation-circle' :
                    type === 'success' ? 'check-circle' : 'info-circle'
                }"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(box);
        setTimeout(() => box.remove(), 4500);
    }
}

// Initialize globally
const auth = new AuthSuperAdmin();

class AuthSuperAdmin {
    constructor() {
        this.token = null;
        this.currentUser = null;
        this.apiBaseUrl = '';
        
        if (window.location.pathname === '/' || window.location.pathname.includes('login.html')) {
            this.initLogin();
        } else {
            this.checkAuthentication();
        }
    }

    initLogin() {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // Auto-redirect if already logged in
        this.token = sessionStorage.getItem('super_admin_token');
        if (this.token) {
            window.location.href = '/';
        }
    }

    async handleLogin() {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const submitBtn = document.querySelector('#loginForm button[type="submit"]');

        // Show loading state
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span> Signing In...</span>';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/superadmin/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                this.token = data.access_token;
                this.currentUser = data.user;
                
                sessionStorage.setItem('super_admin_token', this.token);
                sessionStorage.setItem('super_admin_user', JSON.stringify(this.currentUser));
                
                window.location.href = '/';
            } else {
                this.showNotification(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    checkAuthentication() {
        this.token = sessionStorage.getItem('super_admin_token');
        this.currentUser = JSON.parse(sessionStorage.getItem('super_admin_user') || 'null');

        if (!this.token || !this.currentUser) {
            window.location.href = '/';
            return;
        }

        this.initDashboard();
    }

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

    logout() {
        sessionStorage.removeItem('super_admin_token');
        sessionStorage.removeItem('super_admin_user');
        window.location.href = '/';
    }

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

        const response = await fetch(`/api${url}`, {
            ...defaultOptions,
            ...options,
        });

        if (response.status === 401) {
            this.logout();
            throw new Error('Authentication expired');
        }

        return response;
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transform transition-transform duration-300 ${
            type === 'error' ? 'bg-red-500 text-white' : 
            type === 'success' ? 'bg-green-500 text-white' : 
            'bg-blue-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

const auth = new AuthSuperAdmin();
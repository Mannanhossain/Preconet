class AuthAdmin {
    constructor() {
        this.token = null;
        this.currentUser = null;

        // Works on localhost + Render + Railway
        this.apiBaseUrl = '/api';

        // Normalize path for safe checking
        this.currentPath = window.location.pathname.replace(/\/+$/, "");

        // Decide login or dashboard
        if (this.isLoginPage()) {
            this.initLogin();
        } else {
            this.checkAuthentication();
        }
    }

    // ---------------------------------------------------------
    // PAGE MATCHING HELPERS
    // ---------------------------------------------------------

    isLoginPage() {
        return (
            this.currentPath === "/admin/login" ||
            this.currentPath === "/admin/login.html" ||
            this.currentPath.endsWith("/admin/login") ||
            this.currentPath.endsWith("/admin/login.html")
        );
    }

    isDashboardPage() {
        return (
            this.currentPath === "/admin" ||
            this.currentPath === "/admin/" ||
            this.currentPath.endsWith("/admin/index.html")
        );
    }

    // ---------------------------------------------------------
    // LOGIN PAGE INITIALIZATION
    // ---------------------------------------------------------

    initLogin() {
        const loginForm = document.getElementById("loginForm");

        if (loginForm) {
            loginForm.addEventListener("submit", (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // Auto redirect if already logged in
        this.token = sessionStorage.getItem("admin_token");
        if (this.token) {
            window.location.href = "/admin";
        }
    }

    // ---------------------------------------------------------
    // LOGIN HANDLER
    // ---------------------------------------------------------

    async handleLogin() {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();
        const submitBtn = document.querySelector('#loginForm button[type="submit"]');

        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
        submitBtn.disabled = true;

        try {
            const response = await fetch(`${this.apiBaseUrl}/admin/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                this.showNotification(data.error || "Invalid credentials", "error");
                return;
            }

            // Save token & user info
            this.token = data.access_token;
            this.currentUser = data.user;

            sessionStorage.setItem("admin_token", this.token);
            sessionStorage.setItem("admin_user", JSON.stringify(this.currentUser));

            // Redirect
            window.location.href = "/admin";

        } catch (error) {
            console.error("Login error:", error);
            this.showNotification("Network error. Please try again.", "error");

        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    // ---------------------------------------------------------
    // AUTH CHECK FOR DASHBOARD
    // ---------------------------------------------------------

    checkAuthentication() {
        try {
            this.token = sessionStorage.getItem("admin_token");
            this.currentUser = JSON.parse(sessionStorage.getItem("admin_user") || "null");
        } catch {
            this.token = null;
            this.currentUser = null;
        }

        if (!this.token || !this.currentUser) {
            window.location.href = "/admin/login.html";
            return;
        }

        if (this.isDashboardPage()) {
            this.initDashboard();
        }
    }

    // ---------------------------------------------------------
    // DASHBOARD INITIALIZATION
    // ---------------------------------------------------------

    initDashboard() {
        const adminNameElement = document.getElementById("current-admin-name");
        if (adminNameElement && this.currentUser) {
            adminNameElement.textContent = this.currentUser.name;
        }

        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => this.logout());
        }
    }

    // ---------------------------------------------------------
    // LOGOUT
    // ---------------------------------------------------------

    logout() {
        sessionStorage.removeItem("admin_token");
        sessionStorage.removeItem("admin_user");

        this.showNotification("Logged out successfully", "success");

        setTimeout(() => {
            window.location.href = "/admin/login.html";
        }, 700);
    }

    // ---------------------------------------------------------
    // AUTHENTICATED API REQUESTS
    // ---------------------------------------------------------

    async makeAuthenticatedRequest(url, options = {}) {
        if (!this.token) {
            this.logout();
            throw new Error("Not authenticated");
        }

        const response = await fetch(`${this.apiBaseUrl}${url}`, {
            ...options,
            headers: {
                "Authorization": `Bearer ${this.token}`,
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
        });

        // Token expired
        if (response.status === 401) {
            this.logout();
            throw new Error("Authentication expired");
        }

        return response;
    }

    // ---------------------------------------------------------
    // NOTIFICATION POPUP
    // ---------------------------------------------------------

    showNotification(message, type = "info") {
        const box = document.createElement("div");

        box.className = `
            fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white 
            transition-all duration-300 transform
            ${type === "error" ? "bg-red-500" :
               type === "success" ? "bg-green-500" :
               "bg-blue-500"}
        `;

        box.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-${type === "error" ? "exclamation-circle" :
                   type === "success" ? "check-circle" : "info-circle"}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(box);

        setTimeout(() => box.remove(), 3500);
    }
}

// Initialize on page load
const auth = new AuthAdmin();

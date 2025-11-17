class AuthSuperAdmin {
    constructor() {
        this.token = null;
        this.currentUser = null;

        // Works everywhere (local + Render)
        this.apiBaseUrl = "/api";

        // Normalize path
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
            this.currentPath === "/super_admin/login" ||
            this.currentPath === "/super_admin/login.html" ||
            this.currentPath.endsWith("/super_admin/login") ||
            this.currentPath.endsWith("/super_admin/login.html")
        );
    }

    isDashboardPage() {
        return (
            this.currentPath === "/super_admin" ||
            this.currentPath === "/super_admin/" ||
            this.currentPath.endsWith("/super_admin/index.html")
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

        // Already logged in?
        const savedToken = sessionStorage.getItem("super_admin_token");

        if (savedToken) {
            window.location.href = "/super_admin";
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
            const response = await fetch(`${this.apiBaseUrl}/superadmin/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                this.showNotification(data.error || "Invalid credentials", "error");
                return;
            }

            // Save the token and user
            sessionStorage.setItem("super_admin_token", data.access_token);
            sessionStorage.setItem("super_admin_user", JSON.stringify(data.user));

            // Redirect to dashboard
            window.location.href = "/super_admin";

        } catch (error) {
            console.error("Login failed:", error);
            this.showNotification("Network error. Try again.", "error");

        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    // ---------------------------------------------------------
    // CHECK AUTHENTICATION FOR DASHBOARD
    // ---------------------------------------------------------

    checkAuthentication() {
        try {
            this.token = sessionStorage.getItem("super_admin_token");
            this.currentUser = JSON.parse(sessionStorage.getItem("super_admin_user") || "null");
        } catch {
            this.token = null;
            this.currentUser = null;
        }

        // Not logged in → Redirect to login
        if (!this.token || !this.currentUser) {
            window.location.href = "/super_admin/login.html";
            return;
        }

        // If dashboard, initialize UI
        if (this.isDashboardPage()) {
            this.initDashboard();
        }
    }

    // ---------------------------------------------------------
    // INITIALIZE DASHBOARD
    // ---------------------------------------------------------

    initDashboard() {
        const nameElement = document.getElementById("current-superadmin-name");

        if (nameElement && this.currentUser) {
            nameElement.textContent = this.currentUser.name;
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
        sessionStorage.removeItem("super_admin_token");
        sessionStorage.removeItem("super_admin_user");

        this.showNotification("Logged out successfully", "success");

        setTimeout(() => {
            window.location.href = "/super_admin/login.html";
        }, 700);
    }

    // ---------------------------------------------------------
    // AUTHENTICATED API REQUEST
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

        if (response.status === 401) {
            this.logout();
            throw new Error("Session expired");
        }

        return response;
    }

    // ---------------------------------------------------------
    // NOTIFICATION HANDLER
    // ---------------------------------------------------------

    showNotification(message, type = "info") {
        const box = document.createElement("div");

        box.className = `
            fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white
            transition-all duration-300 transform
            ${type === "error" ? "bg-red-500"
                : type === "success" ? "bg-green-500"
                : "bg-blue-500"}
        `;

        box.innerHTML = `
            <div class="flex items-center gap-2">
                <i class="fas fa-${type === "error" ? "exclamation-circle" :
                    type === "success" ? "check-circle" : "info-circle"}"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(box);

        setTimeout(() => box.remove(), 3500);
    }
}

// Initialize
const auth = new AuthSuperAdmin();

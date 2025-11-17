class AuthAdmin {
    constructor() {
        this.token = null;
        this.currentUser = null;

        // Auto-detect backend URL
        this.apiBaseUrl = window.location.origin.includes("localhost")
            ? "http://localhost:5000/api"
            : "https://preconet-1.onrender.com/api";

        // Normalize path
        this.currentPath = window.location.pathname.replace(/\/+$/, "").toLowerCase();

        // Load page
        if (this.isLoginPage()) {
            this.initLogin();
        } else {
            this.checkAuthentication();
        }
    }

    /* --------------------------------------------------------
       PAGE DETECTION
    -------------------------------------------------------- */
    isLoginPage() {
        return (
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

    /* --------------------------------------------------------
       LOGIN PAGE
    -------------------------------------------------------- */
    initLogin() {
        const form = document.getElementById("loginForm");
        if (form) {
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }

        // Already logged in → redirect
        this.token = sessionStorage.getItem("admin_token");
        if (this.token) window.location.href = "/admin";
    }

    /* --------------------------------------------------------
       HANDLE LOGIN
    -------------------------------------------------------- */
    async handleLogin() {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();
        const btn = document.querySelector('#loginForm button[type="submit"]');

        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
        btn.disabled = true;

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

            // Save token & user
            this.token = data.access_token;
            this.currentUser = data.user;

            sessionStorage.setItem("admin_token", this.token);
            sessionStorage.setItem("admin_user", JSON.stringify(this.currentUser));

            window.location.href = "/admin";

        } catch (err) {
            console.error("Login Error:", err);
            this.showNotification("Network error. Please try again.", "error");
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }

    /* --------------------------------------------------------
       CHECK LOGIN STATUS ON DASHBOARD
    -------------------------------------------------------- */
    checkAuthentication() {
        try {
            this.token = sessionStorage.getItem("admin_token");
            this.currentUser = JSON.parse(sessionStorage.getItem("admin_user") || "{}");
        } catch {
            this.token = null;
            this.currentUser = null;
        }

        if (!this.token || !this.currentUser) {
            return (window.location.href = "/admin/login.html");
        }

        if (this.isDashboardPage()) {
            this.initDashboard();
        }
    }

    /* --------------------------------------------------------
       DASHBOARD INIT
    -------------------------------------------------------- */
    initDashboard() {
        const nameBox = document.getElementById("current-admin-name");
        if (nameBox && this.currentUser) {
            nameBox.textContent = this.currentUser.name;
        }

        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) logoutBtn.addEventListener("click", () => this.logout());
    }

    /* --------------------------------------------------------
       LOGOUT
    -------------------------------------------------------- */
    logout() {
        sessionStorage.removeItem("admin_token");
        sessionStorage.removeItem("admin_user");

        this.showNotification("Logged out successfully", "success");

        setTimeout(() => {
            window.location.href = "/admin/login.html";
        }, 500);
    }

    /* --------------------------------------------------------
       AUTH API REQUEST
    -------------------------------------------------------- */
    async makeAuthenticatedRequest(url, options = {}) {
        if (!this.token) {
            this.logout();
            throw new Error("Not authenticated");
        }

        try {
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
                throw new Error("Token expired");
            }

            return response;
        } catch (err) {
            this.showNotification("Network error", "error");
            throw err;
        }
    }

    /* --------------------------------------------------------
       NOTIFICATION
    -------------------------------------------------------- */
    showNotification(msg, type = "info") {
        const div = document.createElement("div");

        div.className = `
            fixed top-4 right-4 px-4 py-3 rounded-lg text-white shadow-lg z-50
            transition-all duration-300
            ${type === "error" ? "bg-red-600" :
              type === "success" ? "bg-green-600" :
              "bg-blue-600"}
        `;

        div.innerHTML = `
            <div class="flex items-center gap-2">
                <i class="fas fa-${type === "error" ? "exclamation-circle" :
                                type === "success" ? "check-circle" : "info-circle"}"></i>
                <span>${msg}</span>
            </div>
        `;

        document.body.appendChild(div);

        setTimeout(() => div.remove(), 3000);
    }
}

window.auth = new AuthAdmin();

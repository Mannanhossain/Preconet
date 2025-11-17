/************************************************************
 * AUTH SYSTEM (SUPER ADMIN + ADMIN)
 ************************************************************/

class AuthSystem {
    constructor() {
        this.tokenKeySuper = "super_admin_token";
        this.userKeySuper = "super_admin_user";

        this.tokenKeyAdmin = "admin_token";
        this.userKeyAdmin = "admin_user";
    }

    /************************************************************
     * GET CURRENT TOKEN (Auto detects super/admin)
     ************************************************************/
    getToken() {
        return (
            sessionStorage.getItem(this.tokenKeySuper) ||
            sessionStorage.getItem(this.tokenKeyAdmin)
        );
    }

    /************************************************************
     * GET CURRENT USER
     ************************************************************/
    getCurrentUser() {
        const superUser = sessionStorage.getItem(this.userKeySuper);
        if (superUser) return JSON.parse(superUser);

        const adminUser = sessionStorage.getItem(this.userKeyAdmin);
        if (adminUser) return JSON.parse(adminUser);

        return null;
    }

    /************************************************************
     * SAVE TOKEN (Auto detects superadmin or admin)
     ************************************************************/
    saveLogin(role, token, user) {
        if (role === "super_admin") {
            sessionStorage.setItem(this.tokenKeySuper, token);
            sessionStorage.setItem(this.userKeySuper, JSON.stringify(user));
        } else if (role === "admin") {
            sessionStorage.setItem(this.tokenKeyAdmin, token);
            sessionStorage.setItem(this.userKeyAdmin, JSON.stringify(user));
        }
    }

    /************************************************************
     * LOGOUT HANDLER
     ************************************************************/
    logout() {
        sessionStorage.removeItem(this.tokenKeySuper);
        sessionStorage.removeItem(this.userKeySuper);

        sessionStorage.removeItem(this.tokenKeyAdmin);
        sessionStorage.removeItem(this.userKeyAdmin);

        window.location.href = "/super_admin/login.html";
    }

    /************************************************************
     * MAKE AUTHENTICATED REQUEST
     ************************************************************/
    async makeAuthenticatedRequest(url, options = {}) {
        const token = this.getToken();

        if (!token) {
            console.warn("⚠ No token found → redirecting to login");
            this.logout();
            return;
        }

        const fullUrl = url.startsWith("/api") ? url : `/api${url}`;

        const defaultHeaders = {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        };

        options.headers = {
            ...defaultHeaders,
            ...(options.headers || {}),
        };

        const response = await fetch(fullUrl, options);

        // HANDLE TOKEN EXPIRED
        if (response.status === 401) {
            console.error("⚠ Unauthorized / Token expired");
            this.showNotification("Session expired. Please log in again.", "error");
            this.logout();
            return;
        }

        return response;
    }

    /************************************************************
     * NOTIFICATION SYSTEM
     ************************************************************/
    showNotification(message, type = "info") {
        const containerId = "notification-container";
        let container = document.getElementById(containerId);

        if (!container) {
            container = document.createElement("div");
            container.id = containerId;
            container.className = "fixed top-5 right-5 z-50 space-y-3";
            document.body.appendChild(container);
        }

        const colors = {
            success: "bg-green-600",
            error: "bg-red-600",
            info: "bg-blue-600",
            warning: "bg-yellow-500",
        };

        const notif = document.createElement("div");
        notif.className = `
            px-4 py-3 text-white rounded-lg shadow-lg flex items-center space-x-3 
            ${colors[type] || colors.info} animate-fade-in
        `;
        notif.innerHTML = `
            <i class="fas fa-info-circle"></i>
            <span>${message}</span>
        `;

        container.appendChild(notif);

        setTimeout(() => {
            notif.classList.add("opacity-0");
            setTimeout(() => notif.remove(), 500);
        }, 3500);
    }
}

const auth = new AuthSystem();

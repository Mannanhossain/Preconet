/* ================================
   AUTH UTILITIES (ADMIN PANEL)
================================ */

class Auth {
    constructor() {
        this.tokenKey = "admin_token";
        this.userKey = "admin_user";
        this.roleKey = "admin_role";
    }

    /* Save role + token + user */
    saveLogin(role, token, user) {
        sessionStorage.setItem(this.roleKey, role);
        sessionStorage.setItem(this.tokenKey, token);
        sessionStorage.setItem(this.userKey, JSON.stringify(user));
    }

    /* Get token */
    getToken() {
        return sessionStorage.getItem(this.tokenKey);
    }

    /* Get logged in admin */
    getCurrentUser() {
        const raw = sessionStorage.getItem(this.userKey);
        return raw ? JSON.parse(raw) : null;
    }

    /* Logout */
    logout() {
        sessionStorage.removeItem(this.roleKey);
        sessionStorage.removeItem(this.tokenKey);
        sessionStorage.removeItem(this.userKey);

        window.location.href = window.location.origin + "/admin/login.html";
    }

    /* Authenticated API request */
    async makeAuthenticatedRequest(url, options = {}) {
        const token = this.getToken();

        if (!token) {
            this.logout();
            return;
        }

        const fullUrl = url.startsWith("/") ? url : `/${url}`;

        const headers = {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
            ...(options.headers || {})
        };

        const resp = await fetch(fullUrl, { ...options, headers });

        if (resp.status === 401) {
            this.showNotification("Session expired — please login again", "error");
            this.logout();
        }

        return resp;
    }

    /* Notification */
    showNotification(message, type = "info") {
        let area = document.getElementById("notificationArea");

        if (!area) {
            area = document.createElement("div");
            area.id = "notificationArea";
            area.className = "fixed top-5 right-5 z-50 space-y-3";
            document.body.appendChild(area);
        }

        const palette = {
            success: "bg-green-600",
            error: "bg-red-600",
            info: "bg-blue-600",
            warning: "bg-yellow-500"
        };

        const div = document.createElement("div");
        div.className = `
            text-white px-4 py-2 rounded shadow transition
            ${palette[type] || palette.info}
        `;
        div.innerHTML = `
            <div class="flex items-center gap-3">
                <i class="fas fa-info-circle"></i>
                <span>${message}</span>
            </div>
        `;

        area.appendChild(div);

        setTimeout(() => {
            div.classList.add("opacity-0");
            setTimeout(() => div.remove(), 300);
        }, 3000);
    }
}

const auth = new Auth();

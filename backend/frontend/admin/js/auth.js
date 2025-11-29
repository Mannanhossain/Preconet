/* ================================
        AUTH UTILITIES (ADMIN PANEL)
   ================================= */

class Auth {
    constructor() {
        this.tokenKey = "admin_token";
        this.userKey = "admin_user";
        this.emailKey = "admin_email";   // NEW → Remember Email
    }

    /* ---------------------------------
        SAVE LOGIN (TOKEN + USER DATA)
        NOW USING localStorage → One-time login
    --------------------------------- */
    saveLogin(token, user) {
        localStorage.setItem(this.tokenKey, token);
        localStorage.setItem(this.userKey, JSON.stringify(user));

        // Save email for next login screen (not required but helpful)
        if (user?.email) {
            localStorage.setItem(this.emailKey, user.email);
        }
    }

    /* ---------------------------------
        GET LOGIN TOKEN
    --------------------------------- */
    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    /* ---------------------------------
        GET CURRENT LOGGED-IN ADMIN DATA
    --------------------------------- */
    getCurrentUser() {
        const raw = localStorage.getItem(this.userKey);
        return raw ? JSON.parse(raw) : null;
    }

    /* ---------------------------------
        LOGOUT (CLEAR EVERYTHING)
    --------------------------------- */
    logout() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        window.location.href = "/admin/login.html";
    }

    /* ---------------------------------
        REMEMBERED EMAIL FOR LOGIN FORM
    --------------------------------- */
    getRememberedEmail() {
        return localStorage.getItem(this.emailKey) || "";
    }


    /* ---------------------------------
        MAKE AUTHENTICATED REQUEST
        AUTO HANDLE TOKEN & 401 ERRORS
    --------------------------------- */
    async makeAuthenticatedRequest(url, options = {}) {
        const token = this.getToken();

        if (!token) {
            this.showNotification("Please login again", "error");
            this.logout();
            return;
        }

        const finalUrl = url.startsWith("/api") ? url : `/api${url}`;

        const headers = {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
            ...(options.headers || {})
        };

        const resp = await fetch(finalUrl, {
            ...options,
            headers,
        });

        if (resp.status === 401) {
            this.showNotification("Session expired — login again", "error");
            this.logout();
        }

        return resp;
    }


    /* ---------------------------------
        NOTIFICATION SYSTEM
    --------------------------------- */
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
            text-white px-4 py-3 rounded shadow-lg flex items-center gap-3 
            transition-all duration-300
            ${palette[type] || palette.info}
        `;
        div.innerHTML = `
            <i class="fas fa-circle-info"></i>
            <span>${message}</span>
        `;

        area.appendChild(div);

        setTimeout(() => {
            div.classList.add("opacity-0");
            setTimeout(() => div.remove(), 300);
        }, 3000);
    }
}

// GLOBAL INSTANCE
const auth = new Auth();

/* ---------------------------------
   AUTO REDIRECT (FOR ALL ADMIN PAGES)
---------------------------------- */

document.addEventListener("DOMContentLoaded", () => {
    const isLoginPage = window.location.pathname.includes("login");

    if (!isLoginPage && !auth.getToken()) {
        window.location.href = "/admin/login.html";
    }

    // Auto-fill email on login page
    if (isLoginPage) {
        const emailField = document.getElementById("email");
        if (emailField) {
            emailField.value = auth.getRememberedEmail();
        }
    }
});

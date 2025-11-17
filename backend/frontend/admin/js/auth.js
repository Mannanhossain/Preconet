/* AUTH UTILITIES (admin) */
class Auth {
  constructor() {
    this.tokenKey = "admin_token";
    this.userKey = "admin_user";
  }

  saveLogin(token, user) {
    sessionStorage.setItem(this.tokenKey, token);
    sessionStorage.setItem(this.userKey, JSON.stringify(user));
  }

  getToken() {
    return sessionStorage.getItem(this.tokenKey);
  }

  getCurrentUser() {
    const raw = sessionStorage.getItem(this.userKey);
    return raw ? JSON.parse(raw) : null;
  }

  logout() {
    sessionStorage.removeItem(this.tokenKey);
    sessionStorage.removeItem(this.userKey);
    // redirect to admin login page — adjust path if different
    window.location.href = "/admin/login.html";
  }

  async makeAuthenticatedRequest(url, options = {}) {
    const token = this.getToken();
    if (!token) {
      console.warn("No token — redirecting");
      this.logout();
      return;
    }

    const fullUrl = url.startsWith("/api") ? url : `/api${url}`;
    const headers = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
      ...(options.headers || {})
    };

    const resp = await fetch(fullUrl, { ...options, headers });

    // handle unauthorized centrally
    if (resp.status === 401) {
      this.showNotification("Session expired — please login again", "error");
      this.logout();
      return resp;
    }

    return resp;
  }

  showNotification(message, type="info") {
    const area = document.getElementById('notificationArea');
    if (!area) return;

    const palette = {
      success: "bg-green-600",
      error: "bg-red-600",
      info: "bg-blue-600",
      warning: "bg-yellow-500"
    };

    const div = document.createElement('div');
    div.className = `text-white px-4 py-2 rounded shadow notif-enter ${palette[type] || palette.info}`;
    div.innerHTML = `<div class="flex items-center gap-3"><i class="fas fa-info-circle"></i><div>${message}</div></div>`;
    area.appendChild(div);
    setTimeout(() => div.remove(), 3500);
  }
}

const auth = new Auth();

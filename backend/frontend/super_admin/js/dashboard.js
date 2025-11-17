class SuperAdminDashboard {
    constructor() {
        this.stats = null;
        this.init();
    }

    /* -------------------------------------------------------------
        INITIALIZE
    ------------------------------------------------------------- */
    async init() {
        await this.loadStats();
        this.setupNavigation();
        this.setupLogout();
        console.log("✅ Super Admin Dashboard Initialized");
    }

    /* -------------------------------------------------------------
        LOAD DASHBOARD STATS (Correct API)
    ------------------------------------------------------------- */
    async loadStats() {
        try {
            const response = await auth.makeAuthenticatedRequest(
                "/api/superadmin/dashboard-stats"
            );

            const data = await response.json();

            if (response.ok) {
                this.stats = data.stats;
                this.renderStats();
            } else {
                auth.showNotification(data.error || "Failed to load dashboard data", "error");
            }
        } catch (err) {
            console.error("Stats error:", err);
            auth.showNotification("Cannot load dashboard stats", "error");
        }
    }

    /* -------------------------------------------------------------
        RENDER STATS CARDS
    ------------------------------------------------------------- */
    renderStats() {
        const box = document.getElementById("stats-cards");
        if (!box || !this.stats) return;

        const s = this.stats;

        const items = [
            {
                label: "Total Admins",
                value: s.total_admins ?? 0,
                icon: "users-cog",
                bg: "bg-blue-50",
                text: "text-blue-600"
            },
            {
                label: "Total Users",
                value: s.total_users ?? 0,
                icon: "users",
                bg: "bg-green-50",
                text: "text-green-600"
            },
            {
                label: "Active Admins",
                value: s.active_admins ?? 0,
                icon: "user-check",
                bg: "bg-emerald-50",
                text: "text-emerald-600"
            },
            {
                label: "Expired Admins",
                value: s.expired_admins ?? 0,
                icon: "exclamation-triangle",
                bg: "bg-red-50",
                text: "text-red-600"
            }
        ];

        box.innerHTML = items
            .map(
                i => `
                <div class="bg-white rounded-xl shadow-sm p-6 border hover:shadow-md transition">
                    <div class="flex justify-between items-center">
                        <div>
                            <p class="text-gray-600 text-sm">${i.label}</p>
                            <p class="text-3xl font-bold mt-1">${i.value}</p>
                        </div>
                        <div class="${i.bg} w-12 h-12 rounded-lg flex items-center justify-center">
                            <i class="fas fa-${i.icon} ${i.text} text-xl"></i>
                        </div>
                    </div>
                </div>
            `
            )
            .join("");
    }

    /* -------------------------------------------------------------
        HANDLE NAVIGATION BETWEEN SECTIONS
    ------------------------------------------------------------- */
    setupNavigation() {
        const navItems = document.querySelectorAll(".nav-item");
        const title = document.getElementById("page-title");
        const subtitle = document.getElementById("page-subtitle");

        const pages = {
            dashboard: {
                title: "Dashboard Overview",
                subtitle: "Superadmin system summary",
                section: "dashboard-section"
            },
            admins: {
                title: "Administrators",
                subtitle: "Manage all admin accounts",
                section: "admins-section"
            },
            activity: {
                title: "Activity Logs",
                subtitle: "Track all system activity",
                section: "activity-section"
            }
        };

        navItems.forEach((item) => {
            item.addEventListener("click", (e) => {
                e.preventDefault();

                navItems.forEach((i) => i.classList.remove("active"));
                item.classList.add("active");

                const key = item.getAttribute("href").replace("#", "");
                const page = pages[key];

                if (page) {
                    title.textContent = page.title;
                    subtitle.textContent = page.subtitle;
                    this.showSection(key);
                }
            });
        });
    }

    /* -------------------------------------------------------------
        SHOW SELECTED SECTION + AUTO REFRESH
    ------------------------------------------------------------- */
    showSection(section) {
        const all = ["dashboard", "admins", "activity"];

        all.forEach(sec => {
            const el = document.getElementById(`${sec}-section`);
            if (el) el.classList.add("hidden");
        });

        document.getElementById(`${section}-section`).classList.remove("hidden");

        // Auto-load page data
        if (section === "admins" && window.adminsManager)
            adminsManager.loadAdmins();

        if (section === "activity" && window.activityManager)
            activityManager.loadActivity();
    }

    /* -------------------------------------------------------------
        LOGOUT HANDLER
    ------------------------------------------------------------- */
    setupLogout() {
        const logoutSidebar = document.getElementById("logout-btn-sidebar");
        const logoutHeader = document.getElementById("logout-btn-header");

        const logout = () => {
            sessionStorage.removeItem("super_admin_token");
            sessionStorage.removeItem("super_admin_user");
            window.location.href = "/super_admin/login.html";
        };

        if (logoutSidebar) logoutSidebar.onclick = logout;
        if (logoutHeader) logoutHeader.onclick = logout;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.superAdminDashboard = new SuperAdminDashboard();
});

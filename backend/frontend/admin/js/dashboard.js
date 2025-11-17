class Dashboard {
    constructor() {
        this.stats = null;
        this.recentSync = [];
        this.userLogs = [];

        window.dashboard = this;
        this.init();
    }

    async init() {
        if (!this.checkAuth()) return;

        await this.loadStats();
        await this.loadRecentSync();
        await this.loadUserLogs();
        this.renderPerformanceChart();
    }

    checkAuth() {
        const token = sessionStorage.getItem("admin_token");
        if (!token) {
            window.location.href = "/admin/login.html";
            return false;
        }
        return true;
    }

    /* ============================
       LOAD DASHBOARD STATS
    ============================ */
    async loadStats() {
        try {
            const resp = await auth.makeAuthenticatedRequest(`/api/admin/dashboard-stats`);
            const data = await resp.json();

            if (!resp.ok) {
                console.error("Dashboard Stats Error:", data);
                return;
            }

            this.stats = data.stats;
            this.renderStatsCards();

        } catch (err) {
            console.error("Stats Load Error:", err);
        }
    }

    /* ============================
       RENDER DASHBOARD CARDS
    ============================ */
    renderStatsCards() {
        const container = document.getElementById("stats-cards");
        if (!container) return;

        const s = this.stats;

        const cards = [
            {
                title: "Total Users",
                value: s.total_users,
                icon: "users",
                color: "blue"
            },
            {
                title: "Active Users",
                value: s.active_users,
                icon: "user-check",
                color: "green"
            },
            {
                title: "Users With Sync",
                value: s.users_with_sync,
                icon: "sync",
                color: "purple"
            },
            {
                title: "Remaining Slots",
                value: s.remaining_slots,
                icon: "user-plus",
                color: "orange"
            }
        ];

        container.innerHTML = cards.map(card => `
            <div class="floating-card bg-white p-6 rounded-xl shadow-md border border-gray-200">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="text-sm text-gray-500">${card.title}</p>
                        <p class="text-3xl font-bold text-gray-800 mt-1">${card.value}</p>
                    </div>

                    <div class="w-12 h-12 bg-${card.color}-100 text-${card.color}-600 rounded-xl
                                flex items-center justify-center">
                        <i class="fas fa-${card.icon} text-xl"></i>
                    </div>
                </div>
            </div>
        `).join("");
    }

    /* ============================
       RECENT USER SYNC
    ============================ */
    async loadRecentSync() {
        try {
            const resp = await auth.makeAuthenticatedRequest(`/api/admin/recent-sync`);
            const data = await resp.json();

            if (!resp.ok) return;

            this.recentSync = data.recent_sync;
            this.renderRecentSync();

        } catch (err) {
            console.error("Recent Sync Error:", err);
        }
    }

    renderRecentSync() {
        const container = document.getElementById("recent-sync-list");
        if (!container) return;

        if (this.recentSync.length === 0) {
            container.innerHTML = `<p class="text-gray-500 text-sm">No recent sync activity.</p>`;
            return;
        }

        container.innerHTML = this.recentSync.map(item => `
            <div class="p-4 bg-gray-50 rounded-lg border flex justify-between items-center">
                <div>
                    <h4 class="font-semibold text-gray-800">${item.name}</h4>
                    <p class="text-xs text-gray-500">Last Sync: ${new Date(item.last_sync).toLocaleString()}</p>
                </div>
                <i class="fas fa-sync text-blue-600"></i>
            </div>
        `).join("");
    }

    /* ============================
       USER LOGIN / LOGOUT TRACKING
    ============================ */
    async loadUserLogs() {
        try {
            const resp = await auth.makeAuthenticatedRequest(`/api/admin/user-logs`);
            const data = await resp.json();

            if (!resp.ok) return;

            this.userLogs = data.logs;
            this.renderUserLogs();

        } catch (err) {
            console.error("User Logs Error:", err);
        }
    }

    renderUserLogs() {
        const container = document.getElementById("user-logs-container");
        if (!container) return;

        if (this.userLogs.length === 0) {
            container.innerHTML = `<p class="text-gray-500">No login/logout activity.</p>`;
            return;
        }

        container.innerHTML = this.userLogs.map(log => `
            <div class="p-4 bg-white rounded-lg shadow border flex justify-between items-center">

                <div>
                    <p class="font-semibold text-gray-800">${log.user_name}</p>
                    <p class="text-sm text-gray-500">${log.action}</p>
                </div>

                <span class="text-xs bg-gray-100 px-3 py-1 rounded-full">
                    ${new Date(log.timestamp).toLocaleString()}
                </span>
            </div>
        `).join("");
    }

    /* ============================
       PERFORMANCE CHART
    ============================ */
    renderPerformanceChart() {
        if (!this.stats) return;

        const ctx = document.getElementById("performanceChart");
        if (!ctx) return;

        new Chart(ctx, {
            type: "line",
            data: {
                labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                datasets: [{
                    label: "Avg Performance (%)",
                    data: this.stats.performance_trend || [0,0,0,0,0,0,0],
                    borderWidth: 3,
                    fill: false,
                    borderColor: "#2563EB"
                }]
            },
            options: {
                responsive: true,
                tension: 0.4
            }
        });
    }
}

window.dashboard = new Dashboard();

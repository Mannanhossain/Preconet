/* ============================
   ADMIN DASHBOARD MANAGER
   ============================ */
class DashboardManager {
    async init() {
        if (!auth.getToken()) {
            window.location.href = "/admin/login.html";
            return;
        }

        try {
            // Load main dashboard blocks
            await this.loadStats();
            this.drawPerformanceChart();         // Must run AFTER stats
            await this.loadRecentSync();
            await this.loadUserLogs();
        } catch (err) {
            console.error("Dashboard Init Error:", err);
            auth.showNotification("Dashboard failed to load", "error");
        }
    }

    /* ============================
       LOAD DASHBOARD STATS
       ============================ */
    async loadStats() {
        try {
            const resp = await auth.makeAuthenticatedRequest("/api/admin/dashboard-stats");
            const data = await resp.json();

            if (!resp.ok) {
                auth.showNotification(data.error || "Failed to load dashboard stats", "error");
                return;
            }

            this.stats = data.stats || {};
            this.renderStats();
        } catch (err) {
            console.error(err);
            auth.showNotification("Error loading dashboard stats", "error");
        }
    }

    renderStats() {
        const container = document.getElementById("stats-cards");
        if (!container) return;

        const s = this.stats;

        const cards = [
            { title: "Total Users", value: s.total_users ?? 0, icon: "users", color: "blue" },
            { title: "Active Users", value: s.active_users ?? 0, icon: "user-check", color: "green" },
            { title: "Users With Sync", value: s.users_with_sync ?? 0, icon: "sync", color: "purple" },
            { title: "Remaining Slots", value: s.remaining_slots ?? 0, icon: "user-plus", color: "orange" }
        ];

        container.innerHTML = cards.map(c => `
            <div class="bg-white p-4 rounded shadow hover:shadow-md transition">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="text-sm text-gray-500">${c.title}</p>
                        <p class="text-2xl font-bold">${c.value}</p>
                    </div>
                    <div class="w-12 h-12 rounded flex items-center justify-center bg-${c.color}-100 text-${c.color}-600">
                        <i class="fas fa-${c.icon} text-xl"></i>
                    </div>
                </div>
            </div>
        `).join("");
    }

    /* ============================
       RECENT SYNC — LAST 10 USERS
       ============================ */
    async loadRecentSync() {
        try {
            const resp = await auth.makeAuthenticatedRequest("/api/admin/recent-sync");
            const data = await resp.json();

            if (!resp.ok) return;

            const list = document.getElementById("recent-sync-list");
            if (!list) return;

            const users = data.recent_sync || [];

            list.innerHTML = users.map(u => `
                <div class="border p-3 rounded bg-white">
                    <div class="flex justify-between">
                        <div>
                            <div class="font-medium">${u.name}</div>
                            <div class="text-xs text-gray-500">
                                Last Sync: ${u.last_sync ? new Date(u.last_sync).toLocaleString() : "Never"}
                            </div>
                        </div>
                        <div class="text-xs text-gray-500">${u.phone || ""}</div>
                    </div>
                </div>
            `).join("");
        } catch (err) {
            console.error(err);
        }
    }

    /* ============================
       USER ACTIVITY LOGS
       ============================ */
    async loadUserLogs() {
        try {
            const resp = await auth.makeAuthenticatedRequest("/api/admin/user-logs");
            const data = await resp.json();

            if (!resp.ok) return;

            const container = document.getElementById("user-logs-container");
            if (!container) return;

            const logs = data.logs || [];

            container.innerHTML = logs.map(l => `
                <div class="p-4 border rounded bg-white">
                    <div class="flex justify-between">
                        <div>
                            <div class="font-medium">${l.user_name || "Unknown User"}</div>
                            <div class="text-xs text-gray-500">${l.action}</div>
                        </div>
                        <div class="text-xs text-gray-500">
                            ${new Date(l.timestamp).toLocaleString()}
                        </div>
                    </div>
                </div>
            `).join("");
        } catch (err) {
            console.error(err);
        }
    }

    /* ============================
       PERFORMANCE CHART
       ============================ */
    drawPerformanceChart() {
        const ctx = document.getElementById("performanceChart");
        if (!ctx) return;

        if (typeof Chart === "undefined") {
            console.error("Chart.js not loaded");
            return;
        }

        const trend = this.stats?.performance_trend || [0, 0, 0, 0, 0, 0, 0];

        new Chart(ctx, {
            type: "line",
            data: {
                labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                datasets: [{
                    label: "Avg Performance",
                    data: trend,
                    borderColor: "#2563EB",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

const dashboard = new DashboardManager();

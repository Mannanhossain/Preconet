class AdminDashboard {

    constructor() {
        this.stats = null;
        this.users = [];
        this.attendance = [];

        window.adminDashboard = this;
        this.init();
    }

    /* =========================================================================
       INIT
    ========================================================================= */
    async init() {
        if (!this.checkAuth()) return;

        await this.loadStats();
        await this.loadUsers();
        await this.loadAttendance();

        this.setupNavigation();
        this.setupLogout();
        this.setupModalListeners();

        this.showSection("dashboard");
    }

    checkAuth() {
        const token = sessionStorage.getItem("admin_token");
        if (!token) {
            window.location.href = "/admin/login.html";
            return false;
        }
        return true;
    }

    /* =========================================================================
       LOAD STATS
    ========================================================================= */
    async loadStats() {
        try {
            const res = await auth.makeAuthenticatedRequest("/api/admin/dashboard-stats");
            const data = await res.json();

            if (res.ok) {
                this.stats = data.stats;
                this.renderStats();
                this.renderPerformance();
            }
        } catch (err) {
            console.error("Stats error:", err);
        }
    }

    /* =========================================================================
       LOAD USERS
    ========================================================================= */
    async loadUsers() {
        try {
            const res = await auth.makeAuthenticatedRequest("/api/admin/users");
            const data = await res.json();

            if (res.ok) {
                this.users = data.users;
                this.renderUsersTable();
            }
        } catch (err) {
            console.error("Users load error:", err);
        }
    }

    /* =========================================================================
       LOAD ATTENDANCE
    ========================================================================= */
    async loadAttendance() {
        try {
            const res = await auth.makeAuthenticatedRequest("/api/admin/attendance");
            const data = await res.json();

            if (res.ok) {
                this.attendance = data.attendance;
                this.renderAttendanceTable();
            }
        } catch (err) {
            console.error("Attendance load error:", err);
        }
    }

    /* =========================================================================
       RENDER STATS CARDS
    ========================================================================= */
    renderStats() {
        const div = document.getElementById("stats-cards");
        if (!div || !this.stats) return;

        const s = this.stats;

        div.innerHTML = `
            <div class="bg-white p-6 rounded-xl shadow">
                <p class="text-sm text-gray-600">Total Users</p>
                <p class="text-3xl font-bold">${s.total_users}</p>
            </div>

            <div class="bg-white p-6 rounded-xl shadow">
                <p class="text-sm text-gray-600">Active Users</p>
                <p class="text-3xl font-bold">${s.active_users}</p>
            </div>

            <div class="bg-white p-6 rounded-xl shadow">
                <p class="text-sm text-gray-600">Users with Sync</p>
                <p class="text-3xl font-bold">${s.users_with_sync}</p>
            </div>

            <div class="bg-white p-6 rounded-xl shadow">
                <p class="text-sm text-gray-600">Remaining Slots</p>
                <p class="text-3xl font-bold">${s.remaining_slots}</p>
            </div>
        `;
    }

    /* =========================================================================
       PERFORMANCE BOX
    ========================================================================= */
    renderPerformance() {
        const box = document.getElementById("performance-chart");

        if (!box || !this.stats) return;

        const s = this.stats;
        const percent = (s.total_users / s.user_limit) * 100;

        box.innerHTML = `
            <p class="text-3xl font-bold">${s.avg_performance}%</p>
            <p class="text-sm text-gray-500">Average Performance</p>

            <div class="w-full bg-gray-200 h-2 rounded-full mt-4">
                <div class="bg-green-600 h-2 rounded-full" style="width:${percent}%"></div>
            </div>

            <p class="mt-4 text-sm">Sync Rate: ${s.sync_rate}%</p>
        `;
    }

    /* =========================================================================
       USERS TABLE
    ========================================================================= */
    renderUsersTable() {
        const body = document.getElementById("users-table-body");
        if (!body) return;

        body.innerHTML = this.users
            .map(
                (u) => `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-3">
                    <strong>${u.name}</strong><br>
                    <span class="text-sm text-gray-500">${u.email}</span>
                </td>
                <td class="px-4 py-3">${u.phone ?? "N/A"}</td>
                <td class="px-4 py-3">${u.performance_score}%</td>
                <td class="px-4 py-3">${u.last_sync ? new Date(u.last_sync).toLocaleString() : "Never"}</td>
                <td class="px-4 py-3 text-right">
                    <button class="text-blue-600" onclick="adminDashboard.viewUser(${u.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `
            )
            .join("");
    }

    /* =========================================================================
       ATTENDANCE TABLE
    ========================================================================= */
    renderAttendanceTable() {
        const body = document.getElementById("attendance-table-body");
        if (!body) return;

        body.innerHTML = this.attendance
            .map(
                (a) => `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-2">${a.user_name}</td>
                <td class="px-4 py-2">${new Date(a.check_in).toLocaleString()}</td>
                <td class="px-4 py-2">${a.check_out ? new Date(a.check_out).toLocaleString() : "--"}</td>
                <td class="px-4 py-2">${a.status}</td>
            </tr>
        `
            )
            .join("");
    }

    /* =========================================================================
       USER DETAILS MODAL (Analytics + Call History + Attendance)
    ========================================================================= */
    async viewUser(userId) {
        try {
            const [analytics, calls, attendance] = await Promise.all([
                auth.makeAuthenticatedRequest(`/api/admin/user-analytics/${userId}`),
                auth.makeAuthenticatedRequest(`/api/admin/user-call-history/${userId}`),
                auth.makeAuthenticatedRequest(`/api/admin/user-attendance/${userId}`)
            ]);

            const analyticsData = await analytics.json();
            const callsData = await calls.json();
            const attendanceData = await attendance.json();

            const user = this.users.find((u) => u.id === userId);

            this.showModal(user, analyticsData, callsData, attendanceData);
        } catch (err) {
            console.error(err);
            auth.showNotification("Failed to load user details", "error");
        }
    }

    showModal(user, analytics, calls, attendance) {
        const modal = document.getElementById("user-data-modal");
        const box = document.getElementById("user-data-content");

        box.innerHTML = `
            <h2 class="text-xl font-bold">${user.name}</h2>
            <p class="text-sm">Last Sync: ${user.last_sync ? new Date(user.last_sync).toLocaleString() : "Never"}</p>

            <h3 class="mt-4 font-semibold">Analytics</h3>
            <pre>${JSON.stringify(analytics, null, 2)}</pre>

            <h3 class="mt-4 font-semibold">Call History</h3>
            <pre>${JSON.stringify(calls, null, 2)}</pre>

            <h3 class="mt-4 font-semibold">Attendance</h3>
            <pre>${JSON.stringify(attendance, null, 2)}</pre>
        `;

        modal.classList.remove("hidden");
    }

    setupModalListeners() {
        const modal = document.getElementById("user-data-modal");
        const closeBtn = document.getElementById("close-user-data-modal");

        closeBtn.onclick = () => modal.classList.add("hidden");

        modal.onclick = (e) => {
            if (e.target === modal) modal.classList.add("hidden");
        };
    }

    /* =========================================================================
       NAVIGATION
    ========================================================================= */
    showSection(section) {
        ["dashboard", "users", "attendance", "performance"].forEach((s) => {
            const div = document.getElementById(`${s}-section`);
            if (div) div.style.display = "none";
        });

        document.getElementById(`${section}-section`).style.display = "block";
    }

    setupNavigation() {
        document.querySelectorAll(".nav-item").forEach((item) => {
            item.onclick = (e) => {
                e.preventDefault();
                this.showSection(item.getAttribute("href").replace("#", ""));
            };
        });
    }

    /* =========================================================================
       LOGOUT
    ========================================================================= */
    setupLogout() {
        const btn = document.getElementById("logout-btn");
        btn.onclick = () => {
            sessionStorage.clear();
            window.location.href = "/admin/login.html";
        };
    }
}

/* INIT */
window.adminDashboard = new AdminDashboard();

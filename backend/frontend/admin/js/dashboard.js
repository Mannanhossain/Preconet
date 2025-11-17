class AdminDashboard {
    constructor() {
        this.stats = null;
        this.users = [];
        this.attendance = [];

        window.adminDashboard = this;
        this.init();
    }

    async init() {
        if (!this.checkAuth()) return;

        await this.loadStats();
        await this.loadUsers();
        await this.loadAttendance();

        this.setupNavigation();
        this.setupLogout();
        this.setupModalClose();
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

    /* ============================================================
       📌 LOAD ADMIN DASHBOARD STATS
    ============================================================ */
    async loadStats() {
        try {
            const resp = await auth.makeAuthenticatedRequest(`/api/admin/dashboard-stats`);
            const data = await resp.json();

            if (resp.ok) {
                this.stats = data.stats;
                this.renderStats();
                this.renderPerformanceOverview();
            }
        } catch (err) {
            console.error("Stats Error:", err);
        }
    }

    /* ============================================================
       📌 LOAD USERS
    ============================================================ */
    async loadUsers() {
        try {
            const resp = await auth.makeAuthenticatedRequest(`/api/admin/users`);
            const data = await resp.json();

            if (resp.ok) {
                this.users = data.users;
                this.renderUsersTable();
            }
        } catch (err) {
            console.error(err);
        }
    }

    /* ============================================================
       📌 LOAD ATTENDANCE
    ============================================================ */
    async loadAttendance() {
        try {
            const resp = await auth.makeAuthenticatedRequest(`/api/admin/attendance`);
            const data = await resp.json();

            if (resp.ok) {
                this.attendance = data.attendance;
                this.renderAttendanceTable();
            }
        } catch (err) {
            console.error(err);
        }
    }

    /* ============================================================
       📌 RENDER STATS CARDS
    ============================================================ */
    renderStats() {
        const div = document.getElementById("stats-cards");
        if (!div || !this.stats) return;

        const s = this.stats;

        const stats = [
            { label: "Total Users", value: s.total_users, icon: "users", color: "blue" },
            { label: "Active Users", value: s.active_users, icon: "user-check", color: "green" },
            { label: "Users With Sync", value: s.users_with_sync, icon: "sync", color: "purple" },
            { label: "Remaining Slots", value: s.remaining_slots, icon: "user-plus", color: "yellow" }
        ];

        div.innerHTML = stats
            .map(
                (i) => `
            <div class="bg-white p-6 rounded-xl shadow">
                <div class="flex justify-between">
                    <div>
                        <p class="text-gray-500 text-sm">${i.label}</p>
                        <p class="text-3xl font-bold">${i.value}</p>
                    </div>
                    <div class="h-12 w-12 rounded-xl bg-${i.color}-100 flex items-center justify-center text-${i.color}-600">
                        <i class="fas fa-${i.icon} text-xl"></i>
                    </div>
                </div>
            </div>
        `
            )
            .join("");
    }

    /* ============================================================
       📌 PERFORMANCE
    ============================================================ */
    renderPerformanceOverview() {
        const box = document.getElementById("performance-chart");
        if (!box || !this.stats) return;

        const s = this.stats;
        const percent = (s.total_users / s.user_limit) * 100;

        box.innerHTML = `
            <p class="text-3xl font-bold">${s.avg_performance}%</p>
            <p class="text-sm text-gray-500">Average Performance</p>

            <p class="mt-4">Users: ${s.total_users}/${s.user_limit}</p>
            <div class="w-full bg-gray-200 h-2 rounded-full">
                <div class="bg-green-600 h-2 rounded-full" style="width:${percent}%"></div>
            </div>

            <p class="mt-4 text-sm">Sync Rate: ${s.sync_rate}%</p>
        `;
    }

    /* ============================================================
       📌 RENDER USERS TABLE
    ============================================================ */
    renderUsersTable() {
        const body = document.getElementById("users-table-body");
        if (!body) return;

        body.innerHTML = this.users
            .map(
                (u) => `
            <tr class="hover:bg-gray-100">
                <td class="px-4 py-3">
                    <div class="flex items-center">
                        <div class="h-10 w-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">${u.name[0]}</div>
                        <div class="ml-3">
                            <p class="font-semibold">${u.name}</p>
                            <p class="text-sm text-gray-500">${u.email}</p>
                        </div>
                    </div>
                </td>

                <td class="px-4 py-3">${u.phone ?? "N/A"}</td>

                <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs rounded-full ${
                        u.is_active ? "bg-green-100 text-green-600" : "bg-red-100 text-red-600"
                    }">
                        ${u.is_active ? "Active" : "Inactive"}
                    </span>
                </td>

                <td class="px-4 py-3">${u.performance_score}%</td>

                <td class="px-4 py-3">${u.last_sync ? new Date(u.last_sync).toLocaleString() : "Never"}</td>

                <td class="px-4 py-3 text-right">
                    <button onclick="adminDashboard.viewUserDetails(${u.id})" class="text-blue-600 mr-3">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `
            )
            .join("");
    }

    /* ============================================================
       📌 RENDER ATTENDANCE TABLE
    ============================================================ */
    renderAttendanceTable() {
        const body = document.getElementById("attendance-table-body");
        if (!body) return;

        body.innerHTML = this.attendance
            .map(
                (a) => `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-2">${a.user_name}</td>
                <td class="px-4 py-2">${new Date(a.check_in).toLocaleDateString()}</td>
                <td class="px-4 py-2">${new Date(a.check_in).toLocaleTimeString()}</td>
                <td class="px-4 py-2">${a.check_out ? new Date(a.check_out).toLocaleTimeString() : "--"}</td>
                <td class="px-4 py-2">${a.status}</td>
                <td class="px-4 py-2">${a.address}</td>
            </tr>
        `
            )
            .join("");
    }

    /* ============================================================
       📌 VIEW USER FULL DATA (Calls, Analytics, Attendance)
    ============================================================ */
    async viewUserDetails(userId) {
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

            this.showUserModal(user, analyticsData, callsData, attendanceData);
        } catch (err) {
            console.error(err);
            auth.showNotification("Failed to load user data", "error");
        }
    }

    /* ============================================================
       📌 USER DETAILS MODAL
    ============================================================ */
    showUserModal(user, analytics, calls, attendance) {
        const modal = document.getElementById("user-data-modal");
        const box = document.getElementById("user-data-content");

        box.innerHTML = `
            <h2 class="text-xl font-bold">${user.name}</h2>
            <p class="text-sm text-gray-500 mb-4">
                Last Sync: ${user.last_sync ? new Date(user.last_sync).toLocaleString() : "Never"}
            </p>

            <h3 class="font-semibold mt-4">Analytics</h3>
            <pre class="bg-gray-100 p-3 rounded">${JSON.stringify(analytics, null, 2)}</pre>

            <h3 class="font-semibold mt-4">Call History</h3>
            <pre class="bg-gray-100 p-3 rounded">${JSON.stringify(calls, null, 2)}</pre>

            <h3 class="font-semibold mt-4">Attendance</h3>
            <pre class="bg-gray-100 p-3 rounded">${JSON.stringify(attendance, null, 2)}</pre>
        `;

        modal.classList.remove("hidden");
    }

    setupModalClose() {
        const modal = document.getElementById("user-data-modal");
        const close = document.getElementById("close-user-data-modal");

        if (close) {
            close.onclick = () => modal.classList.add("hidden");
        }

        modal.onclick = (e) => {
            if (e.target === modal) modal.classList.add("hidden");
        };
    }

    /* ============================================================
       📌 SIMPLE PAGE NAVIGATION
    ============================================================ */
    showSection(section) {
        ["dashboard", "users", "attendance", "performance"].forEach((s) => {
            const div = document.getElementById(`${s}-section`);
            if (div) div.style.display = "none";
        });

        const active = document.getElementById(`${section}-section`);
        if (active) active.style.display = "block";
    }

    setupNavigation() {
        document.querySelectorAll(".nav-item").forEach((item) => {
            item.onclick = (e) => {
                e.preventDefault();
                const t = item.getAttribute("href").replace("#", "");
                this.showSection(t);
            };
        });
    }

    setupLogout() {
        const btn = document.getElementById("logout-btn");
        if (!btn) return;

        btn.onclick = () => {
            sessionStorage.clear();
            window.location.href = "/admin/login.html";
        };
    }
}

window.adminDashboard = new AdminDashboard();

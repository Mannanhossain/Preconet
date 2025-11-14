class AdminDashboard {
    constructor() {
        this.stats = null;
        this.currentSection = 'dashboard';
        this.users = [];
        window.adminDashboard = this; // ensure global access
        this.init();
    }

    async init() {
        if (!this.checkAuth()) return;

        await this.loadStats();
        await this.loadUsers();

        this.setupNavigation();
        this.setupLogout();
        this.setupEventListeners();
    }

    // ---------------------------------------------------------
    // AUTH CHECK
    // ---------------------------------------------------------
    checkAuth() {
        const token = sessionStorage.getItem('admin_token');
        if (!token) {
            window.location.href = '/admin/login.html';
            return false;
        }
        return true;
    }

    // ---------------------------------------------------------
    // LOAD STATS (FIXED: Removed duplicate /api)
    // ---------------------------------------------------------
    async loadStats() {
        try {
            const response = await auth.makeAuthenticatedRequest('/admin/dashboard-stats');
            const data = await response.json();

            if (response.ok && data.stats) {
                this.stats = data.stats;
                this.renderStats();
                this.renderPerformanceOverview();
            } else {
                auth.showNotification(data.error || 'Failed to load dashboard stats', 'error');
            }
        } catch (error) {
            console.error('Stats error:', error);
            auth.showNotification('Error loading dashboard data', 'error');
        }
    }

    // ---------------------------------------------------------
    // LOAD USERS (FIXED: Removed duplicate /api)
    // ---------------------------------------------------------
    async loadUsers() {
        try {
            const response = await auth.makeAuthenticatedRequest('/admin/users');
            const data = await response.json();

            if (response.ok && data.users) {
                this.users = data.users;
                this.renderUsersTable();
            } else {
                auth.showNotification('Failed to load users', 'error');
            }
        } catch (error) {
            console.error('Users error:', error);
            auth.showNotification('Error loading users', 'error');
        }
    }

    // ---------------------------------------------------------
    // RENDER DASHBOARD STATS
    // ---------------------------------------------------------
    renderStats() {
        const container = document.getElementById('stats-cards');
        if (!container || !this.stats) return;

        const stats = this.stats;

        const items = [
            {
                label: "Total Users",
                value: stats.total_users,
                icon: "users",
                bg: "bg-blue-50",
                text: "text-blue-600"
            },
            {
                label: "Active Users",
                value: stats.active_users,
                icon: "user-check",
                bg: "bg-green-50",
                text: "text-green-600"
            },
            {
                label: "Users with Sync Data",
                value: stats.users_with_sync,
                icon: "sync",
                bg: "bg-purple-50",
                text: "text-purple-600"
            },
            {
                label: "Remaining Slots",
                value: stats.remaining_slots,
                icon: "user-plus",
                bg: "bg-orange-50",
                text: "text-orange-600"
            }
        ];

        container.innerHTML = items
            .map(
                (s) => `
                <div class="stat-card bg-white rounded-xl shadow-sm border p-6 hover:shadow-md transition">
                    <div class="flex justify-between">
                        <div>
                            <p class="text-sm text-gray-600">${s.label}</p>
                            <p class="text-3xl font-bold">${s.value}</p>
                        </div>
                        <div class="${s.bg} w-12 h-12 rounded-lg flex items-center justify-center">
                            <i class="fas fa-${s.icon} ${s.text} text-lg"></i>
                        </div>
                    </div>
                </div>
            `
            )
            .join("");
    }

    // ---------------------------------------------------------
    // PERFORMANCE OVERVIEW
    // ---------------------------------------------------------
    renderPerformanceOverview() {
        const container = document.getElementById('performance-chart');
        if (!container || !this.stats) return;

        const s = this.stats;
        const avg = s.avg_performance ?? 0;
        const total = s.total_users ?? 0;
        const limit = s.user_limit ?? 1;

        const percent = (total / limit) * 100;

        container.innerHTML = `
            <div class="text-center">
                <div class="text-3xl font-bold">${avg}%</div>
                <div class="text-gray-600">Average Performance</div>
            </div>

            <div class="mt-4 space-y-3">
                <div class="flex justify-between text-sm">
                    <span>User Limit</span>
                    <span>${total}/${limit}</span>
                </div>

                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-green-600 h-2 rounded-full" style="width:${percent}%"></div>
                </div>

                <div class="flex justify-between text-sm">
                    <span>Sync Rate</span>
                    <span>${s.sync_rate}%</span>
                </div>
            </div>
        `;
    }

    // ---------------------------------------------------------
    // USERS TABLE
    // ---------------------------------------------------------
    renderUsersTable() {
        const container = document.getElementById('users-table-body');
        if (!container) return;

        container.innerHTML = this.users
            .map(
                (u) => `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4">
                        <div class="flex items-center">
                            <div class="h-10 w-10 bg-blue-500 text-white rounded-full flex items-center justify-center">
                                ${u.name[0].toUpperCase()}
                            </div>
                            <div class="ml-4">
                                <div class="text-sm font-medium">${u.name}</div>
                                <div class="text-sm text-gray-500">${u.email}</div>
                            </div>
                        </div>
                    </td>
                    <td class="px-6 py-4">${u.phone || "N/A"}</td>

                    <td class="px-6 py-4">
                        <span class="px-2 py-1 rounded-full text-xs ${
                            u.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                        }">
                            ${u.is_active ? "Active" : "Inactive"}
                        </span>
                    </td>

                    <td class="px-6 py-4">${u.performance_score}%</td>

                    <td class="px-6 py-4">
                        ${u.last_sync ? new Date(u.last_sync).toLocaleDateString() : "Never"}
                    </td>

                    <td class="px-6 py-4 text-right">
                        <button class="text-blue-600 mr-2" onclick="adminDashboard.viewUserData(${u.id})">
                            <i class="fas fa-database"></i> View
                        </button>
                        <button class="text-indigo-600 mr-2" onclick="adminDashboard.editUser(${u.id})">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="text-red-600" onclick="adminDashboard.deleteUser(${u.id})">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </td>
                </tr>
            `
            )
            .join("");
    }

    // ---------------------------------------------------------
    // VIEW USER DATA (FIXED API PATH)
    // ---------------------------------------------------------
    async viewUserData(userId) {
        try {
            const response = await auth.makeAuthenticatedRequest(`/admin/user-data/${userId}`);
            const data = await response.json();

            if (!response.ok) {
                auth.showNotification(data.error || "Failed to load user data", "error");
                return;
            }

            this.renderUserDataModal(
                this.users.find((u) => u.id === userId),
                data
            );
        } catch (err) {
            console.error(err);
            auth.showNotification("Error loading user data", "error");
        }
    }

    // ---------------------------------------------------------
    // MODAL RENDER
    // ---------------------------------------------------------
    renderUserDataModal(user, data) {
        const modal = document.getElementById("user-data-modal");
        const content = document.getElementById("user-data-content");

        if (!modal || !content) return;

        content.innerHTML = `
            <div class="p-6">
                <h2 class="text-xl font-bold">${user.name}</h2>
                <p class="text-sm text-gray-500">Last Sync: ${
                    data.last_sync
                        ? new Date(data.last_sync).toLocaleString()
                        : "Never"
                }</p>

                <div class="mt-4">
                    <h3 class="font-semibold">Analytics</h3>
                    <pre class="bg-gray-100 p-3 rounded">${JSON.stringify(
                        data.analytics,
                        null,
                        2
                    )}</pre>
                </div>

                <div class="mt-4">
                    <h3 class="font-semibold">Call History (${data.call_history?.length})</h3>
                    <pre class="bg-gray-100 p-3 rounded">${JSON.stringify(
                        data.call_history,
                        null,
                        2
                    )}</pre>
                </div>

                <div class="mt-4">
                    <h3 class="font-semibold">Contacts (${data.contacts?.length})</h3>
                    <pre class="bg-gray-100 p-3 rounded">${JSON.stringify(
                        data.contacts,
                        null,
                        2
                    )}</pre>
                </div>
            </div>
        `;

        modal.classList.remove("hidden");
    }

    closeUserDataModal() {
        const modal = document.getElementById("user-data-modal");
        if (modal) modal.classList.add("hidden");
    }

    // ---------------------------------------------------------
    // NAVIGATION
    // ---------------------------------------------------------
    setupNavigation() {
        const items = document.querySelectorAll(".nav-item");
        const title = document.getElementById("page-title");
        const subtitle = document.getElementById("page-subtitle");

        const pages = {
            dashboard: {
                title: "Admin Dashboard",
                subtitle: "Manage your users and track performance",
                section: "dashboard-section",
            },
            users: {
                title: "Manage Users",
                subtitle: "Add, edit, and manage user accounts",
                section: "users-section",
            },
            performance: {
                title: "Performance Analytics",
                subtitle: "Monitor performance data",
                section: "performance-section",
            },
        };

        items.forEach((item) => {
            item.addEventListener("click", (e) => {
                e.preventDefault();

                items.forEach((n) => n.classList.remove("active"));
                item.classList.add("active");

                const target = item.getAttribute("href").replace("#", "");
                const page = pages[target];

                if (page) {
                    this.currentSection = target;
                    title.textContent = page.title;
                    subtitle.textContent = page.subtitle;
                    this.showSection(target);
                }
            });
        });
    }

    showSection(section) {
        const sections = ["dashboard", "users", "performance"];

        sections.forEach((sec) => {
            const el = document.getElementById(`${sec}-section`);
            if (el) el.style.display = "none";
        });

        const active = document.getElementById(`${section}-section`);
        if (active) active.style.display = "block";
    }

    // ---------------------------------------------------------
    // LOGOUT
    // ---------------------------------------------------------
    setupLogout() {
        const btn = document.getElementById("logout-btn");
        if (!btn) return;

        btn.addEventListener("click", () => {
            sessionStorage.removeItem("admin_token");
            sessionStorage.removeItem("admin_user");

            auth.showNotification("Logged out", "success");

            setTimeout(() => {
                window.location.href = "/admin/login.html";
            }, 600);
        });
    }

    // ---------------------------------------------------------
    // MODAL LISTENERS
    // ---------------------------------------------------------
    setupEventListeners() {
        const modal = document.getElementById("user-data-modal");
        const closeBtn = document.getElementById("close-user-data-modal");

        if (closeBtn) {
            closeBtn.addEventListener("click", () => this.closeUserDataModal());
        }

        if (modal) {
            modal.addEventListener("click", (e) => {
                if (e.target === modal) this.closeUserDataModal();
            });
        }
    }

    // ---------------------------------------------------------
    // PLACEHOLDERS
    // ---------------------------------------------------------
    editUser() {
        auth.showNotification("Edit user feature coming soon", "info");
    }

    deleteUser() {
        auth.showNotification("Delete user feature coming soon", "info");
    }
}

// Attach instance globally
window.adminDashboard = new AdminDashboard();

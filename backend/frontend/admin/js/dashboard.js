class AdminDashboard {
    constructor() {
        this.stats = null;
        this.init();
    }

    async init() {
        await this.loadStats();
        this.setupNavigation();
        this.setupLogout();
        this.setupEventListeners();
    }

    // ✅ Fetch dashboard stats from backend
    async loadStats() {
        try {
            const response = await auth.makeAuthenticatedRequest('/api/admin/dashboard-stats');
            const data = await response.json();
            
            if (response.ok && data.stats) {
                this.stats = data.stats;
                this.renderStats();
                this.renderPerformanceOverview();
            } else {
                auth.showNotification('Failed to load dashboard stats', 'error');
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            auth.showNotification('Error loading dashboard data', 'error');
        }
    }

    // ✅ Display main dashboard stats
    renderStats() {
        const statsContainer = document.getElementById('stats-cards');
        if (!statsContainer || !this.stats) return;

        const statsConfig = [
            { 
                label: 'Total Users', 
                value: this.stats.total_users ?? 0, 
                icon: 'users', 
                bgColor: 'bg-blue-50',
                textColor: 'text-blue-600'
            },
            { 
                label: 'Active Users', 
                value: this.stats.active_users ?? 0, 
                icon: 'user-check', 
                bgColor: 'bg-green-50',
                textColor: 'text-green-600'
            },
            { 
                label: 'Expired Users', 
                value: this.stats.expired_users ?? 0, 
                icon: 'user-times', 
                bgColor: 'bg-red-50',
                textColor: 'text-red-600'
            },
            { 
                label: 'Remaining Slots', 
                value: this.stats.remaining_slots ?? 0, 
                icon: 'user-plus', 
                bgColor: 'bg-orange-50',
                textColor: 'text-orange-600'
            }
        ];

        statsContainer.innerHTML = statsConfig.map(stat => `
            <div class="stat-card bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600 mb-1">${stat.label}</p>
                        <p class="text-3xl font-bold text-gray-900">${stat.value}</p>
                    </div>
                    <div class="${stat.bgColor} w-12 h-12 rounded-lg flex items-center justify-center">
                        <i class="fas fa-${stat.icon} ${stat.textColor} text-lg"></i>
                    </div>
                </div>
                <div class="mt-4 pt-4 border-t border-gray-100">
                    <div class="flex items-center text-xs text-gray-500">
                        <i class="fas fa-clock mr-1"></i>
                        <span>Updated just now</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // ✅ Performance overview card
    renderPerformanceOverview() {
        const container = document.getElementById('performance-chart');
        if (!container || !this.stats) return;

        const avgPerf = this.stats.avg_performance ?? 0;
        const totalUsers = this.stats.total_users ?? 0;
        const userLimit = this.stats.user_limit ?? 1; // prevent division by zero
        const usagePercent = (totalUsers / userLimit) * 100;

        container.innerHTML = `
            <div class="text-center mb-4">
                <div class="text-3xl font-bold text-gray-900 mb-1">${avgPerf}%</div>
                <div class="text-sm text-gray-600">Average Performance</div>
            </div>
            <div class="space-y-3">
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">User Limit</span>
                    <span class="font-medium">${totalUsers}/${userLimit}</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-green-600 h-2 rounded-full" style="width: ${usagePercent}%"></div>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Active Users</span>
                    <span class="font-medium">${this.stats.active_users}</span>
                </div>
            </div>
        `;
    }

    // ✅ Navigation section switching
    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const pageTitle = document.getElementById('page-title');
        const pageSubtitle = document.getElementById('page-subtitle');

        const pages = {
            dashboard: {
                title: 'Admin Dashboard',
                subtitle: 'Manage your users and track performance',
                section: 'dashboard-section'
            },
            users: {
                title: 'Manage Users',
                subtitle: 'Add, edit, and manage user accounts',
                section: 'users-section'
            },
            performance: {
                title: 'Performance Analytics',
                subtitle: 'Monitor and analyze user performance data',
                section: 'performance-section'
            }
        };

        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');

                const target = item.getAttribute('href').substring(1);
                const page = pages[target];

                if (page) {
                    pageTitle.textContent = page.title;
                    pageSubtitle.textContent = page.subtitle;
                    this.showSection(target);
                }
            });
        });
    }

    // ✅ Show/hide sections dynamically
    showSection(section) {
        const sections = ['dashboard', 'users', 'performance'];
        sections.forEach(sec => {
            const el = document.getElementById(`${sec}-section`);
            if (el) el.style.display = 'none';
        });

        const targetEl = document.getElementById(`${section}-section`);
        if (targetEl) targetEl.style.display = 'block';

        switch (section) {
            case 'users':
                if (typeof usersManager !== 'undefined') usersManager.loadUsers();
                break;
            case 'performance':
                if (typeof performanceManager !== 'undefined') performanceManager.loadPerformance();
                break;
        }
    }

    // ✅ Logout handling
    setupLogout() {
        const logoutBtn = document.getElementById('logout-btn');
        if (!logoutBtn) return;

        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            sessionStorage.removeItem('admin_token');
            sessionStorage.removeItem('admin_user');
            auth.showNotification('Logged out successfully', 'success');
            setTimeout(() => {
                window.location.href = '/admin/login.html';
            }, 1000);
        });
    }

    setupEventListeners() {
        console.log('✅ Admin Dashboard initialized successfully');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AdminDashboard();
});

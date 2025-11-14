class SuperAdminDashboard {
    constructor() {
        this.stats = null;
        this.init();
    }

    async init() {
        await this.loadStats();
        this.setupNavigation();
        this.setupEventListeners();
    }

    // -------------------------------------------------------
    // LOAD SUPER ADMIN DASHBOARD STATS
    // -------------------------------------------------------
    async loadStats() {
        try {
            // FIXED: ❌ removed /api prefix (auth adds it automatically)
            const response = await auth.makeAuthenticatedRequest('/superadmin/dashboard-stats');
            const data = await response.json();

            if (response.ok && data.stats) {
                this.stats = data.stats;
                this.renderStats();
            } else {
                auth.showNotification('Failed to load dashboard stats', 'error');
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            auth.showNotification('⚠️ Error loading dashboard data', 'error');
        }
    }

    // -------------------------------------------------------
    // RENDER DASHBOARD INFO CARDS
    // -------------------------------------------------------
    renderStats() {
        const statsContainer = document.getElementById('stats-cards');
        if (!statsContainer || !this.stats) return;

        const statsConfig = [
            { 
                label: 'Total Admins',
                value: this.stats.total_admins ?? 0,
                icon: 'users-cog',
                bgColor: 'bg-blue-50',
                textColor: 'text-blue-600'
            },
            { 
                label: 'Total Users',
                value: this.stats.total_users ?? 0,
                icon: 'users',
                bgColor: 'bg-green-50',
                textColor: 'text-green-600'
            },
            { 
                label: 'Active Admins',
                value: this.stats.active_admins ?? 0,
                icon: 'user-check',
                bgColor: 'bg-green-50',
                textColor: 'text-green-600'
            },
            { 
                label: 'Expired Admins',
                value: this.stats.expired_admins ?? 0,
                icon: 'exclamation-triangle',
                bgColor: 'bg-red-50',
                textColor: 'text-red-600'
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
                        <i class="fas fa-chart-line mr-1"></i>
                        <span>Updated just now</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // -------------------------------------------------------
    // SIDEBAR NAVIGATION
    // -------------------------------------------------------
    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const pageTitle = document.getElementById('page-title');
        const pageSubtitle = document.getElementById('page-subtitle');

        const pages = {
            dashboard: {
                title: 'Dashboard Overview',
                subtitle: 'Welcome back! Here’s your system overview.',
                section: 'dashboard-section'
            },
            admins: {
                title: 'Manage Administrators',
                subtitle: 'Create and manage admin accounts',
                section: 'admins-section'
            },
            activity: {
                title: 'Activity Logs',
                subtitle: 'Monitor system-wide activity',
                section: 'activity-section'
            }
        };

        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();

                navItems.forEach(n => n.classList.remove('active'));
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

    // -------------------------------------------------------
    // SECTION SWITCHING
    // -------------------------------------------------------
    showSection(section) {
        const sections = ['dashboard', 'admins', 'activity'];
        sections.forEach(sec => {
            const el = document.getElementById(`${sec}-section`);
            if (el) el.style.display = 'none';
        });

        const form = document.querySelector('.lg\\:col-span-2');
        const recent = document.querySelector('.lg\\:col-span-1');

        if (section === 'dashboard') {
            if (form) form.style.display = 'block';
            if (recent) recent.style.display = 'block';
        } else {
            if (form) form.style.display = 'none';
            if (recent) recent.style.display = 'none';
        }

        const targetSection = document.getElementById(`${section}-section`);
        if (targetSection) targetSection.style.display = 'block';

        // Load section-specific data
        if (section === 'admins' && typeof adminsManager !== 'undefined') {
            adminsManager.loadAdmins();
        }

        if (section === 'activity' && typeof activityManager !== 'undefined') {
            activityManager.loadActivity();
        }
    }

    // -------------------------------------------------------
    // GENERAL UI EVENTS
    // -------------------------------------------------------
    setupEventListeners() {
        console.log("SuperAdmin Dashboard Ready");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SuperAdminDashboard();
});

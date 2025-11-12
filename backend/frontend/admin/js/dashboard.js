class AdminDashboard {
    constructor() {
        this.stats = null;
        this.init();
    }

    async init() {
        await this.loadStats();
        this.setupNavigation();
        this.setupEventListeners();
    }

    async loadStats() {
        try {
            const response = await auth.makeAuthenticatedRequest('/admin/dashboard-stats');
            const data = await response.json();
            
            if (response.ok) {
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

    renderStats() {
        const statsContainer = document.getElementById('stats-cards');
        if (!statsContainer || !this.stats) return;

        const statsConfig = [
            { 
                label: 'Total Users', 
                value: this.stats.total_users, 
                icon: 'users', 
                color: 'blue',
                bgColor: 'bg-blue-50',
                textColor: 'text-blue-600'
            },
            { 
                label: 'Active Users', 
                value: this.stats.active_users, 
                icon: 'user-check', 
                color: 'green',
                bgColor: 'bg-green-50',
                textColor: 'text-green-600'
            },
            { 
                label: 'Avg Performance', 
                value: this.stats.avg_performance + '%', 
                icon: 'chart-line', 
                color: 'purple',
                bgColor: 'bg-purple-50',
                textColor: 'text-purple-600'
            },
            { 
                label: 'Remaining Slots', 
                value: this.stats.remaining_slots, 
                icon: 'user-plus', 
                color: 'orange',
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
                        <i class="fas fa-chart-line mr-1"></i>
                        <span>Updated just now</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderPerformanceOverview() {
        const container = document.getElementById('performance-chart');
        if (!container || !this.stats) return;

        container.innerHTML = `
            <div class="text-center">
                <div class="text-3xl font-bold text-gray-900 mb-2">${this.stats.avg_performance}%</div>
                <div class="text-sm text-gray-600">Average Performance</div>
            </div>
            <div class="space-y-3">
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">User Limit</span>
                    <span class="font-medium">${this.stats.total_users}/${this.stats.user_limit}</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-green-600 h-2 rounded-full" style="width: ${(this.stats.total_users / this.stats.user_limit) * 100}%"></div>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Active Users</span>
                    <span class="font-medium">${this.stats.active_users}</span>
                </div>
            </div>
        `;
    }

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const pageTitle = document.getElementById('page-title');
        const pageSubtitle = document.getElementById('page-subtitle');

        const pages = {
            dashboard: {
                title: 'Admin Dashboard',
                subtitle: 'Manage your team and track performance',
                section: 'dashboard-section'
            },
            users: {
                title: 'Manage Users',
                subtitle: 'Create and manage user accounts',
                section: 'users-section'
            },
            performance: {
                title: 'Performance Analytics',
                subtitle: 'Track and analyze user performance',
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

    showSection(section) {
        // Hide all sections first
        const sections = ['dashboard', 'users', 'performance'];
        sections.forEach(sec => {
            const element = document.getElementById(`${sec}-section`);
            if (element) {
                element.style.display = 'none';
            }
        });

        // Show create user form in dashboard section
        const createUserForm = document.querySelector('.lg\\:col-span-2');
        const performanceOverview = document.querySelector('.lg\\:col-span-1');
        
        if (section === 'dashboard') {
            if (createUserForm) createUserForm.style.display = 'block';
            if (performanceOverview) performanceOverview.style.display = 'block';
        } else {
            if (createUserForm) createUserForm.style.display = 'none';
            if (performanceOverview) performanceOverview.style.display = 'none';
            
            const targetSection = document.getElementById(`${section}-section`);
            if (targetSection) {
                targetSection.style.display = 'block';
            }
        }

        // Load section-specific data
        switch(section) {
            case 'users':
                if (typeof usersManager !== 'undefined') {
                    usersManager.loadUsers();
                }
                break;
            case 'performance':
                if (typeof performanceManager !== 'undefined') {
                    performanceManager.loadPerformance();
                }
                break;
        }
    }

    setupEventListeners() {
        console.log('Admin Dashboard initialized successfully');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AdminDashboard();
});
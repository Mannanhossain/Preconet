// class AdminDashboard {
//     constructor() {
//         this.stats = null;
//         this.init();
//     }

//     async init() {
//         await this.loadStats();
//         this.setupNavigation();
//         this.setupLogout();
//         this.setupEventListeners();
//     }

//     // ✅ Fetch dashboard stats from backend
//     async loadStats() {
//         try {
//             const response = await auth.makeAuthenticatedRequest('/admin/dashboard-stats'); // ✅ FIXED
//             const data = await response.json();
            
//             if (response.ok && data.stats) {
//                 this.stats = data.stats;
//                 this.renderStats();
//                 this.renderPerformanceOverview();
//             } else {
//                 auth.showNotification('Failed to load dashboard stats', 'error');
//             }
//         } catch (error) {
//             console.error('Error loading stats:', error);
//             auth.showNotification('Error loading dashboard data', 'error');
//         }
//     }

//     // ✅ Display main dashboard stats
//     renderStats() {
//         const statsContainer = document.getElementById('stats-cards');
//         if (!statsContainer || !this.stats) return;

//         const statsConfig = [
//             { 
//                 label: 'Total Users', 
//                 value: this.stats.total_users ?? 0, 
//                 icon: 'users', 
//                 bgColor: 'bg-blue-50',
//                 textColor: 'text-blue-600'
//             },
//             { 
//                 label: 'Active Users', 
//                 value: this.stats.active_users ?? 0, 
//                 icon: 'user-check', 
//                 bgColor: 'bg-green-50',
//                 textColor: 'text-green-600'
//             },
//             { 
//                 label: 'Expired Users', 
//                 value: this.stats.expired_users ?? 0, 
//                 icon: 'user-times', 
//                 bgColor: 'bg-red-50',
//                 textColor: 'text-red-600'
//             },
//             { 
//                 label: 'Remaining Slots', 
//                 value: this.stats.remaining_slots ?? 0, 
//                 icon: 'user-plus', 
//                 bgColor: 'bg-orange-50',
//                 textColor: 'text-orange-600'
//             }
//         ];

//         statsContainer.innerHTML = statsConfig.map(stat => `
//             <div class="stat-card bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
//                 <div class="flex items-center justify-between">
//                     <div>
//                         <p class="text-sm font-medium text-gray-600 mb-1">${stat.label}</p>
//                         <p class="text-3xl font-bold text-gray-900">${stat.value}</p>
//                     </div>
//                     <div class="${stat.bgColor} w-12 h-12 rounded-lg flex items-center justify-center">
//                         <i class="fas fa-${stat.icon} ${stat.textColor} text-lg"></i>
//                     </div>
//                 </div>
//                 <div class="mt-4 pt-4 border-t border-gray-100">
//                     <div class="flex items-center text-xs text-gray-500">
//                         <i class="fas fa-clock mr-1"></i>
//                         <span>Updated just now</span>
//                     </div>
//                 </div>
//             </div>
//         `).join('');
//     }

//     // ✅ Performance overview card
//     renderPerformanceOverview() {
//         const container = document.getElementById('performance-chart');
//         if (!container || !this.stats) return;

//         const avgPerf = this.stats.avg_performance ?? 0;
//         const totalUsers = this.stats.total_users ?? 0;
//         const userLimit = this.stats.user_limit ?? 1;
//         const usagePercent = (totalUsers / userLimit) * 100;

//         container.innerHTML = `
//             <div class="text-center mb-4">
//                 <div class="text-3xl font-bold text-gray-900 mb-1">${avgPerf}%</div>
//                 <div class="text-sm text-gray-600">Average Performance</div>
//             </div>
//             <div class="space-y-3">
//                 <div class="flex justify-between text-sm">
//                     <span class="text-gray-600">User Limit</span>
//                     <span class="font-medium">${totalUsers}/${userLimit}</span>
//                 </div>
//                 <div class="w-full bg-gray-200 rounded-full h-2">
//                     <div class="bg-green-600 h-2 rounded-full" style="width: ${usagePercent}%"></div>
//                 </div>
//                 <div class="flex justify-between text-sm">
//                     <span class="text-gray-600">Active Users</span>
//                     <span class="font-medium">${this.stats.active_users}</span>
//                 </div>
//             </div>
//         `;
//     }

//     // ✅ Navigation section switching
//     setupNavigation() {
//         const navItems = document.querySelectorAll('.nav-item');
//         const pageTitle = document.getElementById('page-title');
//         const pageSubtitle = document.getElementById('page-subtitle');

//         const pages = {
//             dashboard: {
//                 title: 'Admin Dashboard',
//                 subtitle: 'Manage your users and track performance',
//                 section: 'dashboard-section'
//             },
//             users: {
//                 title: 'Manage Users',
//                 subtitle: 'Add, edit, and manage user accounts',
//                 section: 'users-section'
//             },
//             performance: {
//                 title: 'Performance Analytics',
//                 subtitle: 'Monitor and analyze user performance data',
//                 section: 'performance-section'
//             }
//         };

//         navItems.forEach(item => {
//             item.addEventListener('click', (e) => {
//                 e.preventDefault();
//                 navItems.forEach(nav => nav.classList.remove('active'));
//                 item.classList.add('active');

//                 const target = item.getAttribute('href').substring(1);
//                 const page = pages[target];

//                 if (page) {
//                     pageTitle.textContent = page.title;
//                     pageSubtitle.textContent = page.subtitle;
//                     this.showSection(target);
//                 }
//             });
//         });
//     }

//     // ✅ Show/hide sections dynamically
//     showSection(section) {
//         const sections = ['dashboard', 'users', 'performance'];
//         sections.forEach(sec => {
//             const el = document.getElementById(`${sec}-section`);
//             if (el) el.style.display = 'none';
//         });

//         const targetEl = document.getElementById(`${section}-section`);
//         if (targetEl) targetEl.style.display = 'block';

//         switch (section) {
//             case 'users':
//                 if (typeof usersManager !== 'undefined') usersManager.loadUsers();
//                 break;
//             case 'performance':
//                 if (typeof performanceManager !== 'undefined') performanceManager.loadPerformance();
//                 break;
//         }
//     }

//     // ✅ Logout handling
//     setupLogout() {
//         const logoutBtn = document.getElementById('logout-btn');
//         if (!logoutBtn) return;

//         logoutBtn.addEventListener('click', (e) => {
//             e.preventDefault();
//             sessionStorage.removeItem('admin_token');
//             sessionStorage.removeItem('admin_user');
//             auth.showNotification('Logged out successfully', 'success');
//             setTimeout(() => {
//                 window.location.href = '/admin/login.html';
//             }, 1000);
//         });
//     }

//     setupEventListeners() {
//         console.log('✅ Admin Dashboard initialized successfully');
//     }
// }

// document.addEventListener('DOMContentLoaded', () => {
//     new AdminDashboard();
// });



class AdminDashboard {
    constructor() {
        this.stats = null;
        this.currentSection = 'dashboard';
        this.users = [];
        this.init();
    }

    async init() {
        // Check authentication first
        if (!this.checkAuth()) {
            return;
        }
        
        await this.loadStats();
        this.setupNavigation();
        this.setupLogout();
        this.setupEventListeners();
        
        // Load users for the users section
        await this.loadUsers();
    }

    checkAuth() {
        const token = sessionStorage.getItem('admin_token');
        if (!token) {
            window.location.href = '/admin/login.html';
            return false;
        }
        return true;
    }

    // ✅ Fetch dashboard stats from backend
    async loadStats() {
        try {
            const response = await auth.makeAuthenticatedRequest('/admin/dashboard-stats');
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

    // ✅ Load all users for management
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
            console.error('Error loading users:', error);
            auth.showNotification('Error loading users', 'error');
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
                label: 'Users with Sync Data', 
                value: this.stats.users_with_sync ?? 0, 
                icon: 'sync', 
                bgColor: 'bg-purple-50',
                textColor: 'text-purple-600'
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
        const userLimit = this.stats.user_limit ?? 1;
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
                    <div class="bg-green-600 h-2 rounded-full" style="width: ${Math.min(usagePercent, 100)}%"></div>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Sync Rate</span>
                    <span class="font-medium">${this.stats.sync_rate ?? 0}%</span>
                </div>
            </div>
        `;
    }

    // ✅ Render users table with sync data access
    renderUsersTable() {
        const container = document.getElementById('users-table-body');
        if (!container) return;

        container.innerHTML = this.users.map(user => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10 bg-blue-500 rounded-full flex items-center justify-center">
                            <span class="text-white font-medium">${user.name.charAt(0).toUpperCase()}</span>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${user.name}</div>
                            <div class="text-sm text-gray-500">${user.email}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${user.phone || 'N/A'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${user.performance_score}%
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${user.last_sync ? new Date(user.last_sync).toLocaleDateString() : 'Never'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="adminDashboard.viewUserData(${user.id})" class="text-blue-600 hover:text-blue-900 mr-3">
                        <i class="fas fa-database mr-1"></i>View Data
                    </button>
                    <button onclick="adminDashboard.editUser(${user.id})" class="text-indigo-600 hover:text-indigo-900 mr-3">
                        <i class="fas fa-edit mr-1"></i>Edit
                    </button>
                    <button onclick="adminDashboard.deleteUser(${user.id})" class="text-red-600 hover:text-red-900">
                        <i class="fas fa-trash mr-1"></i>Delete
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // ✅ Fetch and display user app data
    async viewUserData(userId) {
        try {
            const user = this.users.find(u => u.id === userId);
            if (!user) return;

            const response = await auth.makeAuthenticatedRequest(`/admin/user-data/${userId}`);
            const data = await response.json();
            
            if (!response.ok) {
                auth.showNotification(data.error || 'Failed to load user data', 'error');
                return;
            }

            this.renderUserDataModal(user, data);
        } catch (error) {
            console.error('Error loading user data:', error);
            auth.showNotification('Error loading user data', 'error');
        }
    }

    // ✅ Render user data in modal
    renderUserDataModal(user, data) {
        const modal = document.getElementById('user-data-modal');
        const content = document.getElementById('user-data-content');
        
        if (!modal || !content) return;

        // Analytics data
        const analytics = data.analytics || {};
        const callHistory = data.call_history || [];
        const attendance = data.attendance || {};
        const contacts = data.contacts || [];

        content.innerHTML = `
            <div class="bg-white rounded-lg">
                <!-- Header -->
                <div class="border-b border-gray-200 px-6 py-4">
                    <h3 class="text-lg font-medium text-gray-900">User Data: ${user.name}</h3>
                    <p class="text-sm text-gray-500">Last sync: ${data.last_sync ? new Date(data.last_sync).toLocaleString() : 'Never'}</p>
                </div>

                <!-- Analytics -->
                <div class="px-6 py-4 border-b border-gray-200">
                    <h4 class="font-medium text-gray-900 mb-3">Analytics</h4>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="text-center p-3 bg-blue-50 rounded-lg">
                            <div class="text-2xl font-bold text-blue-600">${analytics.total_calls || 0}</div>
                            <div class="text-sm text-blue-800">Total Calls</div>
                        </div>
                        <div class="text-center p-3 bg-green-50 rounded-lg">
                            <div class="text-2xl font-bold text-green-600">${analytics.meetings_attended || 0}</div>
                            <div class="text-sm text-green-800">Meetings</div>
                        </div>
                    </div>
                </div>

                <!-- Call History -->
                <div class="px-6 py-4 border-b border-gray-200">
                    <h4 class="font-medium text-gray-900 mb-3">Call History (${callHistory.length})</h4>
                    <div class="max-h-40 overflow-y-auto">
                        ${callHistory.length > 0 ? callHistory.map(call => `
                            <div class="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                                <div>
                                    <div class="font-medium">${call.number || 'Unknown'}</div>
                                    <div class="text-sm text-gray-500">${call.type || 'N/A'} - ${call.duration || 0}s</div>
                                </div>
                                <div class="text-sm text-gray-500">
                                    ${call.timestamp ? new Date(call.timestamp).toLocaleDateString() : 'N/A'}
                                </div>
                            </div>
                        `).join('') : '<p class="text-gray-500 text-center py-2">No call history</p>'}
                    </div>
                </div>

                <!-- Contacts -->
                <div class="px-6 py-4">
                    <h4 class="font-medium text-gray-900 mb-3">Contacts (${contacts.length})</h4>
                    <div class="max-h-40 overflow-y-auto">
                        ${contacts.length > 0 ? contacts.map(contact => `
                            <div class="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                                <div class="font-medium">${contact.name || 'Unknown'}</div>
                                <div class="text-sm text-gray-500">${contact.phone || 'N/A'}</div>
                            </div>
                        `).join('') : '<p class="text-gray-500 text-center py-2">No contacts</p>'}
                    </div>
                </div>
            </div>
        `;

        // Show modal
        modal.classList.remove('hidden');
    }

    // ✅ Close user data modal
    closeUserDataModal() {
        const modal = document.getElementById('user-data-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
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
                    this.currentSection = target;
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

        if (section === 'users' && this.users.length === 0) {
            this.loadUsers();
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
        // Close modal when clicking outside
        const modal = document.getElementById('user-data-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeUserDataModal();
                }
            });
        }

        // Close modal button
        const closeBtn = document.getElementById('close-user-data-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeUserDataModal());
        }

        console.log('✅ Admin Dashboard initialized successfully');
    }

    // Placeholder methods for user management
    editUser(userId) {
        auth.showNotification('Edit user functionality coming soon', 'info');
    }

    deleteUser(userId) {
        if (confirm('Are you sure you want to delete this user?')) {
            auth.showNotification('Delete user functionality coming soon', 'info');
        }
    }
}

// Global instance
const adminDashboard = new AdminDashboard();

document.addEventListener('DOMContentLoaded', () => {
    // Modal close handler
    const closeBtn = document.getElementById('close-user-data-modal');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => adminDashboard.closeUserDataModal());
    }
});
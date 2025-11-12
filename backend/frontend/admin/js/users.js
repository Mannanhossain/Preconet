class UsersManager {
    constructor() {
        this.users = [];
        this.init();
    }

    init() {
        this.setupCreateUserForm();
    }

    setupCreateUserForm() {
        const form = document.getElementById('createUserForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.createUser();
            });
        }
    }

    // ✅ Create new user
    async createUser() {
        const formData = {
            name: document.getElementById('userName').value.trim(),
            email: document.getElementById('userEmail').value.trim(),
            phone: document.getElementById('userPhone').value.trim(),
            password: document.getElementById('userPassword').value.trim() || '123456'
        };

        try {
            const response = await auth.makeAuthenticatedRequest('/api/admin/create-user', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                auth.showNotification('✅ User created successfully!', 'success');
                document.getElementById('createUserForm').reset();
                await this.loadUsers();

                // Reload dashboard stats
                if (typeof adminDashboard !== 'undefined') {
                    await adminDashboard.loadStats();
                }
            } else {
                auth.showNotification(data.error || 'Failed to create user', 'error');
            }
        } catch (error) {
            console.error('Error creating user:', error);
            auth.showNotification('Error creating user account', 'error');
        }
    }

    // ✅ Load all users
    async loadUsers() {
        try {
            const response = await auth.makeAuthenticatedRequest('/api/admin/users');
            const data = await response.json();
            
            if (response.ok && Array.isArray(data.users)) {
                this.users = data.users;
                this.renderUsers();
            } else {
                auth.showNotification('Failed to load users', 'error');
            }
        } catch (error) {
            console.error('Error loading users:', error);
            auth.showNotification('Error loading users list', 'error');
        }
    }

    // ✅ Render users in table
    renderUsers() {
        const tableBody = document.getElementById('users-table-body');
        if (!tableBody) return;

        if (this.users.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-4 py-8 text-center text-gray-500">
                        <i class="fas fa-users text-3xl mb-2 text-gray-300"></i>
                        <p>No users found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = this.users.map(user => `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-4">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                            <i class="fas fa-user text-green-600"></i>
                        </div>
                        <div>
                            <p class="font-medium text-gray-900">${user.name}</p>
                            <p class="text-sm text-gray-500">${user.email}</p>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-4 text-sm text-gray-900">${user.phone || 'N/A'}</td>
                <td class="px-4 py-4">
                    <div class="flex items-center space-x-2">
                        <div class="w-16 bg-gray-200 rounded-full h-2">
                            <div class="bg-blue-600 h-2 rounded-full" style="width: ${(user.performance_score || 0)}%"></div>
                        </div>
                        <span class="text-sm font-medium text-gray-700">${user.performance_score || 0}%</span>
                    </div>
                </td>
                <td class="px-4 py-4">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                        user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }">
                        <i class="fas fa-circle mr-1 text-xs"></i>
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="px-4 py-4">
                    <div class="flex items-center space-x-2">
                        <button class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" onclick="usersManager.editUser(${user.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors" onclick="usersManager.deleteUser(${user.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    // 🧩 Edit user (future implementation)
    async editUser(userId) {
        auth.showNotification('Edit feature coming soon!', 'info');
    }

    // ✅ Delete user
    async deleteUser(userId) {
        if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await auth.makeAuthenticatedRequest(`/api/admin/delete-user/${userId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                auth.showNotification('✅ User deleted successfully!', 'success');
                await this.loadUsers();

                if (typeof adminDashboard !== 'undefined') {
                    await adminDashboard.loadStats();
                }
            } else {
                auth.showNotification(data.error || 'Failed to delete user', 'error');
            }
        } catch (error) {
            console.error('Error deleting user:', error);
            auth.showNotification('Error deleting user', 'error');
        }
    }
}

const usersManager = new UsersManager();

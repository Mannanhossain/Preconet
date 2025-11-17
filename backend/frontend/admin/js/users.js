class UsersManager {
    constructor() {
        this.users = [];
        window.usersManager = this;
        this.init();
    }

    init() {
        this.setupCreateUserForm();
        this.loadUsers();
    }

    // ---------------------------------------------------------
    // CREATE USER FORM LISTENER
    // ---------------------------------------------------------
    setupCreateUserForm() {
        const form = document.getElementById("createUserForm");
        if (!form) return;

        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            await this.createUser();
        });
    }

    // ---------------------------------------------------------
    // CREATE USER
    // ---------------------------------------------------------
    async createUser() {
        const name = document.getElementById("userName").value.trim();
        const email = document.getElementById("userEmail").value.trim();
        const phone = document.getElementById("userPhone").value.trim();
        const password = document.getElementById("userPassword").value.trim() || "123456";

        if (!name || !email) {
            auth.showNotification("Name & Email are required", "error");
            return;
        }

        try {
            const response = await auth.makeAuthenticatedRequest("/api/users/register", {
                method: "POST",
                body: JSON.stringify({ name, email, phone, password })
            });

            const data = await response.json();

            if (!response.ok) {
                auth.showNotification(data.error || "Failed to create user", "error");
                return;
            }

            auth.showNotification("User created successfully!", "success");
            document.getElementById("createUserForm").reset();

            await this.loadUsers();
            if (window.adminDashboard) await adminDashboard.loadStats();

        } catch (error) {
            console.error(error);
            auth.showNotification("Error creating user", "error");
        }
    }

    // ---------------------------------------------------------
    // LOAD USERS
    // ---------------------------------------------------------
    async loadUsers() {
        try {
            const response = await auth.makeAuthenticatedRequest("/api/admin/users");
            const data = await response.json();

            if (response.ok) {
                this.users = data.users || [];
                this.renderUsers();
            } else {
                auth.showNotification(data.error || "Failed to load users", "error");
            }

        } catch (error) {
            console.error(error);
            auth.showNotification("Error loading users", "error");
        }
    }

    // ---------------------------------------------------------
    // RENDER USERS TABLE
    // ---------------------------------------------------------
    renderUsers() {
        const tableBody = document.getElementById("users-table-body");
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

        tableBody.innerHTML = this.users
            .map(
                (user) => `
            <tr class="hover:bg-gray-50 transition">

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

                <td class="px-4 py-4">${user.phone || "N/A"}</td>

                <td class="px-4 py-4">
                    <div class="flex items-center space-x-2">
                        <div class="w-16 bg-gray-200 h-2 rounded-full">
                            <div class="bg-blue-600 h-2 rounded-full" style="width:${user.performance_score || 0}%"></div>
                        </div>
                        <span class="text-sm font-medium">${user.performance_score || 0}%</span>
                    </div>
                </td>

                <td class="px-4 py-4">
                    <span class="px-3 py-1 rounded-full text-sm ${
                        user.is_active
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                    }">
                        ${user.is_active ? "Active" : "Inactive"}
                    </span>
                </td>

                <td class="px-4 py-4">
                    <div class="flex items-center space-x-2">
                        <button onclick="usersManager.editUser(${user.id})"
                            class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg">
                            <i class="fas fa-edit"></i>
                        </button>

                        <button onclick="usersManager.deleteUser(${user.id})"
                            class="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>

            </tr>
        `
            )
            .join("");
    }

    // ---------------------------------------------------------
    // EDIT USER (COMING SOON)
    // ---------------------------------------------------------
    async editUser(userId) {
        auth.showNotification("Edit user feature coming soon!", "info");
    }

    // ---------------------------------------------------------
    // DELETE USER
    // ---------------------------------------------------------
    async deleteUser(userId) {
        if (!confirm("Delete this user permanently?")) return;

        try {
            const response = await auth.makeAuthenticatedRequest(`/api/admin/delete-user/${userId}`, {
                method: "DELETE",
            });

            const data = await response.json();

            if (response.ok) {
                auth.showNotification("User deleted successfully!", "success");
                await this.loadUsers();
                if (window.adminDashboard) await adminDashboard.loadStats();
            } else {
                auth.showNotification(data.error || "Failed to delete user", "error");
            }

        } catch (error) {
            console.error(error);
            auth.showNotification("Error deleting user", "error");
        }
    }
}

const usersManager = new UsersManager();

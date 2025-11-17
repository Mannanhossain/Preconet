/* ============================================================
    USERS MANAGER – Call Manager Pro (Admin Panel)
============================================================ */

class UsersManager {
    constructor() {
        this.users = [];
        window.usersManager = this;
    }

    /* ============================================================
       LOAD ALL USERS
    ============================================================ */
    async loadUsers() {
        try {
            const resp = await auth.makeAuthenticatedRequest("/api/admin/users");
            const data = await resp.json();

            if (!resp.ok) {
                auth.showNotification(data.error || "Failed to load users", "error");
                return;
            }

            this.users = data.users;
            this.renderUsers();
        } catch (err) {
            console.error("Users load error:", err);
            auth.showNotification("Error loading users", "error");
        }
    }

    /* ============================================================
       RENDER USERS TABLE
    ============================================================ */
    renderUsers() {
        const body = document.getElementById("users-table-body");
        if (!body) return;

        if (this.users.length === 0) {
            body.innerHTML = `
                <tr><td colspan="5" class="text-center py-6 text-gray-400">
                    No users found
                </td></tr>`;
            return;
        }

        body.innerHTML = this.users
            .map(
                (u) => `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-3">
                    <div class="flex items-center">
                        <div class="h-10 w-10 bg-blue-600 text-white rounded-full flex items-center justify-center">
                            ${u.name[0].toUpperCase()}
                        </div>
                        <div class="ml-3">
                            <p class="font-semibold">${u.name}</p>
                            <p class="text-sm text-gray-500">${u.email}</p>
                        </div>
                    </div>
                </td>

                <td class="px-4 py-3">${u.phone || "N/A"}</td>

                <td class="px-4 py-3">${u.performance_score}%</td>

                <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs rounded-full ${
                        u.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                    }">
                        ${u.is_active ? "Active" : "Inactive"}
                    </span>
                </td>

                <td class="px-4 py-3 text-right">
                    <button onclick="usersManager.viewUserData(${u.id})"
                        class="text-blue-600 mr-3">
                        <i class="fas fa-eye"></i>
                    </button>

                    <button onclick="usersManager.editUser(${u.id})"
                        class="text-indigo-600 mr-3">
                        <i class="fas fa-edit"></i>
                    </button>

                    <button onclick="usersManager.deleteUser(${u.id})"
                        class="text-red-600">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `
            )
            .join("");
    }

    /* ============================================================
       LOAD + VIEW USER DATA (Calls, Analytics, Contacts, Attendance)
    ============================================================ */
    async viewUserData(userId) {
        try {
            const resp = await auth.makeAuthenticatedRequest(
                `/api/admin/user-data/${userId}`
            );

            const data = await resp.json();

            if (!resp.ok) {
                auth.showNotification(data.error || "Failed to load user data", "error");
                return;
            }

            const user = this.users.find((u) => u.id === userId);
            this.renderUserModal(user, data);

        } catch (err) {
            console.error("User data error:", err);
            auth.showNotification("Error loading user details", "error");
        }
    }

    /* ============================================================
       RENDER USER MODAL (Full Data)
    ============================================================ */
    renderUserModal(user, data) {
        const modal = document.getElementById("user-data-modal");
        const content = document.getElementById("user-data-content");

        content.innerHTML = `
            <h2 class="text-xl font-bold">${user.name}</h2>
            <p class="text-sm text-gray-500 mb-4">Last Sync: 
                ${data.last_sync ? new Date(data.last_sync).toLocaleString() : "Never"}
            </p>

            <div class="space-y-6">

                <div>
                    <h3 class="font-semibold mb-2">Analytics</h3>
                    <pre class="bg-gray-100 p-3 rounded text-sm">${JSON.stringify(
                        data.analytics,
                        null,
                        2
                    )}</pre>
                </div>

                <div>
                    <h3 class="font-semibold mb-2">Call History (${data.call_history?.length})</h3>
                    <pre class="bg-gray-100 p-3 rounded text-sm">${JSON.stringify(
                        data.call_history,
                        null,
                        2
                    )}</pre>
                </div>

                <div>
                    <h3 class="font-semibold mb-2">Contacts (${data.contacts?.length})</h3>
                    <pre class="bg-gray-100 p-3 rounded text-sm">${JSON.stringify(
                        data.contacts,
                        null,
                        2
                    )}</pre>
                </div>

                <div>
                    <h3 class="font-semibold mb-2">Attendance Records</h3>
                    <pre class="bg-gray-100 p-3 rounded text-sm">${JSON.stringify(
                        data.attendance,
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
        modal.classList.add("hidden");
    }

    /* ============================================================
       CREATE USER (From Create User Form)
    ============================================================ */
    async handleCreateUser() {
        const form = document.getElementById("createUserForm");
        if (!form) return;

        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const payload = {
                name: document.getElementById("userName").value.trim(),
                email: document.getElementById("userEmail").value.trim(),
                phone: document.getElementById("userPhone").value.trim(),
                password: document.getElementById("userPassword").value.trim(),
            };

            try {
                const resp = await auth.makeAuthenticatedRequest(
                    "/api/admin/create-user",
                    {
                        method: "POST",
                        body: JSON.stringify(payload),
                    }
                );

                const res = await resp.json();

                if (resp.ok) {
                    auth.showNotification("User created successfully!", "success");
                    form.reset();
                    this.loadUsers();
                } else {
                    auth.showNotification(res.error || "Failed to create user", "error");
                }
            } catch (err) {
                console.error("Create user error:", err);
                auth.showNotification("Error creating user", "error");
            }
        });
    }

    /* ============================================================
       DELETE USER
    ============================================================ */
    async deleteUser(id) {
        if (!confirm("Are you sure you want to delete this user?")) return;

        try {
            const resp = await auth.makeAuthenticatedRequest(
                `/api/admin/delete-user/${id}`,
                { method: "DELETE" }
            );

            const res = await resp.json();

            if (resp.ok) {
                auth.showNotification("User deleted", "success");
                this.loadUsers();
            } else {
                auth.showNotification(res.error || "Unable to delete user", "error");
            }
        } catch (err) {
            console.error(err);
            auth.showNotification("Error deleting user", "error");
        }
    }

    /* ============================================================
       EDIT USER (Placeholder)
    ============================================================ */
    editUser(id) {
        auth.showNotification("Edit user feature coming soon", "info");
    }
}

/* ============================================================
   INIT
============================================================ */
document.addEventListener("DOMContentLoaded", () => {
    window.usersManager = new UsersManager();
    usersManager.handleCreateUser();
});

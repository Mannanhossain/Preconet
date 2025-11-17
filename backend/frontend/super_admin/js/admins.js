class AdminsManager {
    constructor() {
        this.admins = [];
        this.init();
    }

    init() {
        this.setupCreateAdminForm();
        this.loadAdmins();
    }

    // ---------------------------------------------------------
    // SETUP CREATE ADMIN FORM
    // ---------------------------------------------------------
    setupCreateAdminForm() {
        const form = document.getElementById('createAdminForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createAdmin();
            });
        }

        // Default expiry date setup
        const expiryDate = document.getElementById('expiryDate');
        if (expiryDate) {
            const today = new Date().toISOString().split("T")[0];
            expiryDate.min = today;

            const future = new Date();
            future.setDate(future.getDate() + 30);
            expiryDate.value = future.toISOString().split("T")[0];
        }
    }

    // ---------------------------------------------------------
    // CREATE ADMIN
    // ---------------------------------------------------------
    async createAdmin() {
        const formData = {
            name: document.getElementById("adminName").value.trim(),
            email: document.getElementById("adminEmail").value.trim(),
            password: document.getElementById("adminPassword").value.trim(),
            user_limit: Number(document.getElementById("userLimit").value) || 10,
            expiry_date: document.getElementById("expiryDate").value
        };

        if (!formData.name || !formData.email || !formData.password || !formData.expiry_date) {
            auth.showNotification("Please fill all fields", "error");
            return;
        }

        try {
            const response = await auth.makeAuthenticatedRequest(
                "/api/superadmin/create-admin",
                {
                    method: "POST",
                    body: JSON.stringify(formData)
                }
            );

            const data = await response.json();

            if (response.ok) {
                auth.showNotification("Admin created successfully!", "success");
                document.getElementById("createAdminForm").reset();

                // Reset expiry date again
                const expiryDate = document.getElementById("expiryDate");
                const next = new Date();
                next.setDate(next.getDate() + 30);
                expiryDate.value = next.toISOString().split("T")[0];

                this.loadAdmins();
            } else {
                auth.showNotification(data.error || "Failed to create admin", "error");
            }

        } catch (err) {
            console.error("Error creating admin:", err);
            auth.showNotification("Error creating admin", "error");
        }
    }

    // ---------------------------------------------------------
    // LOAD ADMINS LIST
    // ---------------------------------------------------------
    async loadAdmins() {
        try {
            const response = await auth.makeAuthenticatedRequest("/api/superadmin/admins");
            const data = await response.json();

            if (response.ok) {
                this.admins = data.admins || [];
                this.renderAdmins();
            } else {
                auth.showNotification(data.error || "Failed to load admins", "error");
            }

        } catch (err) {
            console.error("Error loading admins:", err);
            auth.showNotification("Error loading admins list", "error");
        }
    }

    // ---------------------------------------------------------
    // RENDER ADMIN TABLE
    // ---------------------------------------------------------
    renderAdmins() {
        const tableBody = document.getElementById("admins-table-body");
        if (!tableBody) return;

        if (this.admins.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-4 py-8 text-center text-gray-500">
                        <i class="fas fa-users text-3xl mb-2 text-gray-300"></i>
                        <p>No admins found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = this.admins.map(admin => {

            const expireDate = admin.expiry_date ? new Date(admin.expiry_date) : null;
            const expiryStr = expireDate && !isNaN(expireDate) ? expireDate.toLocaleDateString() : "N/A";

            const statusBadge = !admin.is_active
                ? `<span class="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium"><i class="fas fa-circle mr-1 text-xs"></i>Inactive</span>`
                : admin.is_expired
                ? `<span class="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm font-medium"><i class="fas fa-circle mr-1 text-xs"></i>Expired</span>`
                : `<span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium"><i class="fas fa-circle mr-1 text-xs"></i>Active</span>`;

            return `
                <tr class="hover:bg-gray-50 transition">

                    <td class="px-4 py-4">
                        <div class="flex items-center space-x-3">
                            <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-user-cog text-blue-600"></i>
                            </div>
                            <div>
                                <p class="font-medium text-gray-900">${admin.name}</p>
                                <p class="text-sm text-gray-500">${admin.email}</p>
                            </div>
                        </div>
                    </td>

                    <td class="px-4 py-4">
                        <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                            ${admin.user_count}/${admin.user_limit} users
                        </span>
                    </td>

                    <td class="px-4 py-4">
                        <div class="flex items-center space-x-2">
                            <i class="fas fa-calendar ${
                                admin.is_expired ? 'text-red-500' : 'text-green-500'
                            }"></i>
                            <span>${expiryStr}</span>
                        </div>
                    </td>

                    <td class="px-4 py-4">
                        ${statusBadge}
                    </td>

                    <td class="px-4 py-4">
                        <div class="flex items-center space-x-2">
                            <button class="p-2 text-blue-600 hover:bg-blue-50"
                                onclick="adminsManager.editAdmin(${admin.id})">
                                <i class="fas fa-edit"></i>
                            </button>

                            <button class="p-2 text-red-600 hover:bg-red-50"
                                onclick="adminsManager.deleteAdmin(${admin.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>

                </tr>
            `;
        }).join('');
    }

    // ---------------------------------------------------------
    // EDIT COMING SOON
    // ---------------------------------------------------------
    editAdmin(id) {
        auth.showNotification("Edit feature coming soon!", "info");
    }

    // ---------------------------------------------------------
    // DELETE ADMIN (function disabled because backend missing)
    // ---------------------------------------------------------
    deleteAdmin(id) {
        auth.showNotification("Delete admin API not implemented in backend", "error");
    }
}

const adminsManager = new AdminsManager();

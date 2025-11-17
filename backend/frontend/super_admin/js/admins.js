class AdminsManager {
    constructor() {
        this.admins = [];
        this.init();
    }

    // =====================================================
    // INITIAL SETUP
    // =====================================================
    init() {
        this.setupCreateAdminForm();
        this.loadAdmins();
    }

    // =====================================================
    // SETUP CREATE ADMIN FORM
    // =====================================================
    setupCreateAdminForm() {
        const form = document.getElementById("createAdminForm");

        if (form) {
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                this.createAdmin();
            });
        }

        // Auto-set expiry date to today + 30 days
        const expiryDate = document.getElementById("expiryDate");
        if (expiryDate) {
            const today = new Date().toISOString().split("T")[0];
            expiryDate.min = today;

            const next = new Date();
            next.setDate(next.getDate() + 30);
            expiryDate.value = next.toISOString().split("T")[0];
        }
    }

    // =====================================================
    // CREATE NEW ADMIN
    // =====================================================
    async createAdmin() {
        const name = document.getElementById("adminName").value.trim();
        const email = document.getElementById("adminEmail").value.trim();
        const password = document.getElementById("adminPassword").value.trim();
        const userLimit = Number(document.getElementById("userLimit").value || 10);
        const expiryDate = document.getElementById("expiryDate").value;

        if (!name || !email || !password || !expiryDate) {
            auth.showNotification("Please fill all fields", "error");
            return;
        }

        const payload = {
            name,
            email,
            password,
            user_limit: userLimit,
            expiry_date: expiryDate
        };

        try {
            const response = await auth.makeAuthenticatedRequest(
                "/api/superadmin/create-admin",
                {
                    method: "POST",
                    body: JSON.stringify(payload)
                }
            );

            const data = await response.json();

            if (response.ok) {
                auth.showNotification("Admin created successfully!", "success");

                document.getElementById("createAdminForm").reset();

                // restore default expiry date
                const expiryDateInput = document.getElementById("expiryDate");
                const next = new Date();
                next.setDate(next.getDate() + 30);
                expiryDateInput.value = next.toISOString().split("T")[0];

                this.loadAdmins();
            } else {
                auth.showNotification(data.error || "Failed to create admin", "error");
            }

        } catch (error) {
            console.error("Error creating admin:", error);
            auth.showNotification("Server error while creating admin", "error");
        }
    }

    // =====================================================
    // LOAD ADMINS
    // =====================================================
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
        } catch (error) {
            console.error("Error loading admins:", error);
            auth.showNotification("Server error while loading admins", "error");
        }
    }

    // =====================================================
    // RENDER ADMIN TABLE
    // =====================================================
    renderAdmins() {
        const tableBody = document.getElementById("admins-table-body");
        if (!tableBody) return;

        if (this.admins.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="py-10 text-center text-gray-500">
                        <i class="fas fa-users text-3xl mb-2 text-gray-300"></i>
                        <p>No admins found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = this.admins
            .map(admin => {
                const exp = admin.expiry_date ? new Date(admin.expiry_date) : null;
                const expStr = exp && !isNaN(exp) ? exp.toLocaleDateString() : "N/A";

                const status =
                    !admin.is_active
                        ? `<span class="bg-red-100 text-red-800 px-3 py-1 rounded-full text-xs"><i class="fas fa-circle mr-1"></i>Inactive</span>`
                        : admin.is_expired
                        ? `<span class="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-xs"><i class="fas fa-circle mr-1"></i>Expired</span>`
                        : `<span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs"><i class="fas fa-circle mr-1"></i>Active</span>`;

                return `
                <tr class="hover:bg-gray-50 transition">

                    <!-- NAME + EMAIL -->
                    <td class="px-4 py-4">
                        <div class="flex items-center space-x-3">
                            <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-user-cog text-blue-600"></i>
                            </div>
                            <div>
                                <p class="font-semibold text-gray-900">${admin.name}</p>
                                <p class="text-xs text-gray-500">${admin.email}</p>
                            </div>
                        </div>
                    </td>

                    <!-- USER LIMIT -->
                    <td class="px-4 py-4">
                        <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                            ${admin.user_count}/${admin.user_limit}
                        </span>
                    </td>

                    <!-- EXPIRY DATE -->
                    <td class="px-4 py-4">
                        <i class="fas fa-calendar text-gray-500 mr-1"></i>
                        <span>${expStr}</span>
                    </td>

                    <!-- STATUS -->
                    <td class="px-4 py-4">
                        ${status}
                    </td>

                    <!-- ACTIONS -->
                    <td class="px-4 py-4">
                        <div class="flex space-x-2">
                            <button onclick="adminsManager.editAdmin(${admin.id})"
                                class="text-blue-600 hover:bg-blue-50 p-2 rounded">
                                <i class="fas fa-edit"></i>
                            </button>

                            <button onclick="adminsManager.deleteAdmin(${admin.id})"
                                class="text-red-600 hover:bg-red-50 p-2 rounded">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>

                </tr>
                `;
            })
            .join("");
    }

    // =====================================================
    // EDIT (COMING SOON)
    // =====================================================
    editAdmin(id) {
        auth.showNotification("Edit feature coming soon!", "info");
    }

    // =====================================================
    // DELETE ADMIN (NOT IMPLEMENTED)
    // =====================================================
    deleteAdmin(id) {
        auth.showNotification("Delete API not implemented in backend", "error");
    }
}

// GLOBAL INSTANCE
const adminsManager = new AdminsManager();

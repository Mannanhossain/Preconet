class ActivityManager {
    constructor() {
        this.activities = [];
    }

    // Load Logs
    async loadActivity() {
        try {
            const response = await auth.makeAuthenticatedRequest('/superadmin/logs?per_page=50');
            const data = await response.json();

            if (response.ok) {
                this.activities = data.logs || [];
                this.renderActivity();
            } else {
                auth.showNotification(data.error || 'Failed to load activity logs', 'error');
            }

        } catch (error) {
            console.error('Error loading activity:', error);
            auth.showNotification('Error loading activity logs', 'error');
        }
    }

    // Convert snake_case role → Human readable
    formatRole(role) {
        if (!role) return "Unknown";
        return role.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }

    // Render All Activity
    renderActivity() {
        const container = document.getElementById('recent-activity');
        const tableBody = document.getElementById('activity-table-body');

        // ==============================
        // RECENT ACTIVITY SECTION
        // ==============================
        if (container) {
            const recent = this.activities.slice(0, 5);

            if (recent.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-6 text-gray-500">
                        <i class="fas fa-history text-3xl mb-2 text-gray-300"></i>
                        <p>No activity yet</p>
                    </div>`;
                return;
            }

            container.innerHTML = recent.map(activity => `
                <div class="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition">
                    <div class="w-9 h-9 rounded-full flex items-center justify-center
                        ${
                            activity.actor_role === "super_admin" ? "bg-purple-100 text-purple-600" :
                            activity.actor_role === "admin" ? "bg-blue-100 text-blue-600" :
                            "bg-green-100 text-green-600"
                        }">

                        <i class="fas fa-${
                            activity.actor_role === "super_admin" ? "user-shield" :
                            activity.actor_role === "admin" ? "user-cog" :
                            "user"
                        } text-sm"></i>
                    </div>

                    <div class="flex-1">
                        <p class="text-sm text-gray-800">${activity.action || "Unknown Action"}</p>
                        <p class="text-xs text-gray-500 mt-1">
                            ${activity.timestamp ? new Date(activity.timestamp).toLocaleString() : "Unknown Time"}
                        </p>
                    </div>
                </div>
            `).join('');
        }

        // ==============================
        // FULL TABLE SECTION
        // ==============================
        if (tableBody) {
            if (this.activities.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-6 text-gray-500">
                            <i class="fas fa-history text-3xl mb-2 text-gray-300"></i>
                            <p>No logs found</p>
                        </td>
                    </tr>`;
                return;
            }

            tableBody.innerHTML = this.activities.map(activity => `
                <tr class="hover:bg-gray-50 transition">
                    <td class="px-4 py-3">
                        <span class="text-sm text-gray-800">${activity.action || "Unknown Action"}</span>
                    </td>

                    <td class="px-4 py-3">
                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                            ${
                                activity.actor_role === "super_admin" ? "bg-purple-100 text-purple-800" :
                                activity.actor_role === "admin" ? "bg-blue-100 text-blue-800" :
                                "bg-green-100 text-green-800"
                            }">
                            ${this.formatRole(activity.actor_role)}
                        </span>
                        <span class="text-xs text-gray-500 ml-2">ID: ${activity.actor_id}</span>
                    </td>

                    <td class="px-4 py-3">
                        <div class="text-sm text-gray-800">${this.formatRole(activity.target_type)}</div>
                        <div class="text-xs text-gray-500">ID: ${activity.target_id || "N/A"}</div>
                    </td>

                    <td class="px-4 py-3">
                        <div class="text-sm">${new Date(activity.timestamp).toLocaleDateString()}</div>
                        <div class="text-xs text-gray-500">${new Date(activity.timestamp).toLocaleTimeString()}</div>
                    </td>
                </tr>
            `).join('');
        }
    }
}

const activityManager = new ActivityManager();

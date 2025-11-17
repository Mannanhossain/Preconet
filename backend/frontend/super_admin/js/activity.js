class ActivityManager {
    constructor() {
        this.activities = [];
    }

    // ---------------------------------------------------------
    // LOAD LOGS
    // ---------------------------------------------------------
    async loadActivity() {
        try {
            const response = await auth.makeAuthenticatedRequest('/api/superadmin/logs?per_page=50');
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

    // ---------------------------------------------------------
    // CLEAN ROLE FORMATTER
    // ---------------------------------------------------------
    formatRole(role) {
        if (!role) return "Unknown";
        return role
            .replace(/_/g, " ")
            .replace(/\b\w/g, (c) => c.toUpperCase());
    }

    // ---------------------------------------------------------
    // ICON BASED ON ACTION
    // ---------------------------------------------------------
    getActionIcon(action = "") {
        action = action.toLowerCase();

        if (action.includes("created")) return "plus-circle";
        if (action.includes("deleted")) return "trash";
        if (action.includes("updated")) return "edit";
        if (action.includes("login")) return "sign-in-alt";
        if (action.includes("sync")) return "sync";
        return "history";
    }

    // ---------------------------------------------------------
    // SAFELY PARSE TIMESTAMP
    // ---------------------------------------------------------
    formatTimestamp(ts) {
        if (!ts) return "Unknown";
        const d = new Date(ts);
        if (isNaN(d.getTime())) return "Unknown";
        return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
    }

    // ---------------------------------------------------------
    // RENDER RECENT ACTIVITY (TOP 5)
    // ---------------------------------------------------------
    renderActivity() {
        const container = document.getElementById('recent-activity');
        const tableBody = document.getElementById('activity-table-body');

        const recent = this.activities.slice(0, 5);

        // ---------------- Recent Activity ----------------
        if (container) {
            if (recent.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-6 text-gray-500">
                        <i class="fas fa-history text-3xl mb-2 text-gray-300"></i>
                        <p>No activity yet</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = recent.map(activity => `
                <div class="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition">

                    <!-- Icon -->
                    <div class="w-9 h-9 rounded-full flex items-center justify-center
                        ${
                            activity.actor_role === "super_admin" ? "bg-purple-100 text-purple-600" :
                            activity.actor_role === "admin" ? "bg-blue-100 text-blue-600" :
                            "bg-green-100 text-green-600"
                        }">
                        <i class="fas fa-${this.getActionIcon(activity.action)} text-sm"></i>
                    </div>

                    <!-- Details -->
                    <div class="flex-1">
                        <p class="text-sm text-gray-800">${activity.action || "Unknown Action"}</p>
                        <p class="text-xs text-gray-500 mt-1">${this.formatTimestamp(activity.timestamp)}</p>
                    </div>

                </div>
            `).join('');
        }

        // ---------------- Full Table ----------------
        if (tableBody) {
            if (this.activities.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-6 text-gray-500">
                            <i class="fas fa-history text-3xl mb-2 text-gray-300"></i>
                            <p>No logs found</p>
                        </td>
                    </tr>
                `;
                return;
            }

            tableBody.innerHTML = this.activities.map(activity => `
                <tr class="hover:bg-gray-50 transition">

                    <td class="px-4 py-3">
                        <span class="text-sm text-gray-800">${activity.action}</span>
                    </td>

                    <td class="px-4 py-3">
                        <span class="px-2 py-1 rounded-full text-xs font-medium
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
                        <div class="text-sm">${this.formatTimestamp(activity.timestamp)}</div>
                    </td>

                </tr>
            `).join('');
        }
    }
}

const activityManager = new ActivityManager();

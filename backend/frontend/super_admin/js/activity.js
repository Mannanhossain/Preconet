/************************************************************
 * ACTIVITY LOG MANAGER – SUPER ADMIN
 ************************************************************/
class ActivityManager {
    constructor() {
        this.activities = [];
    }

    /************************************************************
     * LOAD ACTIVITY LOGS
     ************************************************************/
    async loadActivity() {
        try {
            console.log("DEBUG: Fetching activity logs...");

            const response = await auth.makeAuthenticatedRequest(
                "/api/superadmin/logs"
            );

            const data = await response.json();
            console.log("DEBUG: Activity logs data:", data);

            if (response.ok) {
                this.activities = data.logs || [];
                this.renderActivityTable();
            } else {
                auth.showNotification(data.error || "Failed to load activity logs", "error");
            }
        } catch (error) {
            console.error("ERROR Loading Activity Logs:", error);
            auth.showNotification("Error loading activity logs", "error");
        }
    }

    /************************************************************
     * FORMAT TIMESTAMP
     ************************************************************/
    formatTime(ts) {
        if (!ts) return "Unknown";
        const d = new Date(ts);
        return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
    }

    /************************************************************
     * CLEAN ROLE FORMAT
     ************************************************************/
    formatRole(role) {
        if (!role) return "Unknown";
        return role.replace(/_/g, " ").toUpperCase();
    }

    /************************************************************
     * ICON BASED ON ACTION
     ************************************************************/
    getIcon(action = "") {
        const a = action.toLowerCase();
        if (a.includes("create")) return "plus-circle";
        if (a.includes("delete")) return "trash";
        if (a.includes("update")) return "edit";
        if (a.includes("login")) return "sign-in-alt";
        if (a.includes("logout")) return "sign-out-alt";
        if (a.includes("sync")) return "sync";
        return "history";
    }

    /************************************************************
     * RENDER FULL ACTIVITY TABLE
     ************************************************************/
    renderActivityTable() {
        const tbody = document.getElementById("activity-table-body");
        if (!tbody) return;

        if (this.activities.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="py-10 text-center text-gray-500">
                        <i class="fas fa-history text-4xl mb-3 text-gray-300"></i>
                        <p>No activity logs found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.activities
            .map(log => `
                <tr class="hover:bg-gray-50 transition">

                    <!-- ACTION -->
                    <td class="px-4 py-3">
                        <div class="flex items-center space-x-3">
                            <div class="w-9 h-9 rounded-full flex items-center justify-center
                                ${
                                    log.actor_role === "super_admin"
                                        ? "bg-purple-100 text-purple-600"
                                        : log.actor_role === "admin"
                                        ? "bg-blue-100 text-blue-600"
                                        : "bg-green-100 text-green-600"
                                }">
                                <i class="fas fa-${this.getIcon(log.action)}"></i>
                            </div>
                            <span class="text-sm text-gray-800">${log.action}</span>
                        </div>
                    </td>

                    <!-- ACTOR -->
                    <td class="px-4 py-3">
                        <span class="px-3 py-1 rounded-full text-xs font-medium
                            ${
                                log.actor_role === "super_admin"
                                    ? "bg-purple-100 text-purple-700"
                                    : log.actor_role === "admin"
                                    ? "bg-blue-100 text-blue-700"
                                    : "bg-green-100 text-green-700"
                            }">
                            ${this.formatRole(log.actor_role)}
                        </span>
                        <span class="text-xs text-gray-500 ml-2">ID: ${log.actor_id}</span>
                    </td>

                    <!-- TARGET -->
                    <td class="px-4 py-3">
                        <span class="text-sm text-gray-800">${log.target_type}</span>
                        <p class="text-xs text-gray-500">ID: ${log.target_id ?? "N/A"}</p>
                    </td>

                    <!-- TIME -->
                    <td class="px-4 py-3">
                        <span class="text-sm">${this.formatTime(log.timestamp)}</span>
                    </td>

                </tr>
            `)
            .join("");
    }
}

/************************************************************
 * INIT ACTIVITY MANAGER
 ************************************************************/
const activityManager = new ActivityManager();

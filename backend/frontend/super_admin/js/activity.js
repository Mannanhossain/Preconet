class ActivityManager {
    constructor() {
        this.activities = [];
    }

    async loadActivity() {
        try {
            const response = await auth.makeAuthenticatedRequest('/superadmin/logs?per_page=50');
            const data = await response.json();
            
            if (response.ok) {
                this.activities = data.logs;
                this.renderActivity();
            } else {
                auth.showNotification('Failed to load activity logs', 'error');
            }
        } catch (error) {
            console.error('Error loading activity:', error);
            auth.showNotification('Error loading activity logs', 'error');
        }
    }

    renderActivity() {
        const container = document.getElementById('recent-activity');
        const tableBody = document.getElementById('activity-table-body');
        
        // Render recent activity for dashboard
        if (container) {
            const recentActivities = this.activities.slice(0, 5);
            
            if (recentActivities.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-history text-3xl mb-2 text-gray-300"></i>
                        <p>No activity found</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = recentActivities.map(activity => `
                <div class="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                    <div class="w-8 h-8 rounded-full flex items-center justify-center ${
                        activity.actor_role === 'super_admin' ? 'bg-purple-100 text-purple-600' :
                        activity.actor_role === 'admin' ? 'bg-blue-100 text-blue-600' :
                        'bg-green-100 text-green-600'
                    }">
                        <i class="fas fa-${
                            activity.actor_role === 'super_admin' ? 'user-shield' :
                            activity.actor_role === 'admin' ? 'user-cog' : 'user'
                        } text-xs"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm text-gray-800">${activity.action}</p>
                        <p class="text-xs text-gray-500 mt-1">
                            ${new Date(activity.timestamp).toLocaleString()}
                        </p>
                    </div>
                </div>
            `).join('');
        }

        // Render full activity table for activity section
        if (tableBody) {
            if (this.activities.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="px-4 py-8 text-center text-gray-500">
                            <i class="fas fa-history text-3xl mb-2 text-gray-300"></i>
                            <p>No activity logs found</p>
                        </td>
                    </tr>
                `;
                return;
            }

            tableBody.innerHTML = this.activities.map(activity => `
                <tr class="hover:bg-gray-50 transition-colors">
                    <td class="px-4 py-4">
                        <div class="text-sm text-gray-900">${activity.action}</div>
                    </td>
                    <td class="px-4 py-4">
                        <div class="flex items-center space-x-2">
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                activity.actor_role === 'super_admin' ? 'bg-purple-100 text-purple-800' :
                                activity.actor_role === 'admin' ? 'bg-blue-100 text-blue-800' :
                                'bg-green-100 text-green-800'
                            }">
                                ${activity.actor_role}
                            </span>
                            <span class="text-sm text-gray-500">ID: ${activity.actor_id}</span>
                        </div>
                    </td>
                    <td class="px-4 py-4">
                        <div class="text-sm text-gray-900">${activity.target_type}</div>
                        <div class="text-sm text-gray-500">ID: ${activity.target_id || 'N/A'}</div>
                    </td>
                    <td class="px-4 py-4">
                        <div class="text-sm text-gray-900">${new Date(activity.timestamp).toLocaleDateString()}</div>
                        <div class="text-sm text-gray-500">${new Date(activity.timestamp).toLocaleTimeString()}</div>
                    </td>
                </tr>
            `).join('');
        }
    }
}

const activityManager = new ActivityManager();
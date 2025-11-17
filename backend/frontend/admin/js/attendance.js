class AttendanceManager {
    constructor() {
        this.attendance = [];
    }

    async loadAttendance() {
        try {
            const resp = await auth.makeAuthenticatedRequest(`/api/admin/attendance`);
            const data = await resp.json();

            if (resp.ok) {
                this.attendance = data.attendance;
                this.renderCards();
            } else {
                auth.showNotification("Failed to load attendance", "error");
            }
        } catch (err) {
            console.error(err);
            auth.showNotification("Error loading attendance", "error");
        }
    }

    renderCards() {
        const container = document.getElementById("attendance-cards-container");
        if (!container) return;

        container.innerHTML = "";

        if (!this.attendance.length) {
            container.innerHTML = `
                <p class="text-center text-gray-600 col-span-full p-6 bg-white rounded-xl shadow">
                    No attendance records found.
                </p>
            `;
            return;
        }

        this.attendance.forEach((record) => {

            const statusColor =
                record.status === "Present"
                    ? "bg-green-100 text-green-600"
                    : record.status === "Absent"
                    ? "bg-red-100 text-red-600"
                    : "bg-yellow-100 text-yellow-600";

            const card = `
                <div class="bg-white rounded-xl shadow-md p-6 border hover:shadow-lg transition">
                    <div class="flex items-center justify-between">
                        <h3 class="text-lg font-semibold text-gray-900">${record.user_name}</h3>
                        <span class="px-3 py-1 text-xs rounded-full ${statusColor}">
                            ${record.status}
                        </span>
                    </div>

                    <p class="text-gray-500 text-sm mt-2">📅 ${new Date(record.check_in).toLocaleDateString()}</p>

                    <div class="mt-4 space-y-2">
                        <p class="text-sm"><strong>Check In:</strong> ${
                            record.check_in ? new Date(record.check_in).toLocaleTimeString() : "--"
                        }</p>

                        <p class="text-sm"><strong>Check Out:</strong> ${
                            record.check_out ? new Date(record.check_out).toLocaleTimeString() : "--"
                        }</p>

                        <p class="text-sm"><strong>📍 Location:</strong> ${record.address || "N/A"}</p>
                    </div>
                </div>
            `;

            container.innerHTML += card;
        });
    }
}

window.adminDashboard = window.adminDashboard || {};
window.adminDashboard.attendanceManager = new AttendanceManager();

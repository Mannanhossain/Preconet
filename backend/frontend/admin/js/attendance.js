/* attendance manager */
class AttendanceManager {
  async loadAttendance() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/attendance');
      const data = await resp.json();

      if (!resp.ok) { 
        auth.showNotification(data.error || 'Failed to load attendance', 'error'); 
        return; 
      }

      const items = data.attendance || [];
      const container = document.getElementById('attendance-cards-container');
      if (!container) return;

      if (items.length === 0) {
        container.innerHTML = `
          <div class="text-center text-gray-500 py-8">
            No attendance records found.
          </div>`;
        return;
      }

      // Group by username
      const byUser = {};
      for (const r of items) {
        const username = r.user_name || "Unknown User";
        if (!byUser[username]) byUser[username] = [];
        byUser[username].push(r);
      }

      // Sort each user's records by latest check_in
      for (const name in byUser) {
        byUser[name].sort((a, b) => new Date(b.check_in) - new Date(a.check_in));
      }

      // Build cards
      let html = "";
      for (const name in byUser) {
        const recs = byUser[name];
        const latest = recs[0];

        const status = latest.status?.toLowerCase() === "present" ? "present" : "absent";

        const checkIn = latest.check_in
          ? new Date(latest.check_in).toLocaleString()
          : "N/A";

        const checkOut = latest.check_out
          ? new Date(latest.check_out).toLocaleString()
          : "";

        html += `
          <div class="border p-4 rounded bg-white shadow-sm hover:shadow-md transition shadow">
            <div class="flex justify-between items-start mb-3">
              <div>
                <div class="font-medium text-lg">${name}</div>
                <div class="text-xs text-gray-500">Total records: ${recs.length}</div>
              </div>
              <span class="px-2 py-1 text-xs rounded-full ${
                status === "present"
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              }">
                ${latest.status || "Unknown"}
              </span>
            </div>

            <div class="text-sm text-gray-600 mb-2">
              <strong>Latest:</strong> ${checkIn}
              ${checkOut ? ` — ${checkOut}` : ""}
              ${latest.address ? `<br><i class="fas fa-map-marker-alt"></i> ${latest.address}` : ""}
            </div>

            <div class="mt-3 space-y-1">
        `;

        // Show recent 4 additional entries
        for (let i = 1; i < Math.min(5, recs.length); i++) {
          const a = recs[i];
          html += `
            <div class="text-xs text-gray-600 border-t pt-1 pl-2 border-gray-100">
              ${new Date(a.check_in).toLocaleDateString()} at ${new Date(a.check_in).toLocaleTimeString()} — ${a.status}
            </div>
          `;
        }

        if (recs.length > 5) {
          html += `
            <div class="text-xs text-blue-600 pt-1">
              +${recs.length - 5} more records
            </div>`;
        }

        html += `
            </div>
          </div>
        `;
      }

      container.innerHTML = html;

    } catch (e) {
      console.error(e);
      auth.showNotification("Error loading attendance", "error");
    }
  }
}

const attendanceManager = new AttendanceManager();

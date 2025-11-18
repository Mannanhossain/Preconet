/* admin/js/attendance.js */
class AttendanceManager {
  async loadAttendance(page=1, per_page=25) {
    try {
      const resp = await auth.makeAuthenticatedRequest(`/api/admin/attendance?page=${page}&per_page=${per_page}`);
      if (!resp) return;
      const data = await resp.json();
      if (!resp.ok) {
        auth.showNotification(data.error || 'Failed to load attendance', 'error');
        return;
      }

      const items = data.attendance || [];
      const container = document.getElementById('attendance-cards-container') || document.getElementById('attendance-table-body');
      if (!container) return;

      // If it's table body element name attendance-table-body we render rows, else cards
      if (container.tagName.toLowerCase() === 'tbody') {
        container.innerHTML = items.length ? items.map(a => `
          <tr>
            <td class="p-3">${a.user_name || a.user_id}</td>
            <td class="p-3">${new Date(a.check_in).toLocaleString()}</td>
            <td class="p-3">${a.check_out ? new Date(a.check_out).toLocaleString() : '-'}</td>
            <td class="p-3">${a.status}</td>
          </tr>
        `).join('') : `<tr><td colspan="4" class="p-4 text-center text-gray-500">No records</td></tr>`;
        return;
      }

      container.innerHTML = items.map(a => `
        <div class="bg-white p-4 rounded shadow">
          <div class="flex justify-between">
            <div>
              <div class="font-medium">${a.user_name || a.user_id}</div>
              <div class="text-xs text-gray-500">${new Date(a.check_in).toLocaleString()}</div>
            </div>
            <div class="text-sm">${a.status}</div>
          </div>
        </div>
      `).join('');

    } catch (e) { console.error(e); auth.showNotification('Failed to load attendance', 'error'); }
  }
}

const attendanceManager = new AttendanceManager();

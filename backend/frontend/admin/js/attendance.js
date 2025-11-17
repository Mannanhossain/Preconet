/* attendance manager */
class AttendanceManager {
  async loadAttendance() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/attendance');
      const data = await resp.json();
      if (!resp.ok) { auth.showNotification(data.error||'Failed attendance','error'); return; }
      const items = data.attendance || [];
      const container = document.getElementById('attendanceCards');
      if (!container) return;
      // Group attendance by user_name
      const byUser = {};
      items.forEach(r => {
        (byUser[r.user_name] = byUser[r.user_name]||[]).push(r);
      });
      container.innerHTML = Object.keys(byUser).map(name => {
        const recs = byUser[name];
        const last = recs[0];
        return `
          <div class="border p-4 rounded bg-white">
            <div class="flex justify-between items-start">
              <div>
                <div class="font-medium">${name}</div>
                <div class="text-xs text-gray-500">${recs.length} records</div>
              </div>
              <div class="text-xs text-gray-500">${new Date(last.check_in).toLocaleDateString()}</div>
            </div>
            <div class="mt-3 space-y-2">
              ${recs.slice(0,5).map(a=>`
                <div class="text-xs text-gray-600 border-t pt-2">${new Date(a.check_in).toLocaleString()} — ${a.status} — ${a.address || ''}</div>
              `).join('')}
            </div>
          </div>
        `;
      }).join('');
    } catch(e){ console.error(e); auth.showNotification('Attendance error','error'); }
  }
}

const attendanceManager = new AttendanceManager();

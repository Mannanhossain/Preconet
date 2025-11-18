/* Call History Manager */
class CallHistoryManager {

  async loadCallHistory() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/all-call-history');
      const data = await resp.json();

      if (!resp.ok) {
        auth.showNotification(data.error || "Failed to load call history", "error");
        return;
      }

      const list = data.latest_calls || [];
      const container = document.getElementById("call-history-container");
      if (!container) return;

      container.innerHTML = `
        <table class="w-full bg-white rounded shadow overflow-hidden">
          <thead class="bg-gray-200 text-left">
            <tr>
              <th class="p-3">User</th>
              <th class="p-3">Phone Number</th>
              <th class="p-3">Type</th>
              <th class="p-3">Duration</th>
              <th class="p-3">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            ${this.generateRows(list)}
          </tbody>
        </table>
      `;

    } catch (e) {
      console.error(e);
      auth.showNotification("Error loading call history", "error");
    }
  }

  generateRows(list) {
    if (!list.length) {
      return `<tr><td colspan="5" class="p-3 text-center text-gray-500">No call history found</td></tr>`;
    }

    return list.map(c => `
      <tr class="border-t hover:bg-gray-50">
        <td class="p-3">${c.user_name || 'Unknown'}</td>
        <td class="p-3">${c.formatted_number || c.phone_number || '-'}</td>

        <td class="p-3">
          <span class="px-2 py-1 text-xs rounded ${this.getCallTypeClass(c.type)}">
            ${c.type}
          </span>
        </td>

        <td class="p-3">${c.duration ? c.duration + 's' : '-'}</td>

        <td class="p-3 text-sm text-gray-600">
          ${this.formatDate(c.timestamp || c.created_at)}
        </td>
      </tr>
    `).join('');
  }

  getCallTypeClass(type) {
    const t = (type || "").toLowerCase();
    const map = {
      incoming: "bg-green-100 text-green-800",
      outgoing: "bg-blue-100 text-blue-800",
      missed: "bg-red-100 text-red-800",
      rejected: "bg-yellow-100 text-yellow-800"
    };
    return map[t] || "bg-gray-100 text-gray-800";
  }

  formatDate(ts) {
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return "-";
    }
  }
}

const callHistoryManager = new CallHistoryManager();

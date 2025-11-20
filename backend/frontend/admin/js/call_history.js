/* admin/js/call_history.js */
class CallHistoryManager {

  async loadCalls(user_id = null, page = 1, per_page = 50) {
    try {

      // Choose correct URL
      const url = user_id 
        ? `/api/admin/user-call-history/${user_id}?page=${page}&per_page=${per_page}`
        : `/api/admin/all-call-history?page=${page}&per_page=${per_page}`;

      const resp = await auth.makeAuthenticatedRequest(url);
      if (!resp) return;

      const data = await resp.json();

      if (!resp.ok) {
        auth.showNotification(data.error || 'Failed to load call history', 'error');
        return;
      }

      // main list (supports both admin & individual)
      const list = data.call_history || [];

      const container = document.getElementById("call-history-container");
      if (!container) return;

      container.innerHTML = `
        <table class="w-full bg-white rounded shadow overflow-hidden">
          <thead class="bg-gray-200">
            <tr>
              <th class="p-3">User</th>
              <th class="p-3">Number</th>
              <th class="p-3">Contact Name</th>
              <th class="p-3">Type</th>
              <th class="p-3">Duration</th>
              <th class="p-3">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            ${
              list.length
                ? list.map(r => `
                  <tr class="border-t">
                    <td class="p-3">${r.user_name || r.user_id || '-'}</td>
                    <td class="p-3">${r.phone_number || '-'}</td>
                    <td class="p-3">${r.contact_name || '-'}</td>
                    <td class="p-3">${r.call_type || '-'}</td>
                    <td class="p-3">${r.duration ? r.duration + "s" : "-"}</td>
                    <td class="p-3 text-sm text-gray-600">
                      ${r.timestamp ? new Date(r.timestamp).toLocaleString() : '-'}
                    </td>
                  </tr>
                `).join("")
                : `<tr><td colspan="6" class="p-4 text-center text-gray-500">No call records found</td></tr>`
            }
          </tbody>
        </table>
      `;
    }

    catch (e) {
      console.error(e);
      auth.showNotification("Failed to load call history", "error");
    }
  }
}

const callHistoryManager = new CallHistoryManager();

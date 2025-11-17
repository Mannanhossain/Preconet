/* call history manager */
class CallHistoryManager {
  async loadCalls() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/call-history'); // if you have top-level call-history route
      // If you don't have a top-level route, consider using /api/admin/users -> then fetch per-user
      const data = await resp.json();
      if (!resp.ok) { auth.showNotification(data.error || 'Failed calls','error'); return; }
      const list = data.call_history || [];
      const body = document.getElementById('callHistoryTable');
      if (!body) return;
      body.innerHTML = list.map(c => `
        <tr>
          <td class="p-3">${c.user_name || 'User '+c.user_id}</td>
          <td class="p-3">${c.number}</td>
          <td class="p-3">${c.call_type}</td>
          <td class="p-3">${c.duration ? (c.duration+'s') : '-'}</td>
          <td class="p-3">${new Date(c.timestamp || c.created_at).toLocaleString()}</td>
        </tr>
      `).join('');
    } catch(e){ console.error(e); auth.showNotification('Call history error','error'); }
  }
}

const callHistoryManager = new CallHistoryManager();

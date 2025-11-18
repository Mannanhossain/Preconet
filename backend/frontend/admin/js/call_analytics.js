/* admin/js/call_analytics.js */
class CallAnalyticsManager {
  async loadAnalytics() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/call-analytics');
      if (!resp) return;
      const data = await resp.json();
      if (!resp.ok) { auth.showNotification(data.error || 'Analytics failed', 'error'); return; }
      this.data = data || {};
      this.renderCards();
      this.renderTrend();
      this.renderTable();
    } catch(e) { console.error(e); auth.showNotification('Analytics error', 'error'); }
  }

  renderCards() {
    const container = document.getElementById('call-analytics-cards');
    if (!container) return;
    const d = this.data || {};
    const cards = [
      { label: 'Total Calls', value: d.total_calls || 0, icon: 'phone', color: 'blue' },
      { label: 'Incoming', value: d.incoming || 0, icon: 'phone-volume', color: 'green' },
      { label: 'Outgoing', value: d.outgoing || 0, icon: 'phone', color: 'purple' },
      { label: 'Missed', value: d.missed || 0, icon: 'phone-slash', color: 'red' }
    ];
    container.innerHTML = cards.map(c => `
      <div class="bg-white p-4 rounded shadow">
        <div class="flex justify-between items-center">
          <div><div class="text-xs text-gray-500">${c.label}</div><div class="text-xl font-bold">${c.value}</div></div>
          <div class="w-12 h-12 rounded flex items-center justify-center bg-${c.color}-100 text-${c.color}-600"><i class="fas fa-${c.icon}"></i></div>
        </div>
      </div>
    `).join('');
  }

  renderTrend() {
    const ctx = document.getElementById('call-trend-canvas');
    if (!ctx) return;
    if (typeof Chart === 'undefined') return;
    const trend = (this.data && this.data.daily_series) || { labels: [], values: [] };
    new Chart(ctx, {
      type: 'bar',
      data: { labels: trend.labels, datasets: [{ label: 'Calls', data: trend.values }]},
      options: { responsive:true, maintainAspectRatio:false }
    });
  }

  renderTable() {
    const container = document.getElementById('call-analytics-table-container');
    if (!container) return;
    const rows = (this.data && this.data.user_summary) || [];
    container.innerHTML = `
      <table class="w-full bg-white rounded shadow overflow-hidden">
        <thead class="bg-gray-200 text-left">
          <tr><th class="p-3">User</th><th class="p-3">Incoming</th><th class="p-3">Outgoing</th><th class="p-3">Missed</th><th class="p-3">Total Duration</th></tr>
        </thead>
        <tbody>
          ${rows.length ? rows.map(r => `
            <tr class="border-t">
              <td class="p-3">${r.user_name}</td>
              <td class="p-3">${r.incoming||0}</td>
              <td class="p-3">${r.outgoing||0}</td>
              <td class="p-3">${r.missed||0}</td>
              <td class="p-3">${r.total_duration||'0s'}</td>
            </tr>
          `).join('') : `<tr><td colspan="5" class="p-4 text-center text-gray-500">No data</td></tr>`}
        </tbody>
      </table>
    `;
  }
}

const callAnalyticsManager = new CallAnalyticsManager();

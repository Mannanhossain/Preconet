/* call analytics manager */
class CallAnalyticsManager {
  async loadAnalytics() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/call-analytics'); // implement backend
      const data = await resp.json();
      if (!resp.ok) { auth.showNotification(data.error||'Analytics failed','error'); return; }
      this.data = data;
      this.renderCards();
      this.renderTrend();
      this.renderTable();
    } catch(e){ console.error(e); auth.showNotification('Analytics error','error'); }
  }

  renderCards() {
    const container = document.getElementById('callAnalyticsCards');
    if (!container) return;
    const d = this.data || {};
    const cards = [
      { label: 'Total Calls', value: d.total_calls || 0, icon: 'phone' },
      { label: 'Incoming', value: d.incoming || 0, icon: 'phone-volume' },
      { label: 'Outgoing', value: d.outgoing || 0, icon: 'phone' },
      { label: 'Missed', value: d.missed || 0, icon: 'phone-slash' }
    ];
    container.innerHTML = cards.map(c => `
      <div class="bg-white p-4 rounded shadow">
        <div class="flex justify-between items-center">
          <div>
            <div class="text-xs text-gray-500">${c.label}</div>
            <div class="text-xl font-bold">${c.value}</div>
          </div>
          <div class="text-blue-600"><i class="fas fa-${c.icon}"></i></div>
        </div>
      </div>
    `).join('');
  }

  renderTrend() {
    const ctx = document.getElementById('callTrendCanvas');
    if (!ctx) return;
    const trend = (this.data && this.data.daily_series) || { labels: [], values: [] };
    new Chart(ctx, {
      type: 'bar',
      data: { labels: trend.labels, datasets: [{ label: 'Calls', data: trend.values }] },
      options: { responsive: true }
    });
  }

  renderTable() {
    const body = document.getElementById('callAnalyticsTable');
    if (!body) return;
    const rows = (this.data && this.data.user_summary) || [];
    body.innerHTML = rows.map(r => `
      <tr>
        <td class="p-3">${r.user_name}</td>
        <td class="p-3">${r.incoming}</td>
        <td class="p-3">${r.outgoing}</td>
        <td class="p-3">${r.missed}</td>
        <td class="p-3">${r.total_duration}</td>
      </tr>
    `).join('');
  }
}

const callAnalyticsManager = new CallAnalyticsManager();

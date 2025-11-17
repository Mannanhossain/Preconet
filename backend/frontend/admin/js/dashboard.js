/* dashboard manager */
class DashboardManager {
  async init() {
    // if auth missing, redirect
    const token = auth.getToken();
    if (!token) { window.location.href = "/admin/login.html"; return; }
    await this.loadStats();
    await this.loadRecentSync();
    await this.loadUserLogs();
    this.drawPerformanceChart();
  }

  async loadStats() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/dashboard-stats');
      const data = await resp.json();
      if (!resp.ok) { console.error(data); return; }
      this.stats = data.stats || {};
      this.renderStats();
    } catch (e) { console.error(e); }
  }

  renderStats() {
    const container = document.getElementById('statsCards');
    if (!container) return;
    const s = this.stats;
    const cards = [
      { title: "Total Users", value: s.total_users ?? 0, icon: "users", color: "blue" },
      { title: "Active Users", value: s.active_users ?? 0, icon: "user-check", color:"green" },
      { title: "Users With Sync", value: s.users_with_sync ?? 0, icon: "sync", color:"purple" },
      { title: "Remaining Slots", value: s.remaining_slots ?? 0, icon: "user-plus", color:"orange" }
    ];
    container.innerHTML = cards.map(c => `
      <div class="bg-white p-4 rounded shadow floating">
        <div class="flex justify-between items-center">
          <div>
            <p class="text-sm text-gray-500">${c.title}</p>
            <p class="text-2xl font-bold">${c.value}</p>
          </div>
          <div class="w-12 h-12 rounded flex items-center justify-center bg-${c.color}-100 text-${c.color}-600">
            <i class="fas fa-${c.icon}"></i>
          </div>
        </div>
      </div>
    `).join('');
  }

  async loadRecentSync() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/recent-sync');
      const data = await resp.json();
      if (!resp.ok) return;
      this.recent = data.recent_sync || [];
      const list = document.getElementById('recentSyncList');
      if (!list) return;
      list.innerHTML = this.recent.map(r => `
        <div class="border p-3 rounded">
          <div class="flex justify-between items-start">
            <div>
              <div class="font-medium">${r.name}</div>
              <div class="text-xs text-gray-500">Last: ${r.last_sync ? new Date(r.last_sync).toLocaleString() : 'Never'}</div>
            </div>
            <div class="text-sm text-gray-500">${r.call_records ?? 0} calls</div>
          </div>
        </div>
      `).join('');
    } catch(e){ console.error(e); }
  }

  async loadUserLogs() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/user-logs');
      const data = await resp.json();
      if (!resp.ok) return;
      this.userLogs = data.logs || [];
      const container = document.getElementById('userLogsContainer');
      if (!container) return;
      container.innerHTML = this.userLogs.map(l => `
        <div class="p-4 rounded border bg-white">
          <div class="flex justify-between items-center">
            <div>
              <div class="font-medium">${l.user_name || 'Unknown'}</div>
              <div class="text-xs text-gray-500">${l.action}</div>
            </div>
            <div class="text-xs text-gray-500">${new Date(l.timestamp).toLocaleString()}</div>
          </div>
        </div>
      `).join('');
    } catch(e){ console.error(e); }
  }

  drawPerformanceChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
        datasets: [{ label: 'Avg perf', data: (this.stats && this.stats.performance_trend) || [0,0,0,0,0,0,0], borderColor:'#2563EB', fill:false }]
      },
      options: { responsive:true, tension:0.3 }
    });
  }
}

const dashboard = new DashboardManager();

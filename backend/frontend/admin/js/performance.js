/* performance manager - simple wrapper to render a chart */
class PerformanceManager {
  async loadPerformance() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/performance');
      const data = await resp.json();
      if (!resp.ok) { auth.showNotification(data.error || 'Perf load failed', 'error'); return; }
      const ctx = document.getElementById('performanceBarCanvas');
      if (!ctx) return;
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.labels || [],
          datasets: [{ label: 'Performance', data: data.values || [] }]
        },
        options: { responsive:true }
      });
    } catch(e) { console.error(e); auth.showNotification('Perf error', 'error'); }
  }
}

const performanceManager = new PerformanceManager();

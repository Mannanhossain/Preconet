/* ================================
   CALL ANALYTICS MANAGER (ADMIN)
   ================================ */

class CallAnalyticsManager {
  chartInstance = null; // Prevent multiple Chart.js instances

  async loadAnalytics() {
    try {
      const resp = await auth.makeAuthenticatedRequest('/api/admin/call-analytics');
      const data = await resp.json();

      if (!resp.ok) {
        auth.showNotification(data.error || 'Failed to load analytics', 'error');
        return;
      }

      this.data = data;

      this.renderCards();
      this.renderTrendChart();
      this.renderUserTable();

    } catch (e) {
      console.error(e);
      auth.showNotification('Error loading analytics', 'error');
    }
  }

  /* ==========================================
     RENDER ANALYTICS CARDS
  ========================================== */
  renderCards() {
    const container = document.getElementById('call-analytics-cards');
    if (!container) return;

    const d = this.data;

    const cards = [
      { label: "Total Calls", value: d.total_calls ?? 0, icon: "phone", color: "bg-blue-100 text-blue-700" },
      { label: "Incoming", value: d.incoming ?? 0, icon: "phone-volume", color: "bg-green-100 text-green-700" },
      { label: "Outgoing", value: d.outgoing ?? 0, icon: "arrow-up", color: "bg-purple-100 text-purple-700" },
      { label: "Missed", value: d.missed ?? 0, icon: "phone-slash", color: "bg-red-100 text-red-700" },
      { label: "Rejected", value: d.rejected ?? 0, icon: "ban", color: "bg-yellow-100 text-yellow-700" },
      { label: "Total Duration", value: `${d.total_duration ?? 0}s`, icon: "clock", color: "bg-gray-100 text-gray-700" }
    ];

    container.innerHTML = cards.map(c => `
      <div class="bg-white p-4 rounded shadow-sm flex justify-between items-center">
        <div>
          <div class="text-gray-500 text-sm">${c.label}</div>
          <div class="font-bold text-xl">${c.value}</div>
        </div>
        <div class="w-12 h-12 flex items-center justify-center rounded ${c.color}">
          <i class="fas fa-${c.icon} text-lg"></i>
        </div>
      </div>
    `).join('');
  }

  /* ==========================================
     RENDER TREND CHART
  ========================================== */
  renderTrendChart() {
    const canvas = document.getElementById('call-trend-canvas');
    if (!canvas) return;

    if (typeof Chart === "undefined") {
      console.error("Chart.js missing");
      return;
    }

    const trend = this.data.daily_series || { labels: [], values: [] };

    // Destroy previous chart to avoid duplicates
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }

    this.chartInstance = new Chart(canvas, {
      type: "bar",
      data: {
        labels: trend.labels,
        datasets: [{
          label: "Calls per Day",
          data: trend.values,
          backgroundColor: "#3B82F6",
          borderColor: "#1D4ED8",
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true } },
        plugins: { legend: { display: false } }
      }
    });
  }

  /* ==========================================
     RENDER USER SUMMARY TABLE
  ========================================== */
  renderUserTable() {
    const container = document.getElementById('call-analytics-table-container');
    if (!container) return;

    const rows = this.data.user_summary || [];

    if (!rows.length) {
      container.innerHTML = `
        <div class="p-4 text-center text-gray-500">No analytics data available.</div>
      `;
      return;
    }

    container.innerHTML = `
      <table class="w-full bg-white rounded shadow">
        <thead class="bg-gray-200">
          <tr>
            <th class="p-3 text-left">User</th>
            <th class="p-3 text-left">Incoming</th>
            <th class="p-3 text-left">Outgoing</th>
            <th class="p-3 text-left">Missed</th>
            <th class="p-3 text-left">Total Calls</th>
            <th class="p-3 text-left">Total Duration</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(r => `
            <tr class="border-t hover:bg-gray-50">
              <td class="p-3">${r.user_name}</td>
              <td class="p-3">${r.incoming}</td>
              <td class="p-3">${r.outgoing}</td>
              <td class="p-3">${r.missed}</td>
              <td class="p-3">${r.total_calls}</td>
              <td class="p-3">${r.total_duration}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
}

const callAnalyticsManager = new CallAnalyticsManager();

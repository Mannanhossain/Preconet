/* admin/js/call_analytics.js */
class CallAnalyticsManager {

  constructor() {
    this.chart = null; // prevent chart overlapping
  }

  async loadAnalytics() {
    try {
      const resp = await auth.makeAuthenticatedRequest("/api/admin/call-analytics");
      if (!resp) return;

      const data = await resp.json();
      if (!resp.ok) {
        auth.showNotification(data.error || "Analytics failed", "error");
        return;
      }

      this.data = data;

      this.renderCards();
      this.renderTrend();
      this.renderTable();

    } catch (e) {
      console.error(e);
      auth.showNotification("Analytics error", "error");
    }
  }

  renderCards() {
    const container = document.getElementById("call-analytics-cards");
    if (!container) return;

    const d = this.data || {};

    const cards = [
      { label: "Total Calls", value: d.total_calls || 0, icon: "phone", color: "blue" },
      { label: "Incoming", value: d.incoming || 0, icon: "phone-volume", color: "green" },
      { label: "Outgoing", value: d.outgoing || 0, icon: "phone", color: "purple" },
      { label: "Missed", value: d.missed || 0, icon: "phone-slash", color: "red" }
    ];

    // Tailwind CDN cannot generate dynamic classes → use fixed classes
    const colorMap = {
      blue: "bg-blue-100 text-blue-600",
      green: "bg-green-100 text-green-600",
      purple: "bg-purple-100 text-purple-600",
      red: "bg-red-100 text-red-600"
    };

    container.innerHTML = cards.map(c => `
      <div class="bg-white p-4 rounded-lg shadow card-hover">
        <div class="flex justify-between items-center">
          <div>
            <div class="text-xs text-gray-500">${c.label}</div>
            <div class="text-xl font-bold">${c.value}</div>
          </div>
          <div class="w-12 h-12 rounded flex items-center justify-center ${colorMap[c.color]}">
            <i class="fas fa-${c.icon}"></i>
          </div>
        </div>
      </div>
    `).join("");
  }

  renderTrend() {
    const el = document.getElementById("call-trend-canvas");
    if (!el || typeof Chart === "undefined") return;

    const trend = this.data?.daily_series || { labels: [], values: [] };

    // Prevent duplicate charts
    if (this.chart) this.chart.destroy();

    this.chart = new Chart(el, {
      type: "bar",
      data: {
        labels: trend.labels,
        datasets: [
          {
            label: "Calls",
            data: trend.values,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }

  renderTable() {
    const container = document.getElementById("call-analytics-table-container");
    if (!container) return;

    const rows = this.data?.user_summary || [];

    container.innerHTML = `
      <table class="w-full bg-white rounded shadow">
        <thead class="bg-gray-200 text-left">
          <tr>
            <th class="p-3">User</th>
            <th class="p-3">Incoming</th>
            <th class="p-3">Outgoing</th>
            <th class="p-3">Missed</th>
            <th class="p-3">Total Duration</th>
          </tr>
        </thead>
        <tbody>
          ${
            rows.length
              ? rows.map(r => `
                <tr class="border-t table-row-hover">
                  <td class="p-3">${r.user_name || "-"}</td>
                  <td class="p-3">${r.incoming || 0}</td>
                  <td class="p-3">${r.outgoing || 0}</td>
                  <td class="p-3">${r.missed || 0}</td>
                  <td class="p-3">${r.total_duration || "0s"}</td>
                </tr>
              `).join("")
              : `<tr><td colspan="5" class="p-4 text-center text-gray-500">No data</td></tr>`
          }
        </tbody>
      </table>
    `;
  }
}

const callAnalyticsManager = new CallAnalyticsManager();

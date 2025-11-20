/* admin/js/performance.js */

class PerformanceManager {

  async loadPerformance(rangeType = "today") {
    try {
      const resp = await auth.makeAuthenticatedRequest(`/api/admin/performance?range=${rangeType}`);
      if (!resp) return;
      const data = await resp.json();

      if (!resp.ok) {
        auth.showNotification(data.error || "Failed to load performance", "error");
        return;
      }

      const list = data.results || [];

      // ------- BAR CHART --------
      const ctx = document.getElementById("performanceBarCanvas").getContext("2d");

      if (this.chart) this.chart.destroy();

      this.chart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: list.map(u => u.name),
          datasets: [
            {
              label: "Incoming",
              data: list.map(u => u.incoming),
              borderWidth: 2
            },
            {
              label: "Outgoing",
              data: list.map(u => u.outgoing),
              borderWidth: 2
            },
            {
              label: "Missed",
              data: list.map(u => u.missed),
              borderWidth: 2
            }
          ]
        }
      });

    } catch (e) {
      console.error(e);
      auth.showNotification("Error loading performance", "error");
    }
  }
}

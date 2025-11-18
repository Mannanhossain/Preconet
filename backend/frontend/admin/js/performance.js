/* =============================
   PERFORMANCE CHART MANAGER
   ============================= */
class PerformanceManager {
  async loadPerformance() {
    try {
      const resp = await auth.makeAuthenticatedRequest("/api/admin/performance");
      const data = await resp.json();

      if (!resp.ok) {
        auth.showNotification(data.error || "Failed to load performance analytics", "error");
        return;
      }

      const labels = data.labels || [];
      const values = data.values || [];

      const ctx = document.getElementById("performanceBarCanvas");
      if (!ctx) {
        console.warn("performanceBarCanvas not found in DOM");
        return;
      }

      if (typeof Chart === "undefined") {
        console.error("Chart.js not loaded");
        return;
      }

      new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              label: "Performance Score",
              data: values,
              backgroundColor: "#3B82F6",
              borderColor: "#1D4ED8",
              borderWidth: 1,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });

    } catch (e) {
      console.error("Performance Load Error:", e);
      auth.showNotification("Performance load error", "error");
    }
  }
}

const performanceManager = new PerformanceManager();

class PerformanceManager {
    constructor() {
        this.chart = null;
    }

    // ---------------------------------------------------------
    // LOAD PERFORMANCE DATA
    // ---------------------------------------------------------
    async loadPerformance() {
        try {
            // Correct URL (NO /api prefix here)
            const response = await auth.makeAuthenticatedRequest('/admin/users');
            const data = await response.json();

            if (response.ok && Array.isArray(data.users)) {
                if (data.users.length === 0) {
                    auth.showNotification("No users found to display performance", "info");
                    return;
                }
                this.renderChart(data.users);
            } else {
                auth.showNotification(data.error || 'Failed to load performance data', 'error');
            }

        } catch (error) {
            console.error('Error loading performance:', error);
            auth.showNotification('Error loading performance data', 'error');
        }
    }

    // ---------------------------------------------------------
    // RENDER CHART
    // ---------------------------------------------------------
    renderChart(users) {
        const canvas = document.getElementById('performanceChart');
        if (!canvas) {
            console.warn("Canvas element #performanceChart not found");
            return;
        }

        // Destroy previous chart instance
        if (this.chart) {
            this.chart.destroy();
        }

        // Prepare dataset
        const labels = users.map(u => u.name || "Unnamed");
        const scores = users.map(u => Number(u.performance_score) || 0);

        // Dynamic bar colors
        const barColors = scores.map(score => {
            if (score >= 80) return "rgba(34,197,94,0.8)";   // Green - excellent
            if (score >= 50) return "rgba(234,179,8,0.8)";   // Yellow - average
            return "rgba(239,68,68,0.8)";                    // Red - poor
        });

        // Create chart
        this.chart = new Chart(canvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Performance Score (%)",
                    data: scores,
                    backgroundColor: barColors,
                    borderColor: "rgba(31,41,55,0.9)",
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: ctx => `${ctx.parsed.y}% performance`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { stepSize: 20 },
                        title: {
                            display: true,
                            text: 'Performance Score (%)',
                            font: { size: 13, weight: "bold" }
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Users',
                            font: { size: 13, weight: "bold" }
                        }
                    }
                }
            }
        });
    }
}

// ---------------------------------------------------------
// Initialize when switching to Performance tab
// ---------------------------------------------------------
const performanceManager = new PerformanceManager();

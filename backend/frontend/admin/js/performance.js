class PerformanceManager {
    constructor() {
        this.chart = null;
    }

    // ---------------------------------------------------------
    // LOAD PERFORMANCE DATA
    // ---------------------------------------------------------
    async loadPerformance() {
        try {
            const response = await auth.makeAuthenticatedRequest("/admin/users");
            const data = await response.json();

            if (!response.ok || !Array.isArray(data.users)) {
                auth.showNotification(data.error || "Failed to load performance data", "error");
                return;
            }

            if (data.users.length === 0) {
                auth.showNotification("No users found", "info");
                return;
            }

            // Compute performance summary
            const summary = this.computeSummary(data.users);

            // Render UI
            this.renderSummary(summary);
            this.renderChart(data.users);

        } catch (error) {
            console.error("Performance load error:", error);
            auth.showNotification("Error loading performance data", "error");
        }
    }

    // ---------------------------------------------------------
    // CALCULATE SUMMARY
    // ---------------------------------------------------------
    computeSummary(users) {
        const scores = users.map(u => Number(u.performance_score) || 0);

        const totalUsers = scores.length;
        const average = (scores.reduce((a, b) => a + b, 0) / totalUsers).toFixed(2);

        const best = Math.max(...scores);
        const worst = Math.min(...scores);

        const good = scores.filter(s => s >= 80).length;
        const averageUsers = scores.filter(s => s >= 50 && s < 80).length;
        const poor = scores.filter(s => s < 50).length;

        return {
            totalUsers,
            average,
            best,
            worst,
            good,
            averageUsers,
            poor,
        };
    }

    // ---------------------------------------------------------
    // RENDER PERFORMANCE SUMMARY
    // ---------------------------------------------------------
    renderSummary(summary) {
        const box = document.getElementById("performance-summary");
        if (!box) return;

        box.innerHTML = `
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">

                <div class="p-4 bg-white shadow rounded-lg">
                    <p class="text-sm text-gray-500">Average Performance</p>
                    <p class="text-3xl font-bold text-blue-600">${summary.average}%</p>
                </div>

                <div class="p-4 bg-white shadow rounded-lg">
                    <p class="text-sm text-gray-500">Best Performer</p>
                    <p class="text-3xl font-bold text-green-600">${summary.best}%</p>
                </div>

                <div class="p-4 bg-white shadow rounded-lg">
                    <p class="text-sm text-gray-500">Lowest Performer</p>
                    <p class="text-3xl font-bold text-red-600">${summary.worst}%</p>
                </div>

                <div class="p-4 bg-white shadow rounded-lg">
                    <p class="text-sm text-gray-500">Good (≥80%)</p>
                    <p class="text-xl font-bold text-green-600">${summary.good} users</p>
                </div>

                <div class="p-4 bg-white shadow rounded-lg">
                    <p class="text-sm text-gray-500">Average (50–79%)</p>
                    <p class="text-xl font-bold text-yellow-600">${summary.averageUsers} users</p>
                </div>

                <div class="p-4 bg-white shadow rounded-lg">
                    <p class="text-sm text-gray-500">Poor (<50%)</p>
                    <p class="text-xl font-bold text-red-600">${summary.poor} users</p>
                </div>

            </div>
        `;
    }

    // ---------------------------------------------------------
    // RENDER CHART
    // ---------------------------------------------------------
    renderChart(users) {
        const canvas = document.getElementById("performanceChart");
        if (!canvas) {
            console.warn("Canvas #performanceChart not found");
            return;
        }

        if (this.chart) this.chart.destroy();

        const labels = users.map(u => u.name || "User");
        const scores = users.map(u => Number(u.performance_score) || 0);

        const barColors = scores.map(score => {
            if (score >= 80) return "rgba(34,197,94,0.8)";   // Green
            if (score >= 50) return "rgba(234,179,8,0.8)";   // Yellow
            return "rgba(239,68,68,0.8)";                    // Red
        });

        this.chart = new Chart(canvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Performance (%)",
                    data: scores,
                    backgroundColor: barColors,
                    borderColor: "rgba(31,41,55,0.9)",
                    borderWidth: 2,
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
                            label: ctx => `${ctx.raw}% performance`
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
                            text: "Performance Score (%)",
                            font: { size: 14, weight: "bold" }
                        }
                    },
                    x: {
                        ticks: { autoSkip: false, maxRotation: 60 },
                        title: {
                            display: true,
                            text: "Users",
                            font: { size: 14, weight: "bold" }
                        }
                    }
                }
            }
        });
    }
}

// Initialize manager
const performanceManager = new PerformanceManager();

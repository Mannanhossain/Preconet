class PerformanceManager {
    constructor() {
        this.chart = null;
    }

    // ✅ Load all user performance data
    async loadPerformance() {
        try {
            // ✅ FIXED: Added '/api' prefix
            const response = await auth.makeAuthenticatedRequest('/api/admin/users');
            const data = await response.json();

            if (response.ok && Array.isArray(data.users)) {
                this.renderChart(data.users);
            } else {
                auth.showNotification('Failed to load performance data', 'error');
            }
        } catch (error) {
            console.error('Error loading performance:', error);
            auth.showNotification('Error loading performance data', 'error');
        }
    }

    // ✅ Render Bar Chart with Chart.js
    renderChart(users) {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        // Destroy existing chart before re-rendering
        if (this.chart) {
            this.chart.destroy();
        }

        // Prepare data
        const userNames = users.map(user => user.name || 'Unnamed');
        const performanceScores = users.map(user => user.performance_score || 0);

        // Chart.js bar chart
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: userNames,
                datasets: [{
                    label: 'Performance Score (%)',
                    data: performanceScores,
                    backgroundColor: performanceScores.map(score =>
                        score > 80
                            ? 'rgba(34, 197, 94, 0.8)'   // Green - Excellent
                            : score > 50
                                ? 'rgba(234, 179, 8, 0.8)'  // Yellow - Average
                                : 'rgba(239, 68, 68, 0.8)'  // Red - Poor
                    ),
                    borderColor: 'rgba(31, 41, 55, 0.9)',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            font: { size: 14 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` ${context.parsed.y}% performance`
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
                            font: { size: 14, weight: 'bold' }
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Users',
                            font: { size: 14, weight: 'bold' }
                        }
                    }
                }
            }
        });
    }
}

// ✅ Initialize performance manager
const performanceManager = new PerformanceManager();

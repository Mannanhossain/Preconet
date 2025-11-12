class PerformanceManager {
    constructor() {
        this.chart = null;
    }

    async loadPerformance() {
        try {
            const response = await auth.makeAuthenticatedRequest('/admin/users');
            const data = await response.json();
            
            if (response.ok) {
                this.renderChart(data.users);
            } else {
                auth.showNotification('Failed to load performance data', 'error');
            }
        } catch (error) {
            console.error('Error loading performance:', error);
            auth.showNotification('Error loading performance data', 'error');
        }
    }

    renderChart(users) {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }

        const userNames = users.map(user => user.name);
        const performanceScores = users.map(user => user.performance_score);

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: userNames,
                datasets: [{
                    label: 'Performance Score %',
                    data: performanceScores,
                    backgroundColor: 'rgba(34, 197, 94, 0.6)',
                    borderColor: 'rgba(34, 197, 94, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Performance Score %'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Users'
                        }
                    }
                }
            }
        });
    }
}

const performanceManager = new PerformanceManager();
const adminDashboard = new AdminDashboard();
async function loadPerformance() {
    const res = await fetch("/api/admin/performance", {
        headers: { "Authorization": "Bearer " + token }
    });

    const data = await res.json();

    const labels = data.users.map(u => u.name);
    const scores = data.users.map(u => u.performance_score);

    new Chart(document.getElementById("performanceChart"), {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Performance Score (%)",
                data: scores,
                backgroundColor: "rgba(59,130,246,0.7)"
            }]
        }
    });
}

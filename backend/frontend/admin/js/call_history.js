async function loadCallHistory() {
    const res = await fetch("/api/admin/call-history", {
        headers: { "Authorization": "Bearer " + token }
    });

    const data = await res.json();
    const tbody = document.getElementById("callHistoryTable");
    tbody.innerHTML = "";

    if (!data.records || data.records.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-gray-500">No call history found</td></tr>`;
        return;
    }

    data.records.forEach(c => {
        tbody.innerHTML += `
            <tr>
                <td class="p-3">${c.user_name}</td>
                <td class="p-3">${c.number}</td>
                <td class="p-3">${c.call_type}</td>
                <td class="p-3">${c.duration}s</td>
                <td class="p-3">${new Date(c.timestamp).toLocaleString()}</td>
            </tr>
        `;
    });
}

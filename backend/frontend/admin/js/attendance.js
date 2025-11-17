async function loadAttendance() {
    const res = await fetch("/api/admin/attendance", {
        headers: { "Authorization": "Bearer " + token }
    });

    const data = await res.json();
    const tbody = document.getElementById("attendanceTable");
    tbody.innerHTML = "";

    if (!data.records || data.records.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-gray-500">No attendance found</td></tr>`;
        return;
    }

    data.records.forEach(a => {
        tbody.innerHTML += `
            <tr>
                <td class="p-3">${a.user_name}</td>
                <td class="p-3">${a.check_in}</td>
                <td class="p-3">${a.check_out ?? "-"}</td>
                <td class="p-3">${a.status}</td>
            </tr>
        `;
    });
}

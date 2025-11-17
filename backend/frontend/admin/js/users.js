async function loadUsers() {
    const res = await fetch("/api/admin/users", {
        headers: { "Authorization": "Bearer " + token }
    });

    const data = await res.json();
    const tbody = document.getElementById("usersTable");
    tbody.innerHTML = "";

    if (!data.users || data.users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-gray-500">No users found</td></tr>`;
        return;
    }

    data.users.forEach(u => {
        tbody.innerHTML += `
            <tr class="border-b">
                <td class="p-3">${u.name}</td>
                <td class="p-3">${u.email}</td>
                <td class="p-3">${u.phone ?? "-"}</td>
                <td class="p-3 text-blue-600 cursor-pointer">View</td>
            </tr>
        `;
    });
}

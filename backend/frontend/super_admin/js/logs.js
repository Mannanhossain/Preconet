let currentLogPage = 1;
const logsPerPage = 10;

document.addEventListener("DOMContentLoaded", () => {
    const logFilter = document.getElementById("logFilter");

    if (logFilter) {
        logFilter.addEventListener("change", () => loadLogs(1)); // reset to page 1
    }

    const logsMenuButton = document.querySelector('[data-target="logs-view"]');
    if (logsMenuButton) {
        logsMenuButton.addEventListener("click", () => loadLogs(1));
    }
});

/* -------------------------------------------------------
    LOAD LOGS
------------------------------------------------------- */
async function loadLogs(page = 1) {
    try {
        currentLogPage = page;

        const filter = document.getElementById("logFilter")?.value || "";

        // FIXED URL (Auth adds /api prefix automatically)
        let url = `/super-admin/logs?page=${page}&per_page=${logsPerPage}`;
        if (filter) url += `&actor_role=${filter}`;

        const response = await auth.makeAuthenticatedRequest(url);
        const data = await response.json();

        if (!response.ok) {
            auth.showNotification(data.error || "Failed to load logs", "error");
            return;
        }

        displayLogs(data.logs);
        setupPagination(data.total, data.pages, page);

    } catch (error) {
        console.error("Error loading logs:", error);
        auth.showNotification("Failed to load activity logs", "error");
    }
}

/* -------------------------------------------------------
    DISPLAY LOGS
------------------------------------------------------- */
function displayLogs(logs) {
    const tbody = document.getElementById("logsTableBody");
    if (!tbody) return;

    if (!logs || logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="py-10 text-center text-gray-500">
                    <i class="fas fa-history text-4xl mb-3 text-gray-300"></i>
                    <p>No activity logs found</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = logs
        .map(
            (log) => `
        <tr class="hover:bg-gray-50 transition">
            <td>${new Date(log.timestamp).toLocaleString()}</td>

            <td>
                <span class="px-3 py-1 rounded-full text-xs font-medium ${
                    log.actor_role === "super_admin"
                        ? "bg-purple-100 text-purple-700"
                        : log.actor_role === "admin"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-green-100 text-green-700"
                }">
                    ${log.actor_role.replace("_", " ").toUpperCase()}
                </span>
            </td>

            <td>${log.action}</td>
            <td>${log.target_type}</td>
            <td>${log.target_id || "N/A"}</td>
        </tr>
    `
        )
        .join("");
}

/* -------------------------------------------------------
    PAGINATION
------------------------------------------------------- */
function setupPagination(total, pages, currentPage) {
    const pagination = document.getElementById("logsPagination");
    if (!pagination) return;

    if (pages <= 1) {
        pagination.innerHTML = "";
        return;
    }

    let html = "";

    // Previous button
    if (currentPage > 1) {
        html += `<button onclick="loadLogs(${currentPage - 1})">
                    <i class="fas fa-chevron-left"></i>
                 </button>`;
    }

    // Show limited page numbers (smart pagination)
    const maxButtons = 7;
    let start = Math.max(1, currentPage - 3);
    let end = Math.min(pages, start + maxButtons - 1);

    if (end - start < maxButtons - 1) {
        start = Math.max(1, end - (maxButtons - 1));
    }

    for (let i = start; i <= end; i++) {
        if (i === currentPage) {
            html += `<button class="active">${i}</button>`;
        } else {
            html += `<button onclick="loadLogs(${i})">${i}</button>`;
        }
    }

    // Next button
    if (currentPage < pages) {
        html += `<button onclick="loadLogs(${currentPage + 1})">
                    <i class="fas fa-chevron-right"></i>
                 </button>`;
    }

    pagination.innerHTML = html;
}

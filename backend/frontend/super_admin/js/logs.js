let currentLogPage = 1;
const logsPerPage = 10;

document.addEventListener('DOMContentLoaded', function() {
    const logFilter = document.getElementById('logFilter');
    
    logFilter.addEventListener('change', loadLogs);
    
    document.querySelector('[data-target="logs-view"]').addEventListener('click', function() {
        loadLogs();
    });
});

async function loadLogs(page = 1) {
    try {
        const filter = document.getElementById('logFilter').value;
        let url = `${API_BASE_URL}/superadmin/logs?page=${page}&per_page=${logsPerPage}`;
        
        if (filter) {
            url += `&actor_role=${filter}`;
        }

        const response = await fetch(url, {
            headers: authService.getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to load logs');
        }

        const data = await response.json();
        displayLogs(data.logs);
        setupPagination(data.total, data.pages, page);
        
    } catch (error) {
        console.error('Error loading logs:', error);
        showMessage(document.getElementById('loginMessage'), 'Failed to load activity logs', 'error');
    }
}

function displayLogs(logs) {
    const tbody = document.getElementById('logsTableBody');
    
    if (logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: #7f8c8d;">
                    <i class="fas fa-history" style="font-size: 48px; margin-bottom: 15px; display: block;"></i>
                    No activity logs found.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${new Date(log.timestamp).toLocaleString()}</td>
            <td>
                <span class="status-badge ${
                    log.actor_role === 'super_admin' ? 'status-active' :
                    log.actor_role === 'admin' ? 'status-expired' : 'status-inactive'
                }">
                    ${log.actor_role.replace('_', ' ').toUpperCase()}
                </span>
            </td>
            <td>${log.action}</td>
            <td>${log.target_type}</td>
            <td>${log.target_id || 'N/A'}</td>
        </tr>
    `).join('');
}

function setupPagination(total, pages, currentPage) {
    const pagination = document.getElementById('logsPagination');
    
    if (pages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let paginationHTML = '';
    
    // Previous button
    if (currentPage > 1) {
        paginationHTML += `<button onclick="loadLogs(${currentPage - 1})"><i class="fas fa-chevron-left"></i></button>`;
    }
    
    // Page numbers
    for (let i = 1; i <= pages; i++) {
        if (i === currentPage) {
            paginationHTML += `<button class="active">${i}</button>`;
        } else {
            paginationHTML += `<button onclick="loadLogs(${i})">${i}</button>`;
        }
    }
    
    // Next button
    if (currentPage < pages) {
        paginationHTML += `<button onclick="loadLogs(${currentPage + 1})"><i class="fas fa-chevron-right"></i></button>`;
    }
    
    pagination.innerHTML = paginationHTML;
}
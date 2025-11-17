// ========== AUTH CHECK ==========
const token = sessionStorage.getItem("admin_token");
if (!token) {
    window.location.href = "/admin/login.html";
}

// ========== MENU HANDLING ==========
const sections = {
    dashboard: document.getElementById("sectionDashboard"),
    users: document.getElementById("sectionUsers"),
    createUser: document.getElementById("sectionCreateUser"),
    attendance: document.getElementById("sectionAttendance"),
    callHistory: document.getElementById("sectionCallHistory"),
    performance: document.getElementById("sectionPerformance"),
};

function hideAllSections() {
    Object.values(sections).forEach(sec => sec.classList.add("hidden-section"));
}

function activateMenu(menuId) {
    document.querySelectorAll("aside nav a").forEach(a => a.classList.remove("active-menu"));
    document.getElementById(menuId).classList.add("active-menu");
}

document.getElementById("menuDashboard").onclick = () => {
    hideAllSections();
    sections.dashboard.classList.remove("hidden-section");
    activateMenu("menuDashboard");
    loadDashboardStats();
};

document.getElementById("menuUsers").onclick = () => {
    hideAllSections();
    sections.users.classList.remove("hidden-section");
    activateMenu("menuUsers");
    loadUsers();
};

document.getElementById("menuCreateUser").onclick = () => {
    hideAllSections();
    sections.createUser.classList.remove("hidden-section");
    activateMenu("menuCreateUser");
};

document.getElementById("menuAttendance").onclick = () => {
    hideAllSections();
    sections.attendance.classList.remove("hidden-section");
    activateMenu("menuAttendance");
    loadAttendance();
};

document.getElementById("menuCallHistory").onclick = () => {
    hideAllSections();
    sections.callHistory.classList.remove("hidden-section");
    activateMenu("menuCallHistory");
    loadCallHistory();
};

document.getElementById("menuPerformance").onclick = () => {
    hideAllSections();
    sections.performance.classList.remove("hidden-section");
    activateMenu("menuPerformance");
    loadPerformance();
};

// ========== LOGOUT ==========
document.getElementById("logoutBtn").onclick = () => {
    sessionStorage.clear();
    window.location.href = "/admin/login.html";
};

// Load stats on page start
loadDashboardStats();

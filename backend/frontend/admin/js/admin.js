// =========================
// AUTH CHECK
// =========================
if (!auth.getToken()) {
    window.location.href = "/admin/login.html";
}

// =========================
// SECTIONS
// =========================
const sections = {
    dashboard: document.getElementById("sectionDashboard"),
    users: document.getElementById("sectionUsers"),
    createUser: document.getElementById("sectionCreateUser"),
    attendance: document.getElementById("sectionAttendance"),
    callHistory: document.getElementById("sectionCallHistory"),
    performance: document.getElementById("sectionPerformance"),
};

// Hide all sections
function hideAll() {
    Object.values(sections).forEach(sec => sec.classList.add("hidden"));
}

// Activate menu
function activateMenu(id) {
    document.querySelectorAll("aside nav a")
        .forEach(a => a.classList.remove("active-menu"));
    document.getElementById(id).classList.add("active-menu");
}

// =========================
// MENU BUTTON HANDLERS
// =========================
document.getElementById("menuDashboard").onclick = () => {
    hideAll();
    sections.dashboard.classList.remove("hidden");
    activateMenu("menuDashboard");
    dashboard.loadStats();   // FIXED
};

document.getElementById("menuUsers").onclick = () => {
    hideAll();
    sections.users.classList.remove("hidden");
    activateMenu("menuUsers");
    usersManager.loadUsers();   // FIXED
};

document.getElementById("menuCreateUser").onclick = () => {
    hideAll();
    sections.createUser.classList.remove("hidden");
    activateMenu("menuCreateUser");
};

document.getElementById("menuAttendance").onclick = () => {
    hideAll();
    sections.attendance.classList.remove("hidden");
    activateMenu("menuAttendance");
    attendanceManager.loadAttendance();   // FIXED
};

document.getElementById("menuCallHistory").onclick = () => {
    hideAll();
    sections.callHistory.classList.remove("hidden");
    activateMenu("menuCallHistory");
    callHistoryManager.loadCallHistory();   // FIXED
};

document.getElementById("menuPerformance").onclick = () => {
    hideAll();
    sections.performance.classList.remove("hidden");
    activateMenu("menuPerformance");
    dashboard.renderPerformanceChart();   // FIXED
};

// =========================
// LOGOUT
// =========================
document.getElementById("logoutBtn").onclick = () => {
    auth.logout();   // FIXED
};

// =========================
// AUTO LOAD DASHBOARD
// =========================
dashboard.loadStats();

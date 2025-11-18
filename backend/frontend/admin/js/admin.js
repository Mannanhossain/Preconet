// =========================
// SAFE ELEMENT HELPER
// =========================
function el(id) {
    return document.getElementById(id);
}

// =========================
// AUTH CHECK
// =========================
if (!auth.getToken()) {
    window.location.href = "/admin/login.html";
}

// =========================
// REQUIRED GLOBAL OBJECT CHECK
// =========================
if (!window.dashboard) console.warn("dashboard object missing");
if (!window.usersManager) console.warn("usersManager missing");
if (!window.attendanceManager) console.warn("attendanceManager missing");
if (!window.callHistoryManager) console.warn("callHistoryManager missing");

// =========================
// SECTION REFERENCES
// =========================
const sections = {
    dashboard: el("sectionDashboard"),
    users: el("sectionUsers"),
    createUser: el("sectionCreateUser"),
    attendance: el("sectionAttendance"),
    callHistory: el("sectionCallHistory"),
    performance: el("sectionPerformance"),
};

// Hide all sections
function hideAll() {
    Object.values(sections).forEach(sec => {
        if (sec) sec.classList.add("hidden");
    });
}

// Activate menu item
function activateMenu(id) {
    document.querySelectorAll("aside nav a")
        .forEach(a => a.classList.remove("active-menu"));

    const menu = el(id);
    if (menu) menu.classList.add("active-menu");
}

// =========================
// MENU HANDLERS (SAFE)
// =========================
if (el("menuDashboard")) {
    el("menuDashboard").onclick = () => {
        hideAll();
        sections.dashboard?.classList.remove("hidden");
        activateMenu("menuDashboard");
        dashboard?.loadStats();
    };
}

if (el("menuUsers")) {
    el("menuUsers").onclick = () => {
        hideAll();
        sections.users?.classList.remove("hidden");
        activateMenu("menuUsers");
        usersManager?.loadUsers();
    };
}

if (el("menuCreateUser")) {
    el("menuCreateUser").onclick = () => {
        hideAll();
        sections.createUser?.classList.remove("hidden");
        activateMenu("menuCreateUser");
    };
}

if (el("menuAttendance")) {
    el("menuAttendance").onclick = () => {
        hideAll();
        sections.attendance?.classList.remove("hidden");
        activateMenu("menuAttendance");
        attendanceManager?.loadAttendance();
    };
}

if (el("menuCallHistory")) {
    el("menuCallHistory").onclick = () => {
        hideAll();
        sections.callHistory?.classList.remove("hidden");
        activateMenu("menuCallHistory");
        callHistoryManager?.loadCallHistory();
    };
}

if (el("menuPerformance")) {
    el("menuPerformance").onclick = () => {
        hideAll();
        sections.performance?.classList.remove("hidden");
        activateMenu("menuPerformance");
        dashboard?.renderPerformanceChart();
    };
}

// =========================
// LOGOUT
// =========================
if (el("logoutBtn")) {
    el("logoutBtn").onclick = () => {
        auth.logout();
    };
}

// =========================
// ON PAGE LOAD
// =========================
hideAll();
sections.dashboard?.classList.remove("hidden");
dashboard?.loadStats();
activateMenu("menuDashboard");

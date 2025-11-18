/* admin/js/admin.js */
const dashboard = window.dashboard || new (function(){})();
const usersManager = window.usersManager || new (function(){})();
const attendanceManager = window.attendanceManager || new (function(){})();
const callHistoryManager = window.callHistoryManager || new (function(){})();
const callAnalyticsManager = window.callAnalyticsManager || new (function(){})();
const performanceManager = window.performanceManager || new (function(){})();

// Sidebar toggle for mobile
document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");
    const open = document.getElementById("openSidebar");
    const close = document.getElementById("closeSidebar");

    if (open) open.onclick = () => { sidebar.classList.add("active"); overlay.classList.add("active"); };
    if (close) close.onclick = () => { sidebar.classList.remove("active"); overlay.classList.remove("active"); };
    if (overlay) overlay.onclick = () => { sidebar.classList.remove("active"); overlay.classList.remove("active"); }

    // Expose menu elements as globals used in index.html code
    window.menuDashboard = document.getElementById("menuDashboard");
    window.menuUsers = document.getElementById("menuUsers");
    window.menuCreateUser = document.getElementById("menuCreateUser");
    window.menuAttendance = document.getElementById("menuAttendance");
    window.menuCallHistory = document.getElementById("menuCallHistory");
    window.menuPerformance = document.getElementById("menuPerformance");

    window.sectionDashboard = document.getElementById("sectionDashboard");
    window.sectionUsers = document.getElementById("sectionUsers");
    window.sectionCreateUser = document.getElementById("sectionCreateUser");
    window.sectionAttendance = document.getElementById("sectionAttendance");
    window.sectionCallHistory = document.getElementById("sectionCallHistory");
    window.sectionPerformance = document.getElementById("sectionPerformance");

    window.logoutBtn = document.getElementById("logoutBtn");

    // If managers were created after this script loaded, they will be used by index logic (index.html expects global vars).
});

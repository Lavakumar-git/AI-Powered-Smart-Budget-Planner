(() => {
  const root = document.documentElement;
  const storedTheme = localStorage.getItem("smartbudget-theme");
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebarOverlay");
  const menuButton = document.getElementById("mobileMenuBtn");

  const setTheme = (theme) => {
    root.dataset.theme = theme;
    localStorage.setItem("smartbudget-theme", theme);
    if (themeIcon) {
      themeIcon.className =
        theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
    }
  };

  setTheme(storedTheme || "light");
  themeToggle?.addEventListener("click", () => {
    setTheme(root.dataset.theme === "dark" ? "light" : "dark");
  });

  const closeSidebar = () => {
    sidebar?.classList.remove("open");
    overlay?.classList.remove("visible");
  };

  menuButton?.addEventListener("click", () => {
    sidebar?.classList.toggle("open");
    overlay?.classList.toggle("visible");
  });
  overlay?.addEventListener("click", closeSidebar);
  sidebar
    ?.querySelectorAll("a")
    .forEach((link) => link.addEventListener("click", closeSidebar));
})();

/* EXPENSE BREAKDOWN PIE CHART */

const expenseChart = document.getElementById("expenseBreakdownChart");

if (expenseChart && typeof expenseLabels !== "undefined") {
  const ctx = expenseChart.getContext("2d");

  const colors = [
    "#2563eb",
    "#16a34a",
    "#dc2626",
    "#d97706",
    "#7c3aed",
    "#0891b2",
    "#db2777",
    "#65a30d",
  ];
  const legendDots = document.querySelectorAll(".expense-legend-dot");

  legendDots.forEach(function (dot, index) {
    dot.style.backgroundColor = colors[index % colors.length];
  });

  const values = expenseValues.map(Number);

  const total = values.reduce((sum, value) => sum + value, 0);

  const centerX = 100;
  const centerY = 100;
  const radius = 80;

  let startAngle = -Math.PI / 2;

  values.forEach(function (value, index) {
    const sliceAngle = (value / total) * Math.PI * 2;

    ctx.beginPath();

    ctx.moveTo(centerX, centerY);

    ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);

    ctx.closePath();

    ctx.fillStyle = colors[index % colors.length];

    ctx.fill();

    startAngle += sliceAngle;
  });

  /* Create a white center */

  ctx.beginPath();

  ctx.arc(centerX, centerY, 38, 0, Math.PI * 2);

  ctx.fillStyle = "#ffffff";
  ctx.fill();

  /* Center text */

  ctx.fillStyle = "#111827";
  ctx.font = "bold 15px Arial";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  ctx.fillText("₹" + total.toFixed(0), centerX, centerY);
}

/* PROFILE FORM */

const profileForm = document.getElementById("profileForm");

const profileEditButton = document.getElementById("profileEditButton");

const profileSaveButton = document.getElementById("profileSaveButton");

if (profileForm && profileEditButton && profileSaveButton) {
  const formFields = profileForm.querySelectorAll("input, select, textarea");

  /* INITIAL VIEW MODE */

  formFields.forEach(function (field) {
    field.disabled = true;
  });

  profileEditButton.disabled = false;

  profileSaveButton.disabled = true;
  profileSaveButton.hidden = true;

  /* EDIT BUTTON */

  profileEditButton.addEventListener("click", function () {
    formFields.forEach(function (field) {
      field.disabled = false;
    });

    profileEditButton.disabled = true;
    profileEditButton.hidden = true;

    profileSaveButton.disabled = false;
    profileSaveButton.hidden = false;
  });
}

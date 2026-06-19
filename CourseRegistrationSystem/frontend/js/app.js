/* ===================================================================
   app.js — shared helpers used by every page.
   Provides: session handling, API wrapper, navbar rendering, toasts.
   =================================================================== */

/* ----------------------------- Session ---------------------------- */
const Session = {
  save(token, student) {
    localStorage.setItem("crs_token", token);
    localStorage.setItem("crs_student", JSON.stringify(student));
  },
  token() {
    return localStorage.getItem("crs_token");
  },
  student() {
    const raw = localStorage.getItem("crs_student");
    return raw ? JSON.parse(raw) : null;
  },
  isLoggedIn() {
    return !!this.token();
  },
  isAdmin() {
    const s = this.student();
    return s && s.role === "admin";
  },
  logout() {
    localStorage.removeItem("crs_token");
    localStorage.removeItem("crs_student");
    window.location.href = "login.html";
  },
};

/* ----------------------------- API wrapper ------------------------ */
async function api(path, { method = "GET", body = null, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && Session.token()) {
    headers["Authorization"] = "Bearer " + Session.token();
  }

  let res;
  try {
    res = await fetch(API_BASE + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
    });
  } catch (err) {
    throw new Error(
      "Cannot reach the server. Make sure the backend is running and API_BASE in config.js is correct."
    );
  }

  let data = null;
  const text = await res.text();
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!res.ok) {
    // Session expired -> send back to login.
    if (res.status === 401 && Session.isLoggedIn()) {
      Session.logout();
    }
    const detail = data && data.detail ? data.detail : "Request failed (" + res.status + ").";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

/* ----------------------------- Toast ------------------------------ */
function toast(message, type = "") {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.className = type;
  // force reflow so the transition replays
  void el.offsetWidth;
  el.classList.add("show");
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove("show"), 3000);
}

/* ----------------------------- Navbar ----------------------------- */
function renderNavbar(active) {
  const loggedIn = Session.isLoggedIn();
  const admin = Session.isAdmin();

  const links = [
    { href: "index.html", label: "Home", show: true },
    { href: "about.html", label: "About", show: true },
    { href: "courses.html", label: "Courses", show: true },
    { href: "dashboard.html", label: "Dashboard", show: loggedIn },
    { href: "history.html", label: "History", show: loggedIn },
    { href: "profile.html", label: "Profile", show: loggedIn },
    { href: "admin.html", label: "Admin", show: admin },
  ];

  let items = links
    .filter((l) => l.show)
    .map(
      (l) =>
        `<li><a href="${l.href}" class="${l.href === active ? "active" : ""}">${l.label}</a></li>`
    )
    .join("");

  if (loggedIn) {
    items += `<li><a href="#" id="logoutLink">Logout</a></li>`;
  } else {
    items += `<li><a href="login.html" class="${active === "login.html" ? "active" : ""}">Login</a></li>`;
  }

  const nav = `
    <nav class="navbar">
      <div class="nav-inner">
        <a href="index.html" class="brand">
          <span class="logo">CR</span> Course Registration
        </a>
        <button class="nav-toggle" id="navToggle">&#9776;</button>
        <ul class="nav-links" id="navLinks">${items}</ul>
      </div>
    </nav>`;

  document.body.insertAdjacentHTML("afterbegin", nav);

  document.getElementById("navToggle").addEventListener("click", () => {
    document.getElementById("navLinks").classList.toggle("open");
  });
  const logout = document.getElementById("logoutLink");
  if (logout) {
    logout.addEventListener("click", (e) => {
      e.preventDefault();
      Session.logout();
    });
  }
}

/* ----------------------------- Footer ----------------------------- */
function renderFooter() {
  const footer = `
    <footer class="footer">
      <p>Course Registration System &middot; OSSD Final Project &middot; UMT Lahore</p>
      <p>Built with FastAPI, PostgreSQL &amp; HTML/CSS/JS</p>
    </footer>`;
  document.body.insertAdjacentHTML("beforeend", footer);
}

/* --------------------------- Page guard --------------------------- */
function requireLogin() {
  if (!Session.isLoggedIn()) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}

function requireAdmin() {
  if (!Session.isLoggedIn() || !Session.isAdmin()) {
    toast("Admin access required.", "error");
    setTimeout(() => (window.location.href = "dashboard.html"), 1200);
    return false;
  }
  return true;
}

/* --------------------------- Small utils -------------------------- */
function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}

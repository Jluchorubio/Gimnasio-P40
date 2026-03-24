const authWrapper = document.getElementById("authWrapper");
const toRegister = document.getElementById("toRegister");
const toLogin = document.getElementById("toLogin");
const loginBtn = document.getElementById("loginBtn");
const registerBtn = document.getElementById("registerBtn");
const loginMessage = document.getElementById("loginMessage");
const registerMessage = document.getElementById("registerMessage");

function setToken(token) {
  if (token) {
    localStorage.setItem("auth_token", token);
  } else {
    localStorage.removeItem("auth_token");
  }
}

function showMessage(el, msg) {
  if (!el) return;
  if (msg) {
    el.textContent = msg;
    el.classList.remove("hidden");
  } else {
    el.textContent = "";
    el.classList.add("hidden");
  }
}

function getErrorMessage(data) {
  if (!data) return "Error inesperado. Intenta de nuevo.";
  if (typeof data === "string") return data;
  const keys = Object.keys(data);
  if (!keys.length) return "Error inesperado. Intenta de nuevo.";
  const value = data[keys[0]];
  if (Array.isArray(value)) return value.join(" ");
  return String(value);
}

function redirectByRole(role, miembroId) {
  if (role === "ADMINISTRADOR") {
    window.location.href = "/admin.html";
    return;
  }
  if (role === "ENTRENADOR") {
    if (miembroId) {
      window.location.href = `/trainer.html?trainer_id=${miembroId}`;
      return;
    }
    window.location.href = "/trainer.html";
    return;
  }
  if (role === "CLIENTE") {
    if (miembroId) {
      window.location.href = `/cliente.html?cliente_id=${miembroId}`;
      return;
    }
    window.location.href = "/cliente.html";
    return;
  }
  window.location.href = "/index/";
}

function setMode(mode) {
  if (!authWrapper) return;
  if (mode === "register") {
    authWrapper.classList.add("active");
    showMessage(loginMessage, "");
    return;
  }
  authWrapper.classList.remove("active");
  showMessage(registerMessage, "");
}

if (toRegister) {
  toRegister.addEventListener("click", () => setMode("register"));
}
if (toLogin) {
  toLogin.addEventListener("click", () => setMode("login"));
}

const toggles = document.querySelectorAll("[data-auth]");
toggles.forEach((btn) => {
  btn.addEventListener("click", () => setMode(btn.dataset.auth));
});

if (loginBtn) {
  loginBtn.addEventListener("click", async () => {
    showMessage(loginMessage, "");
    const email = document.getElementById("log-email").value.trim();
    const password = document.getElementById("log-pass").value;

    if (!email || !password) {
      showMessage(loginMessage, "Completa todos los campos.");
      return;
    }

    const res = await fetch("/api/auth/login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json().catch(() => null);
    if (res.ok && data && data.token) {
      setToken(data.token);
      const rol = data?.miembro?.rol;
      const miembroId = data?.miembro?.id;
      redirectByRole(rol, miembroId);
      return;
    }
    showMessage(loginMessage, getErrorMessage(data));
  });
}

if (registerBtn) {
  registerBtn.addEventListener("click", async () => {
    showMessage(registerMessage, "");
    const nombre = document.getElementById("reg-nombre").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-pass").value;
    const password2 = document.getElementById("reg-pass2").value;

    if (!nombre || !email || !password) {
      showMessage(registerMessage, "Completa todos los campos.");
      return;
    }
    if (password !== password2) {
      showMessage(registerMessage, "Las contrasenas no coinciden.");
      return;
    }

    const res = await fetch("/api/auth/registro/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, email, password }),
    });
    const data = await res.json().catch(() => null);
    if (res.ok && data && data.token) {
      setToken(data.token);
      const rol = data?.miembro?.rol;
      const miembroId = data?.miembro?.id;
      redirectByRole(rol, miembroId);
      return;
    }
    showMessage(registerMessage, getErrorMessage(data));
  });
}

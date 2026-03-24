document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("auth_token");
  const btn = document.getElementById("membresia-link");

  if (!btn) return;
  if (!token) {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      window.location.href = "/auth-test/#login";
    });
  }
});

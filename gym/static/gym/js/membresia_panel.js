function toggleSidebar() {
  document.getElementById("sidebar")?.classList.toggle("collapsed");
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".membership-request-form");
  if (!form) return;

  const button = form.querySelector("button[type='submit']");
  form.addEventListener("submit", () => {
    if (!button) return;
    button.disabled = true;
    button.textContent = "Enviando solicitud...";
  });
});

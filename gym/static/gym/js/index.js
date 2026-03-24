function calculateBMI() {
  const weight = parseFloat(document.getElementById("weight").value);
  const height = parseFloat(document.getElementById("height").value) / 100;
  const resultDiv = document.getElementById("bmi-result");
  const valueSpan = document.getElementById("bmi-value");
  const statusP = document.getElementById("bmi-status");

  if (weight > 0 && height > 0) {
    const bmi = (weight / (height * height)).toFixed(1);
    valueSpan.innerText = bmi;
    resultDiv.classList.remove("hidden");

    let status = "";
    if (bmi < 18.5) status = "Bajo peso";
    else if (bmi < 24.9) status = "Peso saludable";
    else if (bmi < 29.9) status = "Sobrepeso";
    else status = "Obesidad";

    statusP.innerText = status;

    resultDiv.style.opacity = 0;
    let op = 0;
    const timer = setInterval(function () {
      if (op >= 1) clearInterval(timer);
      resultDiv.style.opacity = op;
      op += 0.1;
    }, 30);
  }
}

function reveal() {
  const reveals = document.querySelectorAll(".reveal");
  for (let i = 0; i < reveals.length; i++) {
    const windowHeight = window.innerHeight;
    const elementTop = reveals[i].getBoundingClientRect().top;
    const elementVisible = 150;
    if (elementTop < windowHeight - elementVisible) {
      reveals[i].classList.add("active");
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("auth_token");
  const note = document.getElementById("membresia-note");
  const btn = document.getElementById("membresia-link");
  const bmiBtn = document.getElementById("bmiBtn");

  if (!token) {
    if (note) {
      note.textContent = "Para pagar la membresia debes iniciar sesion.";
    }
    if (btn) {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        window.location.href = "/auth-test/#login";
      });
    }
  }

  if (bmiBtn) {
    bmiBtn.addEventListener("click", calculateBMI);
  }

  reveal();
  window.addEventListener("scroll", reveal);
});

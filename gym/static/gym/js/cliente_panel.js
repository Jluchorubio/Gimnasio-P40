let currentCourseId = null;
let currentClassId = null;

function toggleSidebar() {
  document.getElementById("sidebar")?.classList.toggle("collapsed");
}

const viewTitles = {
  courses: "Cursos",
  "my-courses": "Mis Cursos",
  calendar: "Calendario de Entrenamiento",
  profile: "Ajustes de Perfil",
  "course-player": "Reproductor de Entrenamiento",
};

function showView(viewId) {
  document.querySelectorAll(".content-view").forEach((view) => {
    view.classList.remove("active");
  });

  const target = document.getElementById(viewId);
  if (target) {
    target.classList.add("active");
  }

  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.remove("bg-zinc-900/50", "text-white");
    item.classList.add("text-zinc-500");
  });

  const navId = viewId === "course-player" ? "nav-my-courses" : `nav-${viewId}`;
  const activeNav = document.getElementById(navId);
  if (activeNav) {
    activeNav.classList.add("bg-zinc-900/50", "text-white");
    activeNav.classList.remove("text-zinc-500");
  }

  const title = document.getElementById("view-title");
  if (title) {
    title.innerText = viewTitles[viewId] || "Cursos";
  }
}

function activateLesson(lessonEl) {
  if (!lessonEl) return;
  const courseInstance = lessonEl.closest(".course-instance");
  if (!courseInstance) return;

  const classId = lessonEl.dataset.classId;
  currentClassId = classId;

  courseInstance.querySelectorAll(".lesson-item").forEach((item) => {
    item.classList.toggle("active", item === lessonEl);
  });

  courseInstance.querySelectorAll(".class-content").forEach((content) => {
    content.classList.toggle("active", content.dataset.classId === classId);
  });
}

function activateCourse(courseId) {
  if (!courseId) return;
  currentCourseId = String(courseId);

  document.querySelectorAll(".course-instance").forEach((instance) => {
    instance.classList.toggle("active", instance.dataset.courseId === currentCourseId);
  });

  const activeInstance = document.querySelector(
    `.course-instance[data-course-id="${currentCourseId}"]`
  );
  if (activeInstance) {
    const firstLesson = activeInstance.querySelector(".lesson-item");
    if (firstLesson) {
      activateLesson(firstLesson);
    }
    const courseName = activeInstance.dataset.courseName;
    const courseTitle = activeInstance.querySelector(".player-course-name");
    if (courseTitle && courseName) {
      courseTitle.innerText = courseName;
    }
  }
}

function enterCourse(courseId) {
  showView("course-player");
  activateCourse(courseId);
}

function initCoursePlayer() {
  document.querySelectorAll(".lesson-item").forEach((item) => {
    item.addEventListener("click", () => activateLesson(item));
  });
}

function initCalendar() {
  const grid = document.getElementById("calendar-grid");
  if (!grid) return;

  const raw = document.getElementById("calendar-events")?.textContent || "[]";
  let events = [];
  try {
    events = JSON.parse(raw);
  } catch (err) {
    events = [];
  }

  const eventsByDate = {};
  events.forEach((event) => {
    if (!event.date) return;
    if (!eventsByDate[event.date]) {
      eventsByDate[event.date] = [];
    }
    eventsByDate[event.date].push(event);
  });

  const monthNames = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
  ];

  let currentDate = new Date();
  let currentMonth = currentDate.getMonth();
  let currentYear = currentDate.getFullYear();

  const label = document.getElementById("calendar-month-label");

  const renderCalendar = () => {
    grid.innerHTML = "";
    const firstDay = new Date(currentYear, currentMonth, 1);
    const startDay = firstDay.getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    if (label) {
      label.innerText = `${monthNames[currentMonth]} ${currentYear}`;
    }

    for (let i = 0; i < startDay; i += 1) {
      const empty = document.createElement("div");
      empty.className = "calendar-day empty";
      grid.appendChild(empty);
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      const dateKey = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      const dayEvents = eventsByDate[dateKey] || [];

      const cell = document.createElement("div");
      cell.className = `calendar-day${dayEvents.length ? " active-workout" : ""}`;

      const number = document.createElement("span");
      number.className = dayEvents.length
        ? "text-white font-bold"
        : "text-zinc-600";
      number.innerText = day;
      cell.appendChild(number);

      if (dayEvents.length) {
        const labelEl = document.createElement("span");
        labelEl.className = "text-[8px] uppercase font-bold text-red-500";
        labelEl.innerText =
          dayEvents.length === 1
            ? dayEvents[0].label
            : `${dayEvents.length} clases`;
        cell.appendChild(labelEl);
      }

      grid.appendChild(cell);
    }
  };

  document.getElementById("calendar-prev")?.addEventListener("click", () => {
    currentMonth -= 1;
    if (currentMonth < 0) {
      currentMonth = 11;
      currentYear -= 1;
    }
    renderCalendar();
  });

  document.getElementById("calendar-next")?.addEventListener("click", () => {
    currentMonth += 1;
    if (currentMonth > 11) {
      currentMonth = 0;
      currentYear += 1;
    }
    renderCalendar();
  });

  renderCalendar();
}

function initProgressBars() {
  document.querySelectorAll("[data-progress]").forEach((bar) => {
    const raw = parseFloat(bar.dataset.progress || "0");
    if (Number.isNaN(raw)) return;
    const value = Math.min(Math.max(raw, 0), 100);
    bar.style.width = `${value}%`;
  });
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
}

function updateCommentsCount(classId, delta) {
  const counter = document.querySelector(`[data-comments-count="${classId}"]`);
  if (!counter) return;
  const current = parseInt(counter.textContent, 10) || 0;
  const next = Math.max(0, current + delta);
  counter.textContent = `${next} comentarios`;
}

function initComments() {
  const csrfToken = getCookie("csrftoken");

  document.querySelectorAll(".comment-form").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const response = await fetch(form.action || window.location.href, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      });
      if (!response.ok) return;
      const data = await response.json();
      if (!data.ok) return;

      const classId = data.class_id;
      const list = document.querySelector(`[data-comments-list="${classId}"]`);
      if (!list) return;

      const empty = list.querySelector(`[data-comments-empty="${classId}"]`);
      if (empty) empty.remove();

      const card = document.createElement("div");
      card.className = "bg-zinc-900/20 p-6 rounded-2xl border border-zinc-900 flex gap-5";
      card.dataset.commentId = data.comment.id;

      const avatar = document.createElement("div");
      avatar.className =
        "w-10 h-10 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-bold text-white";
      avatar.textContent = data.comment.initials || "";

      const body = document.createElement("div");
      body.className = "flex-grow";

      const header = document.createElement("div");
      header.className = "flex justify-between items-center mb-2";

      const name = document.createElement("span");
      name.className = "text-xs font-bold text-zinc-300 uppercase";
      name.textContent = data.comment.author;

      const meta = document.createElement("div");
      meta.className = "flex items-center gap-3";

      const date = document.createElement("span");
      date.className = "text-[9px] text-zinc-600 uppercase font-bold tracking-widest";
      date.textContent = data.comment.date;

      const del = document.createElement("button");
      del.type = "button";
      del.className =
        "comment-delete text-[9px] font-bold text-zinc-600 uppercase hover:text-red-500 transition";
      del.dataset.commentId = data.comment.id;
      del.textContent = "Eliminar";

      const text = document.createElement("p");
      text.className = "text-sm text-zinc-500 leading-relaxed italic";
      text.textContent = `"${data.comment.content}"`;

      meta.appendChild(date);
      meta.appendChild(del);
      header.appendChild(name);
      header.appendChild(meta);
      body.appendChild(header);
      body.appendChild(text);
      card.appendChild(avatar);
      card.appendChild(body);

      list.prepend(card);
      updateCommentsCount(classId, 1);
      form.reset();
    });
  });

  document.addEventListener("click", async (event) => {
    const btn = event.target.closest(".comment-delete");
    if (!btn) return;

    const commentId = btn.dataset.commentId;
    const classContent = btn.closest(".class-content");
    const classId = classContent?.dataset.classId;

    const formData = new FormData();
    formData.append("action", "delete_comment");
    formData.append("comment_id", commentId);

    const response = await fetch(window.location.href, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrfToken,
      },
      body: formData,
    });

    if (!response.ok) return;
    const data = await response.json();
    if (!data.ok) return;

    const card = document.querySelector(`[data-comment-id="${commentId}"]`);
    if (card) card.remove();

    if (classId) {
      updateCommentsCount(classId, -1);
      const list = document.querySelector(`[data-comments-list="${classId}"]`);
      if (list && !list.querySelector("[data-comment-id]")) {
        const empty = document.createElement("p");
        empty.className = "text-[10px] text-zinc-600 italic";
        empty.dataset.commentsEmpty = classId;
        empty.textContent = "No hay comentarios aun.";
        list.appendChild(empty);
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initCoursePlayer();
  initCalendar();
  initComments();
  initProgressBars();

  const params = new URLSearchParams(window.location.search);
  const courseId = params.get("curso_id");
  if (courseId) {
    enterCourse(courseId);
    const classId = params.get("clase_id");
    if (classId) {
      const lesson = document.querySelector(`.lesson-item[data-class-id="${classId}"]`);
      if (lesson) {
        activateLesson(lesson);
      }
    }
  } else {
    const view = params.get("view");
    if (view && ["courses", "my-courses", "calendar", "profile"].includes(view)) {
      showView(view);
    } else {
      showView("courses");
    }
  }
});

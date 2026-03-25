function toggleSidebar() {
  document.getElementById("sidebar")?.classList.toggle("collapsed");
}

function toggleCoursesDropdown() {
  document.getElementById("course-dropdown")?.classList.toggle("active");
  document.getElementById("arrow-icon")?.classList.toggle("rotate-180");
}

function showView(viewId) {
  document.querySelectorAll(".content-view").forEach((v) => v.classList.remove("active"));
  const view = document.getElementById(viewId);
  if (view) {
    view.classList.add("active");
  }
  const title = document.getElementById("page-title");
  if (title) {
    title.innerText = viewId === "dashboard-view" ? "Panel del Profesor" : "Gestión de Contenido";
  }
}

let currentCourseId = null;
let currentClassId = null;

function openCourse(courseId, courseName) {
  currentCourseId = String(courseId);
  showView("course-view");
  const title = document.getElementById("page-title");
  if (title) {
    title.innerText = courseName || "Curso";
  }

  document.querySelectorAll(".course-instance").forEach((instance) => {
    instance.classList.toggle("active", instance.dataset.courseId === String(courseId));
  });

  const activeInstance = document.querySelector(`.course-instance[data-course-id="${courseId}"]`);
  if (activeInstance) {
    const firstLesson = activeInstance.querySelector(".lesson-item");
    if (firstLesson) {
      activateLesson(firstLesson);
    }
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

function openAttendanceModal(classId) {
  const modal = document.getElementById("attendance-modal");
  if (!modal) return;
  const input = document.getElementById("attendance_class_id");
  if (input) input.value = classId;

  modal.classList.add("active");
  modal.querySelectorAll(".attendance-table").forEach((table) => {
    table.classList.toggle("active", table.dataset.classId === String(classId));
  });
}

function filterAttendance(input) {
  const table = input.closest(".attendance-table");
  if (!table) return;
  const term = input.value.toLowerCase().trim();
  table.querySelectorAll("tbody tr").forEach((row) => {
    const name = row.dataset.name || "";
    const email = row.dataset.email || "";
    const match = name.includes(term) || email.includes(term);
    row.style.display = match ? "" : "none";
  });
}

function closeAttendanceModal() {
  document.getElementById("attendance-modal")?.classList.remove("active");
}

function openEditModal(classId) {
  const modal = document.getElementById("edit-class-modal");
  if (!modal) return;
  const lesson = document.querySelector(`.lesson-item[data-class-id="${classId}"]`);
  if (!lesson) return;

  modal.classList.add("active");
  document.getElementById("edit_class_id").value = classId;
  document.getElementById("edit_nombre").value = lesson.dataset.name || "";
  document.getElementById("edit_descripcion").value = lesson.dataset.desc || "";
  document.getElementById("edit_fecha").value = lesson.dataset.fecha || "";
  document.getElementById("edit_hora").value = lesson.dataset.hora || "";
  document.getElementById("edit_cupo").value = lesson.dataset.cupo || "";
}

function closeEditModal() {
  document.getElementById("edit-class-modal")?.classList.remove("active");
}

function openCreateClassModal(courseId) {
  const modal = document.getElementById("create-class-modal");
  if (!modal) return;
  modal.classList.add("active");
  document.getElementById("create_course_id").value = courseId || currentCourseId || "";
  document.getElementById("create_nombre").value = "";
  document.getElementById("create_descripcion").value = "";
  document.getElementById("create_fecha").value = "";
  document.getElementById("create_hora").value = "";
  document.getElementById("create_cupo").value = "";
}

function closeCreateClassModal() {
  document.getElementById("create-class-modal")?.classList.remove("active");
}

function getPublicationForm(scopeEl) {
  const classContent = scopeEl?.closest(".class-content") || document.querySelector(".class-content.active");
  if (!classContent) return null;
  return classContent.querySelector(".publication-form");
}

function setPublicationFormState(form, data) {
  if (!form) return;
  const actionInput = form.querySelector(".publication-action");
  const idInput = form.querySelector(".publication-id");
  const titleInput = form.querySelector('input[name="titulo"]');
  const contentInput = form.querySelector('textarea[name="contenido"]');
  const videoInput = form.querySelector('input[name="video_url"]');

  if (actionInput) actionInput.value = data.action || "create_publication";
  if (idInput) idInput.value = data.id || "";
  if (titleInput) titleInput.value = data.title || "";
  if (contentInput) contentInput.value = data.content || "";
  if (videoInput) videoInput.value = data.video || "";

  if (data.clearFiles) {
    form.querySelectorAll('input[type="file"]').forEach((input) => {
      input.value = "";
    });
  }

  const card = form.closest("[data-form-card]");
  const titleEl = card?.querySelector("[data-form-title]");
  if (titleEl) {
    titleEl.textContent =
      data.action === "edit_publication" ? "Editar publicacion" : "Crear nueva publicacion";
  }
  if (card) {
    card.classList.toggle("is-editing", data.action === "edit_publication");
  }
}

function resetPublicationForm(btn) {
  const form = btn?.closest(".publication-form");
  if (!form) return;
  setPublicationFormState(form, { action: "create_publication", clearFiles: true });
}

function editPublicationInline(btn) {
  const form = getPublicationForm(btn);
  if (!form) return;
  setPublicationFormState(form, {
    action: "edit_publication",
    id: btn.dataset.id,
    title: btn.dataset.title,
    content: btn.dataset.content,
    video: btn.dataset.video,
  });
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openPublicationModal(classId) {
  const classContent = classId
    ? document.querySelector(`.class-content[data-class-id="${classId}"]`)
    : document.querySelector(".class-content.active");
  const form = classContent?.querySelector(".publication-form");
  if (!form) return;
  setPublicationFormState(form, { action: "create_publication", clearFiles: true });
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function closePublicationModal() {
  return;
}

function openEditPublicationModal(btn) {
  editPublicationInline(btn);
}

function openEditCurrentClass() {
  if (currentClassId) {
    openEditModal(currentClassId);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".lesson-item").forEach((item) => {
    item.addEventListener("click", () => activateLesson(item));
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const courseId = params.get("curso_id");
  const classId = params.get("clase_id");
  if (courseId) {
    const courseName = document.querySelector(`.course-card[data-course-id="${courseId}"]`)?.dataset.courseName;
    openCourse(courseId, courseName);
    if (classId) {
      const lesson = document.querySelector(`.lesson-item[data-class-id="${classId}"]`);
      if (lesson) {
        activateLesson(lesson);
      }
    }
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const courseButtons = document.querySelectorAll("[data-course-target]");
  const courseViews = document.querySelectorAll(".course-view");

  if (!courseButtons.length || !courseViews.length) {
    return;
  }

  const activateCourse = (courseId) => {
    courseButtons.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.courseTarget === courseId);
    });
    courseViews.forEach((view) => {
      view.classList.toggle("active", view.dataset.course === courseId);
    });
  };

  courseButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      activateCourse(btn.dataset.courseTarget);
    });
  });

  activateCourse(courseButtons[0].dataset.courseTarget);
});

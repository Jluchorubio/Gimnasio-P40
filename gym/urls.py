from django.urls import path
from django.views.generic import RedirectView

from gym import views
from gym import admin_views
from gym import trainer_views
from gym import client_views

urlpatterns = [
    path("", RedirectView.as_view(url="/index/", permanent=False), name="root"),
    path("auth-test/", views.auth_test, name="auth_test"),
    path("index/", views.index, name="index"),
    path("roles/", views.roles, name="roles"),
    path("membresia/", views.membresia, name="membresia"),
    path("admin-home/", views.admin_home, name="admin_home"),
    path("admin.html", views.admin_home, name="admin_home_html"),
    path("panel/cursos/", admin_views.admin_courses, name="admin_courses"),
    path("panel/cursos/<int:curso_id>/", admin_views.admin_course_detail, name="admin_course_detail"),
    path("trainer.html", trainer_views.trainer_dashboard, name="trainer_home_html"),
    path("cliente.html", client_views.cliente_dashboard, name="cliente_home_html"),
    path("panel/<str:model_key>/", admin_views.admin_list, name="admin_list"),
    path("panel/<str:model_key>/crear/", admin_views.admin_create, name="admin_create"),
    path(
        "panel/<str:model_key>/<int:pk>/editar/",
        admin_views.admin_edit,
        name="admin_edit",
    ),
    path(
        "panel/<str:model_key>/<int:pk>/eliminar/",
        admin_views.admin_delete,
        name="admin_delete",
    ),
    path("trainer/seleccionar/", trainer_views.trainer_select, name="trainer_select"),
    path("trainer/cursos/", trainer_views.trainer_courses_list, name="trainer_courses_list"),
    path("trainer/cursos/crear/", trainer_views.trainer_course_create, name="trainer_course_create"),
    path(
        "trainer/cursos/<int:curso_id>/",
        trainer_views.trainer_course_detail,
        name="trainer_course_detail",
    ),
    path(
        "trainer/cursos/<int:curso_id>/editar/",
        trainer_views.trainer_course_edit,
        name="trainer_course_edit",
    ),
    path(
        "trainer/asistencia/",
        trainer_views.trainer_attendance_overview,
        name="trainer_attendance_overview",
    ),
    path("trainer/clases/", trainer_views.trainer_clases_list, name="trainer_clases_list"),
    path(
        "trainer/clases/crear/",
        trainer_views.trainer_clase_create,
        name="trainer_clase_create",
    ),
    path(
        "trainer/clases/<int:pk>/editar/",
        trainer_views.trainer_clase_edit,
        name="trainer_clase_edit",
    ),
    path(
        "trainer/clases/<int:pk>/eliminar/",
        trainer_views.trainer_clase_delete,
        name="trainer_clase_delete",
    ),
    path(
        "trainer/clases/<int:pk>/inscritos/",
        trainer_views.trainer_inscritos,
        name="trainer_inscritos",
    ),
    path(
        "trainer/clases/<int:pk>/publicaciones/",
        trainer_views.trainer_publicaciones_list,
        name="trainer_publicaciones_list",
    ),
    path(
        "trainer/clases/<int:pk>/publicaciones/crear/",
        trainer_views.trainer_publicacion_create,
        name="trainer_publicacion_create",
    ),
    path(
        "trainer/publicaciones/<int:pk>/editar/",
        trainer_views.trainer_publicacion_edit,
        name="trainer_publicacion_edit",
    ),
    path(
        "trainer/publicaciones/<int:pk>/eliminar/",
        trainer_views.trainer_publicacion_delete,
        name="trainer_publicacion_delete",
    ),
    path("cliente/seleccionar/", client_views.cliente_select, name="cliente_select"),
    path("cliente/membresia/", client_views.cliente_membresia, name="cliente_membresia"),
    path("cliente/clases/", client_views.cliente_clases_list, name="cliente_clases_list"),
    path("cliente/mis-clases/", client_views.cliente_mis_clases, name="cliente_mis_clases"),
    path(
        "cliente/clases/<int:pk>/publicaciones/",
        client_views.cliente_publicaciones_list,
        name="cliente_publicaciones_list",
    ),
]

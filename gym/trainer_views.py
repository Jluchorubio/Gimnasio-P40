from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Count
from django.contrib import messages

from gym.models import Miembro, Curso, Clase, Asistencia, PublicacionClase


class CursoTrainerForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["nombre", "descripcion", "activo"]

    def __init__(self, *args, profesor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._profesor = profesor

    def save(self, commit=True):
        curso = super().save(commit=False)
        if self._profesor:
            curso.profesor = self._profesor
        if commit:
            curso.save()
        return curso


class ClaseTrainerForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = ["nombre", "descripcion", "fecha", "hora", "cupo_maximo"]

    def __init__(self, *args, instructor=None, curso=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._instructor = instructor
        self._curso = curso

    def save(self, commit=True):
        clase = super().save(commit=False)
        if self._instructor:
            clase.instructor = self._instructor
        if self._curso:
            clase.curso = self._curso
        if commit:
            clase.save()
        return clase


class PublicacionTrainerForm(forms.ModelForm):
    class Meta:
        model = PublicacionClase
        fields = ["titulo", "contenido", "imagen", "video_archivo", "video_url"]


def _get_trainer(request):
    trainer_id = request.GET.get("trainer_id")
    if trainer_id:
        try:
            request.session["trainer_id"] = int(trainer_id)
        except ValueError:
            pass

    trainer_id = request.session.get("trainer_id")
    if not trainer_id:
        return None

    trainer = Miembro.objects.filter(
        pk=trainer_id, rol__nombre="ENTRENADOR"
    ).first()
    if not trainer:
        request.session.pop("trainer_id", None)
        return None
    return trainer


def _require_trainer(request):
    trainer = _get_trainer(request)
    if not trainer:
        return None, redirect(reverse("trainer_select"))
    return trainer, None


def trainer_select(request):
    trainers = Miembro.objects.filter(rol__nombre="ENTRENADOR").order_by("nombre")

    if request.method == "POST":
        trainer_id = request.POST.get("trainer_id")
        trainer = trainers.filter(pk=trainer_id).first()
        if not trainer:
            messages.error(request, "Selecciona un entrenador válido.")
        else:
            request.session["trainer_id"] = trainer.id
            return redirect(reverse("trainer_home_html"))

    return render(request, "gym/trainer/select.html", {"trainers": trainers})


def trainer_dashboard(request):
    return redirect(reverse("trainer_courses_list"))


def trainer_courses_list(request):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    cursos = (
        Curso.objects.filter(profesor=trainer)
        .annotate(total_clases=Count("clases"))
        .order_by("nombre")
    )
    return render(
        request,
        "gym/trainer/courses_list.html",
        {"trainer": trainer, "cursos": cursos},
    )


def trainer_course_create(request):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        form = CursoTrainerForm(request.POST, profesor=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso creado correctamente.")
            return redirect(reverse("trainer_courses_list"))
    else:
        form = CursoTrainerForm(profesor=trainer)

    return render(
        request,
        "gym/trainer/course_form.html",
        {"trainer": trainer, "form": form, "action": "Crear"},
    )


def trainer_course_edit(request, curso_id):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    curso = get_object_or_404(Curso, pk=curso_id, profesor=trainer)

    if request.method == "POST":
        form = CursoTrainerForm(request.POST, instance=curso, profesor=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso actualizado correctamente.")
            return redirect(reverse("trainer_course_detail", kwargs={"curso_id": curso.id}))
    else:
        form = CursoTrainerForm(instance=curso, profesor=trainer)

    return render(
        request,
        "gym/trainer/course_form.html",
        {"trainer": trainer, "form": form, "action": "Editar", "curso": curso},
    )


def trainer_course_detail(request, curso_id):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    curso = get_object_or_404(Curso, pk=curso_id, profesor=trainer)
    clases = (
        Clase.objects.filter(curso=curso, instructor=trainer)
        .annotate(total_inscritos=Count("asistencia"))
        .prefetch_related("publicaciones__comentarios", "asistencia_set__miembro")
        .order_by("fecha", "hora")
    )

    for clase in clases:
        clase.total_comentarios = sum(
            len(pub.comentarios.all()) for pub in clase.publicaciones.all()
        )

    return render(
        request,
        "gym/trainer/course_detail.html",
        {
            "trainer": trainer,
            "curso": curso,
            "clases": clases,
            "clases_count": clases.count(),
        },
    )


def trainer_attendance_overview(request):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clases = (
        Clase.objects.filter(instructor=trainer)
        .select_related("curso")
        .order_by("-fecha", "-hora")
    )
    return render(
        request,
        "gym/trainer/attendance_overview.html",
        {"trainer": trainer, "clases": clases},
    )


def trainer_clases_list(request):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clases = (
        Clase.objects.filter(instructor=trainer)
        .select_related("curso")
        .order_by("fecha", "hora")
    )
    return render(
        request,
        "gym/trainer/clases_list.html",
        {"trainer": trainer, "clases": clases},
    )


def trainer_clase_create(request):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    curso = None
    curso_id = request.GET.get("curso")
    if curso_id:
        curso = Curso.objects.filter(pk=curso_id, profesor=trainer).first()
        if not curso:
            messages.error(request, "No tienes permiso para ese curso.")
            return redirect(reverse("trainer_courses_list"))

    if request.method == "POST":
        form = ClaseTrainerForm(request.POST, instructor=trainer, curso=curso)
        if form.is_valid():
            form.save()
            messages.success(request, "Clase creada correctamente.")
            if curso:
                return redirect(reverse("trainer_course_detail", kwargs={"curso_id": curso.id}))
            return redirect(reverse("trainer_clases_list"))
    else:
        form = ClaseTrainerForm(instructor=trainer, curso=curso)

    return render(
        request,
        "gym/trainer/clase_form.html",
        {"trainer": trainer, "form": form, "action": "Crear", "curso": curso},
    )


def trainer_clase_edit(request, pk):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clase = get_object_or_404(Clase, pk=pk, instructor=trainer)
    curso = clase.curso

    if request.method == "POST":
        form = ClaseTrainerForm(
            request.POST, instance=clase, instructor=trainer, curso=curso
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Clase actualizada correctamente.")
            if curso:
                return redirect(
                    reverse("trainer_course_detail", kwargs={"curso_id": curso.id})
                )
            return redirect(reverse("trainer_clases_list"))
    else:
        form = ClaseTrainerForm(instance=clase, instructor=trainer, curso=curso)

    return render(
        request,
        "gym/trainer/clase_form.html",
        {"trainer": trainer, "form": form, "action": "Editar", "curso": curso},
    )


def trainer_clase_delete(request, pk):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clase = get_object_or_404(Clase, pk=pk, instructor=trainer)
    curso = clase.curso

    if request.method == "POST":
        clase.delete()
        messages.success(request, "Clase eliminada correctamente.")
        if curso:
            return redirect(
                reverse("trainer_course_detail", kwargs={"curso_id": curso.id})
            )
        return redirect(reverse("trainer_clases_list"))

    return render(
        request,
        "gym/trainer/clase_delete.html",
        {"trainer": trainer, "clase": clase, "curso": curso},
    )


def trainer_inscritos(request, pk):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clase = get_object_or_404(Clase, pk=pk, instructor=trainer)
    inscritos = Asistencia.objects.filter(clase=clase).select_related("miembro")

    return render(
        request,
        "gym/trainer/inscritos_list.html",
        {"trainer": trainer, "clase": clase, "inscritos": inscritos},
    )


def trainer_publicaciones_list(request, pk):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clase = get_object_or_404(Clase, pk=pk, instructor=trainer)
    publicaciones = PublicacionClase.objects.filter(clase=clase).order_by(
        "-fecha_publicacion"
    )

    return render(
        request,
        "gym/trainer/publicaciones_list.html",
        {"trainer": trainer, "clase": clase, "publicaciones": publicaciones},
    )


def trainer_publicacion_create(request, pk):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clase = get_object_or_404(Clase, pk=pk, instructor=trainer)

    if request.method == "POST":
        form = PublicacionTrainerForm(request.POST, request.FILES)
        if form.is_valid():
            publicacion = form.save(commit=False)
            publicacion.clase = clase
            publicacion.autor = trainer
            publicacion.save()
            messages.success(request, "Publicación creada correctamente.")
            return redirect(
                reverse("trainer_publicaciones_list", kwargs={"pk": clase.pk})
            )
    else:
        form = PublicacionTrainerForm()

    return render(
        request,
        "gym/trainer/publicacion_form.html",
        {
            "trainer": trainer,
            "clase": clase,
            "form": form,
            "action": "Crear",
        },
    )


def trainer_publicacion_edit(request, pk):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    publicacion = get_object_or_404(
        PublicacionClase, pk=pk, clase__instructor=trainer
    )

    if request.method == "POST":
        form = PublicacionTrainerForm(request.POST, request.FILES, instance=publicacion)
        if form.is_valid():
            form.save()
            messages.success(request, "Publicación actualizada correctamente.")
            return redirect(
                reverse(
                    "trainer_publicaciones_list",
                    kwargs={"pk": publicacion.clase.pk},
                )
            )
    else:
        form = PublicacionTrainerForm(instance=publicacion)

    return render(
        request,
        "gym/trainer/publicacion_form.html",
        {
            "trainer": trainer,
            "clase": publicacion.clase,
            "form": form,
            "action": "Editar",
        },
    )


def trainer_publicacion_delete(request, pk):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    publicacion = get_object_or_404(
        PublicacionClase, pk=pk, clase__instructor=trainer
    )

    if request.method == "POST":
        clase_id = publicacion.clase.pk
        publicacion.delete()
        messages.success(request, "Publicación eliminada correctamente.")
        return redirect(reverse("trainer_publicaciones_list", kwargs={"pk": clase_id}))

    return render(
        request,
        "gym/trainer/publicacion_delete.html",
        {"trainer": trainer, "publicacion": publicacion},
    )

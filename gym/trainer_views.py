import os
from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Count, Prefetch
from django.contrib import messages

from gym.models import Miembro, Curso, Clase, Asistencia, PublicacionClase, Comentario


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
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_class":
            curso_id = request.POST.get("curso_id")
            curso = Curso.objects.filter(pk=curso_id, profesor=trainer).first()
            if not curso:
                messages.error(request, "Curso no válido.")
                return redirect(reverse("trainer_home_html"))

            form = ClaseTrainerForm(request.POST, instructor=trainer, curso=curso)
            if form.is_valid():
                clase = form.save()
                messages.success(request, "Clase creada correctamente.")
                return redirect(
                    reverse("trainer_home_html") + f"?curso_id={curso.id}&clase_id={clase.id}"
                )
            messages.error(request, "Revisa los datos de la clase.")
            return redirect(reverse("trainer_home_html"))

        if action == "edit_class":
            class_id = request.POST.get("class_id")
            clase = Clase.objects.filter(pk=class_id, instructor=trainer).first()
            if not clase:
                messages.error(request, "Clase no válida.")
                return redirect(reverse("trainer_home_html"))

            form = ClaseTrainerForm(
                request.POST, instance=clase, instructor=trainer, curso=clase.curso
            )
            if form.is_valid():
                form.save()
                messages.success(request, "Clase actualizada correctamente.")
            else:
                messages.error(request, "No se pudo actualizar la clase.")
            return redirect(
                reverse("trainer_home_html")
                + f"?curso_id={clase.curso_id}&clase_id={clase.id}"
            )

        if action == "attendance":
            class_id = request.POST.get("class_id")
            clase = Clase.objects.filter(pk=class_id, instructor=trainer).first()
            if not clase:
                messages.error(request, "Clase no válida.")
                return redirect(reverse("trainer_home_html"))

            asistencias = Asistencia.objects.filter(clase=clase).select_related("miembro")
            for asistencia in asistencias:
                checked = request.POST.get(f"present_{asistencia.id}") == "on"
                if asistencia.asistio != checked:
                    asistencia.asistio = checked
                    asistencia.save(update_fields=["asistio"])
            messages.success(request, "Asistencia guardada.")
            return redirect(
                reverse("trainer_home_html")
                + f"?curso_id={clase.curso_id}&clase_id={clase.id}"
            )

        if action == "create_publication":
            class_id = request.POST.get("class_id")
            clase = Clase.objects.filter(pk=class_id, instructor=trainer).first()
            if not clase:
                messages.error(request, "Clase no válida.")
                return redirect(reverse("trainer_home_html"))

            titulo = request.POST.get("titulo", "").strip()
            contenido = request.POST.get("contenido", "").strip()
            video_url = request.POST.get("video_url", "").strip()
            if not titulo or not contenido:
                messages.error(request, "Título y contenido son obligatorios.")
                return redirect(
                    reverse("trainer_home_html")
                    + f"?curso_id={clase.curso_id}&clase_id={clase.id}"
                )

            PublicacionClase.objects.create(
                clase=clase,
                autor=trainer,
                titulo=titulo,
                contenido=contenido,
                video_url=video_url or None,
                imagen=request.FILES.get("imagen"),
                video_archivo=request.FILES.get("video_archivo"),
                archivo_1=request.FILES.get("archivo_1"),
                archivo_2=request.FILES.get("archivo_2"),
                archivo_3=request.FILES.get("archivo_3"),
            )
            messages.success(request, "Publicación creada.")
            return redirect(
                reverse("trainer_home_html")
                + f"?curso_id={clase.curso_id}&clase_id={clase.id}"
            )

        if action == "edit_publication":
            publication_id = request.POST.get("publication_id")
            publicacion = PublicacionClase.objects.filter(
                pk=publication_id, clase__instructor=trainer
            ).first()
            if not publicacion:
                messages.error(request, "Publicación no válida.")
                return redirect(reverse("trainer_home_html"))

            publicacion.titulo = request.POST.get("titulo", "").strip()
            publicacion.contenido = request.POST.get("contenido", "").strip()
            publicacion.video_url = request.POST.get("video_url", "").strip() or None

            if request.FILES.get("imagen"):
                publicacion.imagen = request.FILES.get("imagen")
            if request.FILES.get("video_archivo"):
                publicacion.video_archivo = request.FILES.get("video_archivo")
            if request.FILES.get("archivo_1"):
                publicacion.archivo_1 = request.FILES.get("archivo_1")
            if request.FILES.get("archivo_2"):
                publicacion.archivo_2 = request.FILES.get("archivo_2")
            if request.FILES.get("archivo_3"):
                publicacion.archivo_3 = request.FILES.get("archivo_3")

            publicacion.save()
            messages.success(request, "Publicación actualizada.")
            return redirect(
                reverse("trainer_home_html")
                + f"?curso_id={publicacion.clase.curso_id}&clase_id={publicacion.clase_id}"
            )

        if action == "delete_publication":
            publication_id = request.POST.get("publication_id")
            publicacion = PublicacionClase.objects.filter(
                pk=publication_id, clase__instructor=trainer
            ).first()
            if not publicacion:
                messages.error(request, "Publicación no válida.")
                return redirect(reverse("trainer_home_html"))

            curso_id = publicacion.clase.curso_id
            clase_id = publicacion.clase_id
            publicacion.delete()
            messages.success(request, "Publicación eliminada.")
            return redirect(
                reverse("trainer_home_html")
                + f"?curso_id={curso_id}&clase_id={clase_id}"
            )

        if action == "add_comment":
            publication_id = request.POST.get("publication_id")
            contenido = request.POST.get("comment_content", "").strip()
            publicacion = PublicacionClase.objects.filter(
                pk=publication_id, clase__instructor=trainer
            ).first()
            if not publicacion:
                messages.error(request, "Publicación no válida.")
                return redirect(reverse("trainer_home_html"))
            if not contenido:
                messages.error(request, "El comentario no puede estar vacío.")
                return redirect(
                    reverse("trainer_home_html")
                    + f"?curso_id={publicacion.clase.curso_id}&clase_id={publicacion.clase_id}"
                )

            Comentario.objects.create(
                publicacion=publicacion, autor=trainer, contenido=contenido
            )
            messages.success(request, "Comentario publicado.")
            return redirect(
                reverse("trainer_home_html")
                + f"?curso_id={publicacion.clase.curso_id}&clase_id={publicacion.clase_id}"
            )

        if action == "delete_comment":
            comment_id = request.POST.get("comment_id")
            comentario = Comentario.objects.filter(
                pk=comment_id,
                autor=trainer,
                publicacion__clase__instructor=trainer,
            ).first()
            if not comentario:
                messages.error(request, "Comentario no vÃ¡lido.")
                return redirect(reverse("trainer_home_html"))

            clase_id = comentario.publicacion.clase_id
            curso_id = comentario.publicacion.clase.curso_id
            comentario.delete()
            messages.success(request, "Comentario eliminado.")
            return redirect(
                reverse("trainer_home_html")
                + f"?curso_id={curso_id}&clase_id={clase_id}"
            )

    cursos = (
        Curso.objects.filter(profesor=trainer)
        .annotate(total_clases=Count("clases"))
        .prefetch_related(
            Prefetch(
                "clases",
                queryset=Clase.objects.filter(instructor=trainer).prefetch_related(
                    Prefetch(
                        "publicaciones",
                        queryset=PublicacionClase.objects.order_by("-fecha_publicacion").prefetch_related(
                            "comentarios__autor"
                        ),
                    ),
                    "asistencia_set__miembro",
                ),
            )
        )
        .order_by("nombre")
    )

    def _file_ext(name):
        return os.path.splitext(name)[1].replace(".", "").upper()

    image_exts = {"JPG", "JPEG", "PNG", "WEBP", "GIF"}
    video_exts = {"MP4", "WEBM", "OGG"}
    calendar_events = []

    for curso in cursos:
        for clase in curso.clases.all():
            publicaciones = list(clase.publicaciones.all())
            clase.latest_publicacion = publicaciones[0] if publicaciones else None
            clase.first_publicacion_id = (
                clase.latest_publicacion.id if clase.latest_publicacion else None
            )
            clase.total_comentarios = sum(
                len(pub.comentarios.all()) for pub in publicaciones
            )

            primary_video = None
            primary_video_url = None
            primary_image = None
            images = []
            files = []

            for pub in publicaciones:
                if pub.video_archivo and not primary_video:
                    ext = _file_ext(pub.video_archivo.name)
                    if ext in video_exts:
                        primary_video = pub.video_archivo
                if pub.video_url and not primary_video and not primary_video_url:
                    primary_video_url = pub.video_url
                if pub.imagen and not primary_image:
                    primary_image = pub.imagen

                if pub.imagen:
                    images.append({"url": pub.imagen.url, "label": pub.titulo or "Imagen"})

                for attachment in (pub.archivo_1, pub.archivo_2, pub.archivo_3):
                    if not attachment:
                        continue
                    ext = _file_ext(attachment.name)
                    if ext in image_exts:
                        images.append(
                            {
                                "url": attachment.url,
                                "label": os.path.basename(attachment.name),
                            }
                        )
                    else:
                        files.append(
                            {
                                "url": attachment.url,
                                "name": os.path.basename(attachment.name),
                                "ext": ext or "FILE",
                            }
                        )

                if pub.video_archivo:
                    ext = _file_ext(pub.video_archivo.name)
                    if ext and ext not in video_exts:
                        files.append(
                            {
                                "url": pub.video_archivo.url,
                                "name": os.path.basename(pub.video_archivo.name),
                                "ext": ext,
                            }
                        )

            if primary_video:
                clase.primary_media_type = "video"
                clase.primary_media_url = primary_video.url
            elif primary_video_url:
                clase.primary_media_type = "video_url"
                clase.primary_media_url = primary_video_url
            elif primary_image:
                clase.primary_media_type = "image"
                clase.primary_media_url = primary_image.url
            else:
                clase.primary_media_type = None
                clase.primary_media_url = None

            clase.media_images = images
            clase.media_files = files

            if clase.fecha:
                hora_label = clase.hora.strftime("%H:%M") if clase.hora else ""
                base_label = (
                    f"{curso.nombre} - {clase.nombre}"
                    if curso
                    else clase.nombre
                )
                label = f"{hora_label} · {base_label}" if hora_label else base_label
                calendar_events.append(
                    {"date": clase.fecha.isoformat(), "label": label}
                )

            asistencias = list(clase.asistencia_set.all())
            clase.total_inscritos = len(asistencias)
            clase.presentes = sum(1 for a in asistencias if a.asistio)
            clase.ausentes = clase.total_inscritos - clase.presentes

    return render(
        request,
        "gym/trainer.html",
        {"trainer": trainer, "cursos": cursos, "calendar_events": calendar_events},
    )


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

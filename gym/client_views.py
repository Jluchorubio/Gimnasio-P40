import os
from collections import defaultdict
from types import SimpleNamespace

from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Count, Prefetch
from django.contrib import messages
from django.http import JsonResponse

from gym.models import (
    Miembro,
    Clase,
    Curso,
    Asistencia,
    SolicitudMembresia,
    PublicacionClase,
    Comentario,
)


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ["contenido"]


def _get_cliente(request):
    cliente_id = request.GET.get("cliente_id")
    if cliente_id:
        try:
            request.session["cliente_id"] = int(cliente_id)
        except ValueError:
            pass

    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return None

    cliente = Miembro.objects.filter(
        pk=cliente_id, rol__nombre="CLIENTE"
    ).first()
    if not cliente:
        request.session.pop("cliente_id", None)
        return None
    return cliente


def _require_cliente(request):
    cliente = _get_cliente(request)
    if not cliente:
        return None, redirect(reverse("cliente_select"))
    return cliente, None


def cliente_select(request):
    clientes = Miembro.objects.filter(rol__nombre="CLIENTE").order_by("nombre")

    if request.method == "POST":
        cliente_id = request.POST.get("cliente_id")
        cliente = clientes.filter(pk=cliente_id).first()
        if not cliente:
            messages.error(request, "Selecciona un cliente válido.")
        else:
            request.session["cliente_id"] = cliente.id
            return redirect(reverse("cliente_home_html"))

    return render(request, "gym/cliente/select.html", {"clientes": clientes})


def cliente_dashboard(request):
    cliente, redirect_response = _require_cliente(request)
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "membership_request":
            if cliente.estado_membresia:
                messages.info(request, "Ya tienes una membresia activa.")
            else:
                solicitud_pendiente = SolicitudMembresia.objects.filter(
                    miembro=cliente, aprobada=False
                ).exists()
                if solicitud_pendiente:
                    messages.info(request, "Ya tienes una solicitud pendiente.")
                else:
                    SolicitudMembresia.objects.create(miembro=cliente, aprobada=False)
                    messages.success(request, "Solicitud enviada correctamente.")
            return redirect(reverse("cliente_home_html") + "?view=membership")
        if action == "add_comment":
            publication_id = request.POST.get("publication_id")
            contenido = request.POST.get("comment_content", "").strip()
            publicacion = PublicacionClase.objects.filter(
                pk=publication_id, clase__asistencia__miembro=cliente
            ).first()
            if not publicacion:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {"ok": False, "error": "Publicacion no valida."}, status=400
                    )
                messages.error(request, "Publicacion no valida.")
            elif not contenido:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {"ok": False, "error": "El comentario no puede estar vacio."},
                        status=400,
                    )
                messages.error(request, "El comentario no puede estar vacio.")
            else:
                comentario = Comentario.objects.create(
                    publicacion=publicacion, autor=cliente, contenido=contenido
                )
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {
                            "ok": True,
                            "class_id": publicacion.clase_id,
                            "comment": {
                                "id": comentario.id,
                                "author": cliente.nombre,
                                "initials": cliente.nombre[:2].upper(),
                                "content": comentario.contenido,
                                "date": comentario.fecha.strftime("%d %b"),
                            },
                        }
                    )
                messages.success(request, "Comentario publicado.")
                redirect_url = reverse("cliente_home_html")
                if publicacion.clase.curso_id:
                    redirect_url += (
                        f"?curso_id={publicacion.clase.curso_id}"
                        f"&clase_id={publicacion.clase_id}"
                    )
                return redirect(redirect_url)

        if action == "delete_comment":
            comment_id = request.POST.get("comment_id")
            comentario = Comentario.objects.filter(
                pk=comment_id,
                autor=cliente,
                publicacion__clase__asistencia__miembro=cliente,
            ).first()
            if not comentario:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {"ok": False, "error": "Comentario no valido."}, status=400
                    )
                messages.error(request, "Comentario no valido.")
            else:
                clase_id = comentario.publicacion.clase_id
                curso_id = comentario.publicacion.clase.curso_id
                comentario.delete()
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {"ok": True, "comment_id": comment_id, "class_id": clase_id}
                    )
                messages.success(request, "Comentario eliminado.")
                redirect_url = reverse("cliente_home_html")
                if curso_id:
                    redirect_url += (
                        f"?curso_id={curso_id}"
                        f"&clase_id={clase_id}"
                    )
                return redirect(redirect_url)

    asistencias = (
        Asistencia.objects.filter(miembro=cliente)
        .select_related("clase", "clase__curso", "clase__instructor")
        .order_by("clase__fecha", "clase__hora")
    )
    clase_ids = list(asistencias.values_list("clase_id", flat=True))

    publicaciones_qs = PublicacionClase.objects.order_by("-fecha_publicacion").prefetch_related(
        "comentarios__autor"
    )
    clases_inscritas = (
        Clase.objects.filter(pk__in=clase_ids)
        .select_related("curso", "instructor")
        .prefetch_related(Prefetch("publicaciones", queryset=publicaciones_qs))
        .order_by("fecha", "hora")
    )

    def _file_ext(name):
        return os.path.splitext(name)[1].replace(".", "").upper()

    image_exts = {"JPG", "JPEG", "PNG", "WEBP", "GIF"}
    video_exts = {"MP4", "WEBM", "OGG"}
    clases_por_curso = defaultdict(list)
    for clase in clases_inscritas:
        publicaciones = list(clase.publicaciones.all())
        clase.total_publicaciones = len(publicaciones)
        clase.total_comentarios = sum(
            len(pub.comentarios.all()) for pub in publicaciones
        )
        clase.latest_publicacion = publicaciones[0] if publicaciones else None
        clase.first_publicacion_id = publicaciones[0].id if publicaciones else None

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

        clase.media_images = images[:4]
        clase.media_files = files

        curso_key = clase.curso_id if clase.curso_id else "sin-curso"
        clases_por_curso[curso_key].append(clase)

    cursos = Curso.objects.annotate(total_clases=Count("clases")).order_by("nombre")
    mis_cursos = list(
        cursos.filter(clases__asistencia__miembro=cliente).distinct()
    )

    if "sin-curso" in clases_por_curso:
        clases_sin_curso = clases_por_curso["sin-curso"]
        mis_cursos.append(
            SimpleNamespace(
                id="sin-curso",
                nombre="Clases individuales",
                total_clases=len(clases_sin_curso),
                clases_inscritas=clases_sin_curso,
            )
        )

    for curso in mis_cursos:
        curso.clases_inscritas = getattr(curso, "clases_inscritas", None) or clases_por_curso.get(curso.id, [])
        curso.inscritas_count = len(curso.clases_inscritas)
        curso.progress_percent = (
            round((curso.inscritas_count / curso.total_clases) * 100)
            if curso.total_clases
            else 0
        )

    clases_disponibles = (
        Clase.objects.select_related("curso", "instructor")
        .order_by("fecha", "hora")
    )
    inscritos_ids = set(
        Asistencia.objects.filter(miembro=cliente).values_list("clase_id", flat=True)
    )
    counts = {
        row["clase_id"]: row["total"]
        for row in Asistencia.objects.filter(
            clase_id__in=clases_disponibles.values_list("id", flat=True)
        )
        .values("clase_id")
        .annotate(total=Count("id"))
    }
    for clase in clases_disponibles:
        clase.total_inscritos = counts.get(clase.id, 0)
        clase.is_inscrito = clase.id in inscritos_ids
        clase.cupo_lleno = clase.total_inscritos >= clase.cupo_maximo

    calendar_events = []
    for clase in clases_inscritas:
        calendar_events.append(
            {
                "date": clase.fecha.isoformat(),
                "label": clase.curso.nombre if clase.curso else clase.nombre,
            }
        )

    solicitudes = SolicitudMembresia.objects.filter(miembro=cliente).order_by(
        "-fecha_solicitud"
    )
    solicitud_pendiente = solicitudes.filter(aprobada=False).exists()

    return render(
        request,
        "gym/cliente.html",
        {
            "cliente": cliente,
            "cursos": cursos,
            "mis_cursos": mis_cursos,
            "calendar_events": calendar_events,
            "total_clases_inscritas": asistencias.count(),
            "total_clases_asistidas": asistencias.filter(asistio=True).count(),
            "clases_disponibles": clases_disponibles,
            "membresia_activa": cliente.estado_membresia,
            "solicitud_pendiente": solicitud_pendiente,
            "solicitudes": solicitudes,
        },
    )


def cliente_membresia(request):
    cliente, redirect_response = _require_cliente(request)
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        if cliente.estado_membresia:
            messages.info(request, "Ya tienes una membresia activa.")
        else:
            solicitud_pendiente = SolicitudMembresia.objects.filter(
                miembro=cliente, aprobada=False
            ).exists()
            if solicitud_pendiente:
                messages.info(request, "Ya tienes una solicitud pendiente.")
            else:
                SolicitudMembresia.objects.create(miembro=cliente, aprobada=False)
                messages.success(request, "Solicitud enviada correctamente.")
        return redirect(reverse("cliente_home_html") + "?view=membership")

    return redirect(reverse("cliente_home_html") + "?view=membership")


def cliente_clases_list(request):
    cliente, redirect_response = _require_cliente(request)
    if redirect_response:
        return redirect_response

    redirect_url = reverse("cliente_home_html") + "?view=courses"

    if request.method == "POST":
        clase_id = request.POST.get("clase_id")
        action = request.POST.get("action", "enroll")
        clase = Clase.objects.filter(pk=clase_id).first()
        if not clase:
            messages.error(request, "Clase no v?lida.")
            return redirect(redirect_url)

        if action == "cancel":
            asistencia = Asistencia.objects.filter(miembro=cliente, clase=clase).first()
            if not asistencia:
                messages.info(request, "No estas inscrito en esta clase.")
            else:
                asistencia.delete()
                messages.success(request, "Te diste de baja correctamente.")
            return redirect(redirect_url)

        if not cliente.estado_membresia:
            messages.error(request, "Necesitas una membresia activa para inscribirte.")
            return redirect(redirect_url)

        if Asistencia.objects.filter(miembro=cliente, clase=clase).exists():
            messages.info(request, "Ya estas inscrito en esta clase.")
            return redirect(redirect_url)

        asistencia = Asistencia(miembro=cliente, clase=clase, asistio=False)
        try:
            asistencia.full_clean()
            asistencia.save()
            messages.success(request, "Inscripcion realizada correctamente.")
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))

        return redirect(redirect_url)

    return redirect(redirect_url)


def cliente_mis_clases(request):
    cliente, redirect_response = _require_cliente(request)
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        clase_id = request.POST.get("clase_id")
        clase = Clase.objects.filter(pk=clase_id).first()
        if not clase:
            messages.error(request, "Clase no v??lida.")
            return redirect(reverse("cliente_mis_clases"))

        asistencia = Asistencia.objects.filter(miembro=cliente, clase=clase).first()
        if not asistencia:
            messages.info(request, "No estas inscrito en esta clase.")
        else:
            asistencia.delete()
            messages.success(request, "Te diste de baja correctamente.")
        return redirect(reverse("cliente_mis_clases"))

    asistencias = Asistencia.objects.filter(miembro=cliente).select_related("clase")
    return render(
        request,
        "gym/cliente/mis_clases.html",
        {"cliente": cliente, "asistencias": asistencias},
    )


def cliente_publicaciones_list(request, pk):
    cliente, redirect_response = _require_cliente(request)
    if redirect_response:
        return redirect_response

    clase = get_object_or_404(Clase, pk=pk)
    if not Asistencia.objects.filter(miembro=cliente, clase=clase).exists():
        messages.error(request, "Debes estar inscrito en la clase para ver contenido.")
        return redirect(reverse("cliente_mis_clases"))

    if request.method == "POST":
        form = ComentarioForm(request.POST)
        publicacion_id = request.POST.get("publicacion_id")
        publicacion = PublicacionClase.objects.filter(
            pk=publicacion_id, clase=clase
        ).first()
        if not publicacion:
            messages.error(request, "Publicacion no válida.")
        elif form.is_valid():
            comentario = form.save(commit=False)
            comentario.publicacion = publicacion
            comentario.autor = cliente
            comentario.save()
            messages.success(request, "Comentario publicado.")
            return redirect(
                reverse("cliente_publicaciones_list", kwargs={"pk": clase.pk})
            )
    else:
        form = ComentarioForm()

    publicaciones = (
        PublicacionClase.objects.filter(clase=clase)
        .prefetch_related("comentarios", "comentarios__autor")
        .order_by("-fecha_publicacion")
    )

    return render(
        request,
        "gym/cliente/publicaciones_list.html",
        {
            "cliente": cliente,
            "clase": clase,
            "publicaciones": publicaciones,
            "form": form,
        },
    )

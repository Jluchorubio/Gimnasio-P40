from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Count
from django.contrib import messages

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

    cursos = (
        Curso.objects.prefetch_related("clases")
        .annotate(total_clases=Count("clases"))
        .order_by("nombre")
    )
    mis_cursos = cursos.filter(clases__asistencia__miembro=cliente).distinct()

    return render(
        request,
        "gym/cliente.html",
        {"cliente": cliente, "cursos": cursos, "mis_cursos": mis_cursos},
    )


def cliente_membresia(request):
    cliente, redirect_response = _require_cliente(request)
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        if cliente.estado_membresia:
            messages.info(request, "Ya tienes una membresia activa.")
        else:
            pendiente = SolicitudMembresia.objects.filter(
                miembro=cliente, aprobada=False
            ).exists()
            if pendiente:
                messages.info(request, "Ya tienes una solicitud pendiente.")
            else:
                SolicitudMembresia.objects.create(miembro=cliente, aprobada=False)
                messages.success(request, "Solicitud enviada correctamente.")

    solicitudes = SolicitudMembresia.objects.filter(miembro=cliente).order_by(
        "-fecha_solicitud"
    )

    return render(
        request,
        "gym/cliente/membresia.html",
        {
            "cliente": cliente,
            "solicitudes": solicitudes,
            "membresia_activa": cliente.estado_membresia,
        },
    )


def cliente_clases_list(request):
    cliente, redirect_response = _require_cliente(request)
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        clase_id = request.POST.get("clase_id")
        clase = Clase.objects.filter(pk=clase_id).first()
        if not clase:
            messages.error(request, "Clase no válida.")
            return redirect(reverse("cliente_clases_list"))

        if not cliente.estado_membresia:
            messages.error(request, "Necesitas una membresia activa para inscribirte.")
            return redirect(reverse("cliente_clases_list"))

        if Asistencia.objects.filter(miembro=cliente, clase=clase).exists():
            messages.info(request, "Ya estas inscrito en esta clase.")
            return redirect(reverse("cliente_clases_list"))

        asistencia = Asistencia(miembro=cliente, clase=clase, asistio=False)
        try:
            asistencia.full_clean()
            asistencia.save()
            messages.success(request, "Inscripcion realizada correctamente.")
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))

        return redirect(reverse("cliente_clases_list"))

    clases = Clase.objects.select_related("instructor").order_by("fecha", "hora")
    inscritos_ids = set(
        Asistencia.objects.filter(miembro=cliente).values_list("clase_id", flat=True)
    )
    cupos = {
        clase.id: Asistencia.objects.filter(clase=clase).count() for clase in clases
    }

    return render(
        request,
        "gym/cliente/clases_list.html",
        {
            "cliente": cliente,
            "clases": clases,
            "inscritos_ids": inscritos_ids,
            "cupos": cupos,
        },
    )


def cliente_mis_clases(request):
    cliente, redirect_response = _require_cliente(request)
    if redirect_response:
        return redirect_response

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

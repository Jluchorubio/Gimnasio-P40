from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages

from gym.models import Miembro, Clase, Asistencia, PublicacionClase


class ClaseTrainerForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = ["nombre", "descripcion", "fecha", "hora", "cupo_maximo"]

    def __init__(self, *args, instructor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._instructor = instructor

    def save(self, commit=True):
        clase = super().save(commit=False)
        if self._instructor:
            clase.instructor = self._instructor
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

    return render(request, "gym/trainer.html", {"trainer": trainer})


def trainer_clases_list(request):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clases = Clase.objects.filter(instructor=trainer).order_by("fecha", "hora")
    return render(
        request,
        "gym/trainer/clases_list.html",
        {"trainer": trainer, "clases": clases},
    )


def trainer_clase_create(request):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        form = ClaseTrainerForm(request.POST, instructor=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, "Clase creada correctamente.")
            return redirect(reverse("trainer_clases_list"))
    else:
        form = ClaseTrainerForm(instructor=trainer)

    return render(
        request,
        "gym/trainer/clase_form.html",
        {"trainer": trainer, "form": form, "action": "Crear"},
    )


def trainer_clase_edit(request, pk):
    trainer, redirect_response = _require_trainer(request)
    if redirect_response:
        return redirect_response

    clase = get_object_or_404(Clase, pk=pk, instructor=trainer)

    if request.method == "POST":
        form = ClaseTrainerForm(request.POST, instance=clase, instructor=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, "Clase actualizada correctamente.")
            return redirect(reverse("trainer_clases_list"))
    else:
        form = ClaseTrainerForm(instance=clase, instructor=trainer)

    return render(
        request,
        "gym/trainer/clase_form.html",
        {"trainer": trainer, "form": form, "action": "Editar"},
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

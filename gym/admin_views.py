from django import forms
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages

from gym.models import (
    Rol,
    Plan,
    Miembro,
    Clase,
    Asistencia,
    SolicitudMembresia,
    PublicacionClase,
    Comentario,
)


class MiembroForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Deja en blanco para mantener la contraseña actual.",
    )

    class Meta:
        model = Miembro
        fields = [
            "nombre",
            "email",
            "password",
            "rol",
            "estado_membresia",
            "plan",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_password = self.instance.password
        if not self.instance.pk:
            self.fields["password"].required = True
            self.fields["password"].help_text = "Obligatoria para nuevos miembros."
        self.fields["password"].initial = ""

    def save(self, commit=True):
        miembro = super().save(commit=False)
        raw_password = self.cleaned_data.get("password")
        if raw_password:
            miembro.set_password(raw_password)
        elif self.instance.pk:
            miembro.password = self._original_password
        if commit:
            miembro.save()
            self.save_m2m()
        return miembro


MODEL_CONFIG = {
    "roles": {
        "model": Rol,
        "label": "Roles",
        "list_fields": ["nombre"],
    },
    "planes": {
        "model": Plan,
        "label": "Planes",
        "list_fields": ["nombre", "precio", "duracion_dias"],
    },
    "miembros": {
        "model": Miembro,
        "label": "Miembros",
        "list_fields": ["nombre", "email", "rol", "estado_membresia", "plan"],
        "form": MiembroForm,
    },
    "clases": {
        "model": Clase,
        "label": "Clases",
        "list_fields": ["nombre", "instructor", "fecha", "hora", "cupo_maximo"],
    },
    "asistencias": {
        "model": Asistencia,
        "label": "Asistencias",
        "list_fields": ["miembro", "clase", "fecha_inscripcion", "asistio"],
    },
    "solicitudes": {
        "model": SolicitudMembresia,
        "label": "Solicitudes de Membresia",
        "list_fields": ["miembro", "fecha_solicitud", "aprobada"],
    },
    "publicaciones": {
        "model": PublicacionClase,
        "label": "Publicaciones de Clase",
        "list_fields": ["clase", "autor", "titulo", "fecha_publicacion"],
    },
    "comentarios": {
        "model": Comentario,
        "label": "Comentarios",
        "list_fields": ["publicacion", "autor", "fecha"],
    },
}


def get_model_config(model_key):
    config = MODEL_CONFIG.get(model_key)
    if not config:
        raise ValueError("Modelo no encontrado.")
    return config


def admin_list(request, model_key):
    try:
        config = get_model_config(model_key)
    except ValueError:
        return render(request, "gym/admin/not_found.html", status=404)

    model = config["model"]
    objects = model.objects.all()
    fields = config["list_fields"]
    field_labels = [model._meta.get_field(f).verbose_name.title() for f in fields]
    filter_label = None

    clase_id = request.GET.get("clase")
    if clase_id:
        try:
            clase_id_int = int(clase_id)
        except ValueError:
            clase_id_int = None
        if clase_id_int:
            if model is Asistencia:
                objects = objects.filter(clase_id=clase_id_int)
            elif model is PublicacionClase:
                objects = objects.filter(clase_id=clase_id_int)
            elif model is Comentario:
                objects = objects.filter(publicacion__clase_id=clase_id_int)

            if model in {Asistencia, PublicacionClase, Comentario}:
                clase = Clase.objects.filter(pk=clase_id_int).first()
                if clase:
                    filter_label = f"{clase.nombre} ({clase.fecha})"

    context = {
        "model_key": model_key,
        "model_label": config["label"],
        "objects": objects,
        "fields": fields,
        "field_labels": field_labels,
        "filter_label": filter_label,
    }
    return render(request, "gym/admin/list.html", context)


def admin_create(request, model_key):
    try:
        config = get_model_config(model_key)
    except ValueError:
        return render(request, "gym/admin/not_found.html", status=404)

    model = config["model"]
    form_class = config.get("form") or modelform_factory(model, fields="__all__")

    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro creado correctamente.")
            return redirect(reverse("admin_list", kwargs={"model_key": model_key}))
    else:
        form = form_class()

    return render(
        request,
        "gym/admin/form.html",
        {
            "model_key": model_key,
            "model_label": config["label"],
            "form": form,
            "action": "Crear",
        },
    )


def admin_edit(request, model_key, pk):
    try:
        config = get_model_config(model_key)
    except ValueError:
        return render(request, "gym/admin/not_found.html", status=404)

    model = config["model"]
    instance = get_object_or_404(model, pk=pk)
    form_class = config.get("form") or modelform_factory(model, fields="__all__")

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Registro actualizado correctamente.")
            return redirect(reverse("admin_list", kwargs={"model_key": model_key}))
    else:
        form = form_class(instance=instance)

    return render(
        request,
        "gym/admin/form.html",
        {
            "model_key": model_key,
            "model_label": config["label"],
            "form": form,
            "action": "Editar",
        },
    )


def admin_delete(request, model_key, pk):
    try:
        config = get_model_config(model_key)
    except ValueError:
        return render(request, "gym/admin/not_found.html", status=404)

    model = config["model"]
    instance = get_object_or_404(model, pk=pk)

    if request.method == "POST":
        instance.delete()
        messages.success(request, "Registro eliminado correctamente.")
        return redirect(reverse("admin_list", kwargs={"model_key": model_key}))

    return render(
        request,
        "gym/admin/delete.html",
        {
            "model_key": model_key,
            "model_label": config["label"],
            "instance": instance,
        },
    )

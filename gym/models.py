from uuid import uuid4

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password, identify_hasher


class Rol(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Plan(models.Model):
    nombre = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    duracion_dias = models.IntegerField()

    def __str__(self):
        return self.nombre


class Miembro(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=200)

    fecha_registro = models.DateField(auto_now_add=True)

    estado_membresia = models.BooleanField(default=False)

    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

    @property
    def is_authenticated(self):
        return True

    def _password_is_hashed(self):
        if not self.password:
            return False
        try:
            identify_hasher(self.password)
            return True
        except Exception:
            return False

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if self.password and not self._password_is_hashed():
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    profesor = models.ForeignKey(
        "Miembro",
        on_delete=models.CASCADE,
        limit_choices_to={"rol__nombre": "ENTRENADOR"},
        related_name="cursos"
    )
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class TokenAcceso(models.Model):
    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, related_name="tokens")
    key = models.UUIDField(default=uuid4, unique=True, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token {self.key} - {self.miembro.email}"


class Clase(models.Model):

    nombre = models.CharField(max_length=100)
    curso = models.ForeignKey(
        Curso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clases"
    )

    instructor = models.ForeignKey(
        Miembro,
        on_delete=models.CASCADE,
        limit_choices_to={'rol__nombre': 'ENTRENADOR'}
    )

    descripcion = models.TextField(blank=True)

    fecha = models.DateField()
    hora = models.TimeField()

    cupo_maximo = models.IntegerField()

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"


class Asistencia(models.Model):

    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE)
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)

    fecha_inscripcion = models.DateField(auto_now_add=True)

    asistio = models.BooleanField(default=False)

    def clean(self):

        if not self.miembro.estado_membresia:
            raise ValidationError("El miembro no tiene membresía activa")

        inscritos = Asistencia.objects.filter(clase=self.clase).count()

        if inscritos >= self.clase.cupo_maximo:
            raise ValidationError("El cupo de la clase está lleno")

    def __str__(self):
        return f"{self.miembro} - {self.clase}"


class SolicitudMembresia(models.Model):

    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE)

    fecha_solicitud = models.DateField(auto_now_add=True)

    aprobada = models.BooleanField(default=False)

    def __str__(self):
        return f"Solicitud de {self.miembro.nombre}"


# ================================
# FORO DE CLASES
# ================================

class PublicacionClase(models.Model):

    clase = models.ForeignKey(
        Clase,
        on_delete=models.CASCADE,
        related_name="publicaciones"
    )

    autor = models.ForeignKey(
        Miembro,
        on_delete=models.CASCADE
    )

    titulo = models.CharField(max_length=200)

    contenido = models.TextField()

    imagen = models.ImageField(
        upload_to="clases/imagenes/",
        null=True,
        blank=True
    )

    video_archivo = models.FileField(
        upload_to="clases/videos/",
        null=True,
        blank=True
    )

    video_url = models.URLField(
        null=True,
        blank=True
    )

    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.clase.nombre}"


# ================================
# COMENTARIOS EN PUBLICACIONES
# ================================

class Comentario(models.Model):

    publicacion = models.ForeignKey(
        PublicacionClase,
        on_delete=models.CASCADE,
        related_name="comentarios"
    )

    autor = models.ForeignKey(
        Miembro,
        on_delete=models.CASCADE
    )

    contenido = models.TextField()

    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.autor.nombre}"

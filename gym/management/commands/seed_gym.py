from django.core.management.base import BaseCommand
from django.utils import timezone

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


class Command(BaseCommand):
    help = "Carga datos de ejemplo para el sistema del gimnasio."

    def handle(self, *args, **options):
        roles = {}
        for nombre in ["ADMINISTRADOR", "ENTRENADOR", "CLIENTE"]:
            rol, _ = Rol.objects.get_or_create(nombre=nombre)
            roles[nombre] = rol

        plan, _ = Plan.objects.get_or_create(
            nombre="Mensual",
            defaults={"precio": 120000, "duracion_dias": 30},
        )

        admin, _ = Miembro.objects.get_or_create(
            email="admin@gym.com",
            defaults={
                "nombre": "Admin Principal",
                "password": "admin123",
                "rol": roles["ADMINISTRADOR"],
                "estado_membresia": True,
                "plan": plan,
            },
        )

        entrenador, _ = Miembro.objects.get_or_create(
            email="trainer@gym.com",
            defaults={
                "nombre": "Carlos Trainer",
                "password": "trainer123",
                "rol": roles["ENTRENADOR"],
                "estado_membresia": True,
                "plan": plan,
            },
        )

        cliente, _ = Miembro.objects.get_or_create(
            email="cliente@gym.com",
            defaults={
                "nombre": "Ana Cliente",
                "password": "cliente123",
                "rol": roles["CLIENTE"],
                "estado_membresia": True,
                "plan": plan,
            },
        )

        clase, _ = Clase.objects.get_or_create(
            nombre="Funcional Básico",
            fecha=timezone.localdate(),
            hora=timezone.localtime().time().replace(second=0, microsecond=0),
            defaults={
                "instructor": entrenador,
                "descripcion": "Entrenamiento funcional para principiantes.",
                "cupo_maximo": 15,
            },
        )

        if not Asistencia.objects.filter(miembro=cliente, clase=clase).exists():
            asistencia = Asistencia(miembro=cliente, clase=clase, asistio=False)
            asistencia.full_clean()
            asistencia.save()

        if not SolicitudMembresia.objects.filter(miembro=cliente).exists():
            SolicitudMembresia.objects.create(miembro=cliente, aprobada=True)

        publicacion, _ = PublicacionClase.objects.get_or_create(
            clase=clase,
            titulo="Rutina de bienvenida",
            defaults={
                "autor": entrenador,
                "contenido": "Rutina recomendada para iniciar la semana.",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            },
        )

        if not Comentario.objects.filter(publicacion=publicacion, autor=cliente).exists():
            Comentario.objects.create(
                publicacion=publicacion,
                autor=cliente,
                contenido="Gracias profe, la rutina estuvo excelente.",
            )

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo cargados."))

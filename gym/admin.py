from django.contrib import admin
from .models import (
    Rol,
    Plan,
    Miembro,
    Clase,
    Asistencia,
    SolicitudMembresia,
    PublicacionClase,
    Comentario,
    TokenAcceso,
)

admin.site.register(Rol)
admin.site.register(Plan)
admin.site.register(Miembro)
admin.site.register(Clase)
admin.site.register(Asistencia)
admin.site.register(SolicitudMembresia)
admin.site.register(PublicacionClase)
admin.site.register(Comentario)
admin.site.register(TokenAcceso)

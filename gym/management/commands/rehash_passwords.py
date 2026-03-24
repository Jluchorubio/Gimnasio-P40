from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password, identify_hasher

from gym.models import Miembro


def is_hashed(value):
    if not value:
        return False
    try:
        identify_hasher(value)
        return True
    except Exception:
        return False


class Command(BaseCommand):
    help = "Convierte contraseñas en texto plano de Miembro a hashes seguros."

    def handle(self, *args, **options):
        updated = 0
        for miembro in Miembro.objects.all():
            if miembro.password and not is_hashed(miembro.password):
                miembro.password = make_password(miembro.password)
                miembro.save(update_fields=["password"])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Contraseñas actualizadas: {updated}")
        )

from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

from gym.models import TokenAcceso


class MiembroTokenAuthentication(BaseAuthentication):
    keyword = "Token"

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token_key = parts[1]
        try:
            token = TokenAcceso.objects.select_related("miembro").get(key=token_key)
        except TokenAcceso.DoesNotExist:
            raise exceptions.AuthenticationFailed("Token invalido o expirado.")

        return (token.miembro, token)

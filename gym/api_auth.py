from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from gym.authentication import MiembroTokenAuthentication
from gym.models import TokenAcceso
from gym.serializers import RegistroSerializer, LoginSerializer, MiembroSerializer


class RegistroView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        miembro = serializer.save()

        token = TokenAcceso.objects.create(miembro=miembro)
        data = {
            "token": str(token.key),
            "miembro": MiembroSerializer(miembro).data,
        }
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        miembro = serializer.validated_data["miembro"]

        TokenAcceso.objects.filter(miembro=miembro).delete()
        token = TokenAcceso.objects.create(miembro=miembro)

        data = {
            "token": str(token.key),
            "miembro": MiembroSerializer(miembro).data,
        }
        return Response(data, status=status.HTTP_200_OK)


class MeView(APIView):
    authentication_classes = [MiembroTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(MiembroSerializer(request.user).data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    authentication_classes = [MiembroTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.auth
        if token:
            token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

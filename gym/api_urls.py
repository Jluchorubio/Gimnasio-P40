from django.urls import path

from gym.api_auth import RegistroView, LoginView, MeView, LogoutView

urlpatterns = [
    path("auth/registro/", RegistroView.as_view(), name="api_registro"),
    path("auth/login/", LoginView.as_view(), name="api_login"),
    path("auth/me/", MeView.as_view(), name="api_me"),
    path("auth/logout/", LogoutView.as_view(), name="api_logout"),
]

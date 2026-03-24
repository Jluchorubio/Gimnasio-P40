from django.shortcuts import redirect, render


def auth_test(request):
    return render(request, "gym/auth_test.html")


def index(request):
    return render(request, "gym/index.html")


def roles(request):
    return render(request, "gym/roles.html")


def membresia(request):
    return redirect("/index/#membresia")


def admin_home(request):
    return render(request, "gym/admin.html")


def trainer_home(request):
    return render(request, "gym/trainer.html")


def cliente_home(request):
    return render(request, "gym/cliente.html")

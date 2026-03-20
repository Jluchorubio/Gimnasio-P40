from django.db import models

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
    estado_membresia = models.BooleanField(default=True)

    
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Clase(models.Model):
    nombre = models.CharField(max_length=100)
    instructor = models.CharField(max_length=100)
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

    def __str__(self):
        return f"{self.miembro} - {self.clase}"


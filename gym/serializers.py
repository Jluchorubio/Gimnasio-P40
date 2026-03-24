from rest_framework import serializers

from gym.models import Miembro, Rol


class MiembroSerializer(serializers.ModelSerializer):
    rol = serializers.CharField(source="rol.nombre", read_only=True)
    plan = serializers.CharField(source="plan.nombre", read_only=True)

    class Meta:
        model = Miembro
        fields = [
            "id",
            "nombre",
            "email",
            "rol",
            "estado_membresia",
            "plan",
            "fecha_registro",
        ]


class RegistroSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):
        if Miembro.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya esta registrado.")
        return value

    def create(self, validated_data):
        rol_cliente, _ = Rol.objects.get_or_create(nombre="CLIENTE")
        miembro = Miembro(
            nombre=validated_data["nombre"],
            email=validated_data["email"],
            rol=rol_cliente,
            estado_membresia=False,
        )
        miembro.set_password(validated_data["password"])
        miembro.save()
        return miembro


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            miembro = Miembro.objects.get(email=email)
        except Miembro.DoesNotExist:
            raise serializers.ValidationError("Credenciales invalidas.")

        if not miembro.check_password(password):
            raise serializers.ValidationError("Credenciales invalidas.")

        attrs["miembro"] = miembro
        return attrs

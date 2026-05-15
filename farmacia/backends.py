# farmacia/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class CustomUserBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Obtener el modelo de usuario personalizado
        UserModel = get_user_model()

        try:
            # Intentar obtener un usuario por nombre de usuario o correo electrónico
            user = UserModel.objects.get(Q(username=username) | Q(email=username))
        except UserModel.DoesNotExist:
            # Si no se encuentra el usuario, retornar None
            return None

        # Verificar la contraseña y retornar el usuario si es válido
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        # Obtener el modelo de usuario personalizado
        UserModel = get_user_model()

        try:
            # Intentar obtener un usuario por su ID
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            # Si no se encuentra el usuario, retornar None
            return None


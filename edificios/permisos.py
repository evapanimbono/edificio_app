from rest_framework import permissions
from usuarios.models_usuario_edificio import UsuarioEdificio
from contratos.models import Contrato

class EsSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


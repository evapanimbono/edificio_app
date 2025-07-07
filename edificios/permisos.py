from rest_framework import permissions
from usuarios.models_usuario_edificio import UsuarioEdificio
from contratos.models import Contrato

class EsSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class PuedeVerEdificio(permissions.BasePermission):
    """
    Permite ver edificios según:
    - Superuser: todos
    - Arrendador: edificios donde está asignado
    - Arrendatario: edificios donde tiene contrato activo
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser:
            return True

        if user.tipo_usuario == 'arrendador':
            edificios_ids = UsuarioEdificio.objects.filter(usuario=user).values_list('edificio_id', flat=True)
            return obj.id in edificios_ids

        if user.tipo_usuario == 'arrendatario':
            # Buscar si edificio está en alguno de sus contratos
            return obj.id in Contrato.objects.filter(arrendatario=user).values_list('apartamento__edificio_id', flat=True)

        return False

class PuedeModificarEliminarEdificio(permissions.BasePermission):
    """
    Solo superuser puede modificar o eliminar edificios
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return user.is_superuser

        return True

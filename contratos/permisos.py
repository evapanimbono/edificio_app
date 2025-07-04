from rest_framework import permissions

from contratos.models import Mensualidad
from usuarios.models import UsuarioEdificio

class PuedeModificarOMostrarMensualidad(permissions.BasePermission):
    """
    - Superuser puede ver y editar todo.
    - Arrendador puede ver/editar si administra el edificio.
    - Arrendatario solo puede ver si es su contrato.
    """

    def has_object_permission(self, request, view, obj: Mensualidad):
        user = request.user

        if user.is_superuser:
            return True

        if user.tipo_usuario == 'arrendador':
            edificios_ids = UsuarioEdificio.objects.filter(
                usuario=user
            ).values_list('edificio_id', flat=True)

            return obj.contrato.apartamento.edificio_id in edificios_ids

        if user.tipo_usuario == 'arrendatario':
            return obj.contrato.arrendatario_id == user.id

        return False

class PuedeEliminarMensualidadSinPagos(permissions.BasePermission):
    """
    Permite eliminar solo si:
    - Usuario es superuser o arrendador administrador.
    - La mensualidad no tiene pagos asociados.
    """

    def has_object_permission(self, request, view, obj: Mensualidad):
        user = request.user

        if not (user.is_superuser or user.tipo_usuario == 'arrendador'):
            return False

        # Validar si el usuario arrendador administra el edificio
        if user.tipo_usuario == 'arrendador':
            edificios_ids = UsuarioEdificio.objects.filter(
                usuario=user
            ).values_list('edificio_id', flat=True)

            if obj.contrato.apartamento.edificio_id not in edificios_ids:
                return False

        # No permitir eliminar si ya tiene pagos asociados
        return not obj.pagos.exists()

class EsArrendadorYAdministraLaMensualidad(permissions.BasePermission):
    """
    Solo permite si el usuario es arrendador y administra el edificio donde está la mensualidad.
    """

    def has_object_permission(self, request, view, obj: Mensualidad):
        if request.user.tipo_usuario != 'arrendador':
            return False

        edificios_ids = UsuarioEdificio.objects.filter(
            usuario=request.user
        ).values_list('edificio_id', flat=True)

        return obj.contrato.apartamento.edificio_id in edificios_ids
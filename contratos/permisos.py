from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from contratos.models import Mensualidad
from usuarios.models import UsuarioEdificio
from pagos.models import PagoMensualidad

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
            if request.method in permissions.SAFE_METHODS:
                # solo puede ver (GET, HEAD, OPTIONS)
                return obj.contrato.arrendatario_id == user.id
            else:
                # no puede modificar
                return False

        return False

class PuedeEliminarMensualidadSinPagos(permissions.BasePermission):
    """
    Permite eliminar solo si:
    - Usuario es superuser o arrendador administrador.
    - La mensualidad no tiene pagos asociados.
    - La mensualidad no está pagada ni anulada.
    """

    def has_object_permission(self, request, view, obj):
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

        # Bloquear si mensualidad está pagada o anulada
        if obj.estado != 'anulado':
            raise PermissionDenied("Solo se pueden eliminar mensualidades que hayan sido previamente anuladas.")
       
        # Verificar si tiene pagos asociados
        tiene_pagos = PagoMensualidad.objects.filter(mensualidad=obj).exists()
        if tiene_pagos:
            raise PermissionDenied("No se puede eliminar una mensualidad que ya tenga pagos registrados.")

        return True

class PuedeAnularMensualidadConPagos(permissions.BasePermission):
    """
    Permite anular solo si:
    - Usuario es superuser o arrendador administrador.
    - La mensualidad tiene pagos asociados.
    """

    def has_object_permission(self, request, view, obj):
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

        if obj.estado == 'anulado':
            raise PermissionDenied("La mensualidad ya está anulada.")

         # Permitir solo si no hay pagos activos (pendientes o validados)
        pagos_activos = PagoMensualidad.objects.filter(
            mensualidad=obj
        ).exclude(pago__estado_validacion__in=['anulado', 'rechazado'])

        if pagos_activos.exists():
            raise PermissionDenied("No se puede anular la mensualidad porque tiene pagos activos asociados.")
        
        return True

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
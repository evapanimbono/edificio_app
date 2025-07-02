from rest_framework import permissions

from .models import Pago
from .models_recibos import Recibo
from usuarios.models import UsuarioEdificio

class EsArrendatarioYEsDueñoDelPago(permissions.BasePermission):
    """
    Permite acceso solo si el usuario es arrendatario y está vinculado a alguna mensualidad o gasto extra del pago.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.tipo_usuario != 'arrendatario':
            return False

        # Verificar mensualidades asociadas al pago
        tiene_mensualidad = obj.mensualidades_pagadas.filter(
            mensualidad__contrato__arrendatario_id=request.user.id
        ).exists()

        # Verificar gastos extra asociados al pago
        tiene_gasto_extra = obj.gastos_pagados.filter(
            gasto_extra__apartamento__contrato__arrendatario_id=request.user.id
        ).exists()

        return tiene_mensualidad or tiene_gasto_extra

class EsArrendatarioYEsDueñoDelRecibo(permissions.BasePermission):
    """
    Permite acceso solo si el usuario es arrendatario y el recibo fue emitido para él.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.tipo_usuario != 'arrendatario':
            return False
        return obj.usuario_id == request.user.id


class EsArrendadorYAdministraElPago(permissions.BasePermission):
    """
    Permite acceso al arrendador solo si está vinculado al edificio de alguno de los apartamentos de ese pago.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.tipo_usuario != 'arrendador':
            return False

        edificio_ids = UsuarioEdificio.objects.filter(
            usuario=request.user
        ).values_list('edificio_id', flat=True)

        # Buscar si algún apartamento relacionado al pago pertenece a un edificio administrado por el usuario
        pago_mensualidades = obj.mensualidades_pagadas.filter(
            mensualidad__contrato__apartamento__edificio_id__in=edificio_ids
        ).exists()

        pago_gastos = obj.gastos_pagados.filter(
            gasto_extra__apartamento__edificio_id__in=edificio_ids
        ).exists()

        return pago_mensualidades or pago_gastos

class EsArrendadorYAdministraElRecibo(permissions.BasePermission):
    """
    Permite acceso al arrendador si el recibo está asociado a mensualidades o gastos de un edificio que administra.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.tipo_usuario != 'arrendador':
            return False

        edificio_ids = UsuarioEdificio.objects.filter(
            usuario=request.user
        ).values_list('edificio_id', flat=True)

        tiene_mensualidad = obj.mensualidades.filter(
            mensualidad__contrato__apartamento__edificio_id__in=edificio_ids
        ).exists()

        tiene_gasto = obj.gastos.filter(
            gasto_extra__apartamento__edificio_id__in=edificio_ids
        ).exists()

        return tiene_mensualidad or tiene_gasto

    
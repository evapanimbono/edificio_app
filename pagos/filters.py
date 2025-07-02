import django_filters
from django_filters import rest_framework as filters

from .models import Pago
from .models_recibos import Recibo

class PagoFilter(filters.FilterSet):
    fecha_pago = filters.DateFromToRangeFilter()
    usuario = filters.NumberFilter(field_name='usuario_id')
    tipo_pago = filters.CharFilter()
    estado_validacion = filters.CharFilter()
    validado_por = filters.NumberFilter(field_name='validado_por_id')

    class Meta:
        model = Pago
        fields = ['usuario', 'estado_validacion', 'tipo_pago', 'validado_por', 'fecha_pago']

class ReciboFilter(filters.FilterSet):
    fecha_emision = filters.DateFromToRangeFilter()
    fecha_vencimiento = filters.DateFromToRangeFilter()
    usuario = filters.NumberFilter(field_name='usuario_id')
    estado = filters.CharFilter()
    creado_por = filters.NumberFilter(field_name='creado_por_id')

    class Meta:
        model = Recibo
        fields = ['usuario', 'estado', 'creado_por', 'fecha_emision', 'fecha_vencimiento']
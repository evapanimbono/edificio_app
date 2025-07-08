import django_filters
from .models import GastoExtra

class GastoExtraFilter(django_filters.FilterSet):
    # Filtros accesibles para todos los usuarios
    estado = django_filters.CharFilter(field_name='estado', lookup_expr='iexact')
    monto_usd_min = django_filters.NumberFilter(field_name='monto_usd', lookup_expr='gte')
    monto_usd_max = django_filters.NumberFilter(field_name='monto_usd', lookup_expr='lte')
    fecha_vencimiento_desde = django_filters.DateFilter(field_name='fecha_vencimiento', lookup_expr='gte')
    fecha_vencimiento_hasta = django_filters.DateFilter(field_name='fecha_vencimiento', lookup_expr='lte')

    # Filtros adicionales que solo aplicarán si el usuario es arrendador o superuser
    apartamento = django_filters.NumberFilter(field_name='apartamento_id')
    fecha_generacion_desde = django_filters.DateFilter(field_name='fecha_generacion', lookup_expr='gte')
    fecha_generacion_hasta = django_filters.DateFilter(field_name='fecha_generacion', lookup_expr='lte')

    class Meta:
        model = GastoExtra
        fields = [
            'estado',
            'monto_usd_min',
            'monto_usd_max',
            'fecha_vencimiento_desde',
            'fecha_vencimiento_hasta',
            'fecha_generacion_desde',
            'fecha_generacion_hasta',
            'apartamento',
        ]
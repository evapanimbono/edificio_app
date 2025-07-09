import django_filters
from .models import Edificio

from .models_apartamentos import Apartamento

class EdificioFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(field_name='nombre', lookup_expr='icontains')
    direccion = django_filters.CharFilter(field_name='direccion', lookup_expr='icontains')
    fecha_creacion_desde = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    fecha_creacion_hasta = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    ultima_modificacion_desde = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    ultima_modificacion_hasta = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')

    class Meta:
        model = Edificio
        fields = [
            'nombre',
            'direccion',
            'fecha_creacion_desde',
            'fecha_creacion_hasta',
            'ultima_modificacion_desde',
            'ultima_modificacion_hasta',
        ]

class ApartamentoFilter(django_filters.FilterSet):
    edificio = django_filters.NumberFilter(field_name="edificio_id")
    edificio_nombre = django_filters.CharFilter(field_name='edificio__nombre', lookup_expr='icontains')
    estado = django_filters.CharFilter(field_name="estado")
    habitaciones_min = django_filters.NumberFilter(field_name="habitaciones", lookup_expr='gte')
    banos_min = django_filters.NumberFilter(field_name="banos", lookup_expr='gte')
    piso = django_filters.NumberFilter(field_name="piso")
    numero_apartamento = django_filters.CharFilter(field_name="numero_apartamento", lookup_expr='icontains')

    class Meta:
        model = Apartamento
        fields = ['edificio', 'edificio_nombre', 'estado', 'habitaciones_min', 'banos_min', 'piso', 'numero_apartamento']
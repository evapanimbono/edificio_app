import django_filters
from .models import Edificio

from .models_apartamentos import Apartamento

class EdificioFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(field_name='nombre', lookup_expr='icontains')

    class Meta:
        model = Edificio
        fields = ['nombre']

class ApartamentoFilter(django_filters.FilterSet):
    edificio = django_filters.NumberFilter(field_name="edificio_id")
    estado = django_filters.CharFilter(field_name="estado")
    habitaciones_min = django_filters.NumberFilter(field_name="habitaciones", lookup_expr='gte')
    banos_min = django_filters.NumberFilter(field_name="banos", lookup_expr='gte')
    piso = django_filters.NumberFilter(field_name="piso")
    numero_apartamento = django_filters.CharFilter(field_name="numero_apartamento", lookup_expr='icontains')

    class Meta:
        model = Apartamento
        fields = ['edificio', 'estado', 'habitaciones_min', 'banos_min', 'piso', 'numero_apartamento']
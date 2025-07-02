import django_filters
from .models import LogAccion

class LogAccionesFilter(django_filters.FilterSet):
    usuario = django_filters.NumberFilter(field_name='usuario_id')
    tabla_afectada = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = LogAccion
        fields = ['usuario', 'tabla_afectada']
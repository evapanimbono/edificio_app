import django_filters
from django.db.models import Q

from .models import LogAccion

class LogAccionesFilter(django_filters.FilterSet):
    usuario = django_filters.NumberFilter(field_name='usuario_id')
    tabla_afectada = django_filters.CharFilter(lookup_expr='icontains')
    accion = django_filters.CharFilter(lookup_expr='icontains')
    fecha_desde = django_filters.DateFilter(field_name='fecha', lookup_expr='gte')
    fecha_hasta = django_filters.DateFilter(field_name='fecha', lookup_expr='lte')
    edificio = django_filters.NumberFilter(method='filter_por_edificio')
    apartamento = django_filters.NumberFilter(method='filter_por_apartamento')

    class Meta:
        model = LogAccion
        fields = ['usuario', 'tabla_afectada', 'accion', 'fecha_desde', 'fecha_hasta', 'edificio', 'apartamento']

    def filter_por_edificio(self, queryset, name, value):
        """
        Filtra logs por edificio relacionado al usuario que hizo la acción,
        ya sea por UsuarioEdificio (arrendador) o Contrato->Apartamento->Edificio (arrendatario).
        """
        return queryset.filter(
            Q(usuario__usuarioedificio__edificio_id=value) |
            Q(usuario__contrato__apartamento__edificio_id=value)
        ).distinct()

    def filter_por_apartamento(self, queryset, name, value):
        """
        Filtra logs por apartamento relacionado al usuario que hizo la acción,
        a través de Contrato o directamente si la tabla_afectada lo indica.
        """
        # Filtra logs donde el usuario tiene contrato en ese apartamento
        qs = queryset.filter(
            Q(usuario__contrato__apartamento_id=value)
        )

        return qs.distinct()
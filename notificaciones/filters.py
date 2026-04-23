import django_filters
from .models import Notificacion

class NotificacionFilter(django_filters.FilterSet):
    estado = django_filters.CharFilter(field_name='estado')
    leido = django_filters.BooleanFilter(field_name='leido')
    tipo = django_filters.CharFilter(field_name='tipo')
    objeto_tipo = django_filters.CharFilter(field_name='objeto_tipo')

    fecha_desde = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__gte'
    )
    fecha_hasta = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__lte'
    )

    class Meta:
        model = Notificacion
        fields = [
            'estado',
            'leido',
            'tipo',
            'objeto_tipo',
            'fecha_desde',
            'fecha_hasta',
        ]
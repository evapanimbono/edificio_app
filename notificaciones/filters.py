import django_filters
from .models import Notificacion

class NotificacionFilter(django_filters.FilterSet):
    receptor = django_filters.NumberFilter(field_name='receptor_id')
    leido = django_filters.BooleanFilter(field_name='leido')

    class Meta:
        model = Notificacion
        fields = ['receptor', 'leido']
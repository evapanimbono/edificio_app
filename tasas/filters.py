import django_filters
from .models import TasaDia

class TasasDiaFilter(django_filters.FilterSet):
    echa = django_filters.DateFilter(field_name='fecha', lookup_expr='exact')
    fecha__gte = django_filters.DateFilter(field_name='fecha', lookup_expr='gte')
    fecha__lte = django_filters.DateFilter(field_name='fecha', lookup_expr='lte')

    class Meta:
        model = TasaDia
        fields = ['fecha', 'fecha__gte', 'fecha__lte']
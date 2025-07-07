import django_filters
from .models import Edificio

class EdificioFilter(django_filters.FilterSet):
    nombre = django_filters.CharFilter(field_name='nombre', lookup_expr='icontains')

    class Meta:
        model = Edificio
        fields = ['nombre']
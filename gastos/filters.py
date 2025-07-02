import django_filters
from .models import GastoExtra

class GastoExtraFilter(django_filters.FilterSet):
    apartamento = django_filters.NumberFilter(field_name='apartamento_id')
    estado = django_filters.CharFilter(field_name='estado')

    class Meta:
        model = GastoExtra
        fields = ['apartamento', 'estado']
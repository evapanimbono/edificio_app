import django_filters
from .models_mensualidades import Mensualidad
from .models import Contrato

class MensualidadFilter(django_filters.FilterSet):
    estado = django_filters.CharFilter(field_name="estado")
    fecha_inicio = django_filters.DateFilter(field_name="fecha_inicio", lookup_expr="gte")
    fecha_vencimiento = django_filters.DateFilter(field_name="fecha_vencimiento", lookup_expr="lte")
    contrato = django_filters.NumberFilter(field_name="contrato_id")

    class Meta:
        model = Mensualidad
        fields = ['estado', 'fecha_inicio', 'fecha_vencimiento', 'contrato']

class ContratosFilter(django_filters.FilterSet):
    apartamento = django_filters.NumberFilter(field_name="apartamento_id")

    class Meta:
        model = Contrato
        fields = ['apartamento']        
import django_filters
from .models_mensualidades import Mensualidad
from .models import Contrato

class MensualidadFilter(django_filters.FilterSet):
    class Meta:
        model = Mensualidad
        fields = {
            'contrato': ['exact'],
            'estado': ['exact'],
            'fecha_vencimiento': ['exact', 'lte', 'gte'],
        }

class ContratosFilter(django_filters.FilterSet):
    class Meta:
        model = Contrato
        fields = ['arrendatario', 'apartamento']        
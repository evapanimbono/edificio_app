import django_filters
from .models import Encuesta
from .models import RespuestaEncuestas

class EncuestasFilter(django_filters.FilterSet):
    titulo = django_filters.CharFilter(lookup_expr='icontains')
    creada_por = django_filters.NumberFilter(field_name='creada_por_id')

    class Meta:
        model = Encuesta
        fields = ['titulo', 'creada_por']

class RespuestasEncuestasFilter(django_filters.FilterSet):
    arrendatario = django_filters.NumberFilter(field_name='arrendatario_id')
    encuesta = django_filters.NumberFilter(field_name='encuesta_id')

    class Meta:
        model = RespuestaEncuestas
        fields = ['arrendatario', 'encuesta']        
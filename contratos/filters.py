import django_filters
from .models_mensualidades import Mensualidad
from .models import Contrato

class MensualidadFilter(django_filters.FilterSet):
    estado = django_filters.ChoiceFilter(field_name="estado", choices=Mensualidad.ESTADO_CHOICES)
    fecha_generacion_desde = django_filters.DateFilter(field_name="fecha_generacion", lookup_expr="gte")
    fecha_generacion_hasta = django_filters.DateFilter(field_name="fecha_generacion", lookup_expr="lte")
    fecha_vencimiento_desde = django_filters.DateFilter(field_name="fecha_vencimiento", lookup_expr="gte")
    fecha_vencimiento_hasta = django_filters.DateFilter(field_name="fecha_vencimiento", lookup_expr="lte")
    contrato = django_filters.NumberFilter(field_name="contrato_id")

    # Campos relacionales útiles
    apartamento = django_filters.NumberFilter(field_name="contrato__apartamento_id")
    usuario = django_filters.NumberFilter(field_name="contrato__arrendatario_id")
    edificio = django_filters.NumberFilter(field_name="contrato__apartamento__edificio_id")

    class Meta:
        model = Mensualidad
        fields = [
            'estado', 'fecha_generacion_desde', 'fecha_generacion_hasta',
            'fecha_vencimiento_desde', 'fecha_vencimiento_hasta',
            'contrato', 'apartamento', 'usuario', 'edificio'
        ]
class ContratosFilter(django_filters.FilterSet):
    apartamento = django_filters.NumberFilter(field_name="apartamento_id")
    usuario = django_filters.NumberFilter(field_name="arrendatario_id")
    edificio = django_filters.NumberFilter(field_name="apartamento__edificio_id")
    estado = django_filters.ChoiceFilter(field_name="estado", choices=Contrato.ESTADO_CHOICES)
    fecha_inicio_desde = django_filters.DateFilter(field_name="fecha_inicio", lookup_expr="gte")
    fecha_inicio_hasta = django_filters.DateFilter(field_name="fecha_inicio", lookup_expr="lte")
    fecha_fin_desde = django_filters.DateFilter(field_name="fecha_fin", lookup_expr="gte")
    fecha_fin_hasta = django_filters.DateFilter(field_name="fecha_fin", lookup_expr="lte")

    class Meta:
        model = Contrato
        fields = [
            'apartamento', 'usuario', 'edificio', 'estado',
            'fecha_inicio_desde', 'fecha_inicio_hasta',
            'fecha_fin_desde', 'fecha_fin_hasta'
        ]       
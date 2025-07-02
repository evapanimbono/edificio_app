import django_filters

from .models import Usuario
from .models_usuario_edificio import UsuarioEdificio
from .models_usuario_solicitud import SolicitudUsuarioEdificio

#==================== SUPERUSER =====================
class SolicitudUsuarioEdificioFilter(django_filters.FilterSet):
    estado = django_filters.CharFilter(lookup_expr='iexact')
    tipo_solicitado = django_filters.CharFilter(lookup_expr='iexact')
    edificio_id = django_filters.NumberFilter(field_name='edificio__id')
    fecha_creacion = django_filters.DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = SolicitudUsuarioEdificio
        fields = ['estado', 'tipo_solicitado', 'edificio_id', 'fecha_creacion']

class UsuarioEdificioFilter(django_filters.FilterSet):
    usuario_id = django_filters.NumberFilter(field_name='usuario__id')
    edificio_id = django_filters.NumberFilter(field_name='edificio__id')
    rol = django_filters.CharFilter(lookup_expr='iexact')
    fecha_asignacion = django_filters.DateFromToRangeFilter()

    class Meta:
        model = UsuarioEdificio
        fields = ['usuario_id', 'edificio_id', 'rol', 'fecha_asignacion']

#=================== ARRENDADOR =====================
class UsuarioAsignadoFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    correo = django_filters.CharFilter(lookup_expr='icontains')
    estado = django_filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = Usuario
        fields = ['username', 'correo', 'estado']
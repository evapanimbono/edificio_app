from django.urls import path
from .views import (
    ListaTasasDiaAPIView,
    DetalleTasaDiaAPIView,
    CrearTasaDiaAPIView,
    AnularTasaDiaAPIView,
    TasaDiaActivaAPIView,
    EliminarTasaDiaAPIView
)

urlpatterns = [
    path('', ListaTasasDiaAPIView.as_view(), name='tasas-dia-lista'), # Listado de tasas del día
    path('detalle/<int:pk>/', DetalleTasaDiaAPIView.as_view(), name='tasas-dia-detalle'), # Detalle de tasa del día
    path('crear/', CrearTasaDiaAPIView.as_view(), name='tasa-dia-crear'), # Crear una nueva tasa del día
    path('anular/<int:pk>/', AnularTasaDiaAPIView.as_view(), name='anular-tasa'), # Anular una tasa del día (solo si no tiene pagos o los pagos asociados estan anulados o rechazados)
    path('eliminar/<int:pk>/', EliminarTasaDiaAPIView.as_view(), name='eliminar-tasa'), # Eliminar una tasa del día (solo si está en estado 'anulada')
    path('activa/', TasaDiaActivaAPIView.as_view(), name='tasa-dia-activa'), # Obtener la tasa activa del día
]
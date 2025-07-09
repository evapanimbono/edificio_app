from django.urls import path
from .views import ListaTasasDiaAPIView,DetalleTasaDiaAPIView,CrearTasaDiaAPIView

urlpatterns = [
    path('', ListaTasasDiaAPIView.as_view(), name='tasas-dia-lista'), # Listado de tasas del día
    path('detalle/<int:pk>/', DetalleTasaDiaAPIView.as_view(), name='tasas-dia-detalle'), # Detalle de tasa del día
    path('crear/', CrearTasaDiaAPIView.as_view(), name='tasa-dia-crear'), # Crear una nueva tasa del día
]
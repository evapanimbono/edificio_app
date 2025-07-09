from django.urls import path
from .views import (
    ListaLogAccionesAPIView,
    DetalleLogAccionAPIView
)

urlpatterns = [
    path('', ListaLogAccionesAPIView.as_view()), #Lista de logs de acciones
    path('<int:pk>/', DetalleLogAccionAPIView.as_view(), name='log-detalle'), # Detalle de un log de acción
]
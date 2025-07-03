from django.urls import path
from .views import (
    ListaContratosAPIView,
    ListaMensualidadesAPIView,
    CrearContratoAPIView,
    ContratoDetailArrendatarioAPIView,
    ContratoDetailArrendadorAPIView,
)

urlpatterns = [
    path('', ListaContratosAPIView.as_view(), name='contratos-lista'), # Lista de contratos
    path('mensualidades/', ListaMensualidadesAPIView.as_view(), name='mensualidades-lista'), # Lista de mensualidades

    path('crear/', CrearContratoAPIView.as_view(), name='crear-contrato'), #Crear contrato (arrendador o superusuario)
    path('detalle/<int:pk>/', ContratoDetailArrendatarioAPIView.as_view(), name='detalle-contrato-arrendatario'), # Detalle de contrato (arrendatario)
    path('<int:pk>/', ContratoDetailArrendadorAPIView.as_view(), name='detalle-contrato-arrendador'), # Detalle de contrato (arrendador o superusuario)
]
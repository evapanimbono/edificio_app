from django.urls import path
from .views import (
    ListaContratosAPIView,    
    CrearContratoAPIView,
    ContratoDetailArrendatarioAPIView,
    ContratoDetailArrendadorAPIView,
    MiContratoActivoAPIView,

    ListaMensualidadesAPIView,
    DetalleMensualidadAPIView,
    CrearMensualidadAPIView,
    ActualizarMensualidadAPIView,
    EliminarMensualidadAPIView,
    AnularMensualidadAPIView,
)

urlpatterns = [
    path('', ListaContratosAPIView.as_view(), name='contratos-lista'), # Lista de contratos
    path('mensualidades/', ListaMensualidadesAPIView.as_view(), name='mensualidades-lista'), # Lista de mensualidades

    path('crear/', CrearContratoAPIView.as_view(), name='crear-contrato'), #Crear contrato (arrendador o superusuario)
    path('detalle/<int:pk>/', ContratoDetailArrendatarioAPIView.as_view(), name='detalle-contrato-arrendatario'), # Detalle de contrato (arrendatario)
    path('<int:pk>/', ContratoDetailArrendadorAPIView.as_view(), name='detalle-contrato-arrendador'), # Detalle, actualizar o eliminar un contrato (arrendador o superusuario)
    path('mi-contrato/', MiContratoActivoAPIView.as_view(), name='mi-contrato-activo'),

    path('mensualidades/detalle/<int:pk>/', DetalleMensualidadAPIView.as_view(), name='detalle-mensualidad'), # Detalle de mensualidad (arrendador, arrendatario o superusuario)
    path('mensualidades/crear/', CrearMensualidadAPIView.as_view(), name='crear_mensualidad'), # Crear mensualidad (superusuario)
    path('mensualidades/actualizar/<int:pk>/', ActualizarMensualidadAPIView.as_view(), name='actualizar_mensualidad'), # Modificar mensualidad (arrendador o superusuario, solo fecha_vencimiento)
    path('mensualidades/eliminar/<int:pk>/', EliminarMensualidadAPIView.as_view(), name='eliminar-mensualidad'), # Eliminar mensualidad (arrendador o superusuario, sin pagos asociados)
    path('mensualidades/anular/<int:pk>/', AnularMensualidadAPIView.as_view(), name='anular-mensualidad'), # Anular mensualidad (arrendador o superusuario, con pagos asociados)
]
from django.urls import path
from .views import ListaPagosAPIView,RegistrarPagoView,ValidarPagoView,HistorialPagosView,DetallePagoView

from .views import ListaRecibosAPIView,RecibosDelUsuarioView,GenerarReciboAPIView

urlpatterns = [
    path('', ListaPagosAPIView.as_view(), name='lista_pagos'),
    path('registrar/', RegistrarPagoView.as_view(), name='registrar_pago'),
    path('validar/<int:pago_id>/', ValidarPagoView.as_view(), name='validar_pago'),
    path('validados/historial/', HistorialPagosView.as_view(), name='historial_pagos'),
    path('detalle/<int:id>/', DetallePagoView.as_view(), name='detalle-pago'),
    
    path('recibos/', ListaRecibosAPIView.as_view(), name='lista_recibos'),
    path('recibos/usuario/', RecibosDelUsuarioView.as_view(), name='recibos_usuario'),
    path('recibos/generar/', GenerarReciboAPIView.as_view(), name='generar_recibo'),
]
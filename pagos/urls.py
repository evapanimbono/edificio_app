from django.urls import path
from .views import ListaPagosAPIView,RegistrarPagoView,ValidarPagoView,HistorialPagosView,DetallePagoView,DetallePagoPrevioAPIView,AnularPagoView

from .views import ListaRecibosAPIView,ReciboDetalleAPIView

urlpatterns = [
    path('', ListaPagosAPIView.as_view(), name='lista_pagos'), #Listar pagos filtrables (por tipo de usuario: arrendador ve pagos de su edificio, arrendatario ve los suyos)
    path('registrar/', RegistrarPagoView.as_view(), name='registrar_pago'), #Permite registrar un nuevo pago (efectivo, transferencia o mixto)
    path('validar/<int:pago_id>/', ValidarPagoView.as_view(), name='validar_pago'), #Permite que el arrendador valide o rechace pagos pendientes
    path('validados/historial/', HistorialPagosView.as_view(), name='historial_pagos'), #Ver historial de pagos ya validados (por usuario)
    path('detalle/<int:id>/', DetallePagoView.as_view(), name='detalle-pago'), #Muestra el detalle completo de un pago existente
    path('detalle-previo/', DetallePagoPrevioAPIView.as_view(), name='detalle-pago-previo'), # Detalle de pago previo (antes de registrar)
    path('anular/<int:pago_id>/', AnularPagoView.as_view(), name='anular_pago'), # Permite anular un pago solo si esta validado (arrendador o superusuario)

    path('recibos/', ListaRecibosAPIView.as_view(), name='lista_recibos'), #Lista de recibos (filtrable por estado, usuario, fechas)
    path('recibos/<int:id>/', ReciboDetalleAPIView.as_view(), name='detalle-recibo'), #Detalle de un recibo específico (por id)
]
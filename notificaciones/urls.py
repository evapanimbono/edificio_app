from django.urls import path
from .views import (
    ListaNotificacionesAPIView, 
    DetalleNotificacionAPIView,
    MarcarNotificacionLeidaAPIView,
    ArchivarNotificacionAPIView)

urlpatterns = [
    path('', ListaNotificacionesAPIView.as_view(), name='notificaciones'),
    path('detalle/<int:pk>/', DetalleNotificacionAPIView.as_view(), name='notificacion'),
    path('leer/<int:pk>/', MarcarNotificacionLeidaAPIView.as_view(), name='leer-notificacion'),
    path('archivar/<int:pk>/', ArchivarNotificacionAPIView.as_view(), name='archivar-notificacion'),
]
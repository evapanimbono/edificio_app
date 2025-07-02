from django.urls import path
from .views import ListaNotificacionesAPIView

urlpatterns = [
    path('', ListaNotificacionesAPIView.as_view(), name='notificaciones-lista'),
]
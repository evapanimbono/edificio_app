from django.urls import path
from .views import ListaContratosAPIView
from .views import ListaMensualidadesAPIView

urlpatterns = [
    path('', ListaContratosAPIView.as_view(), name='contratos-lista'),
    path('mensualidades/', ListaMensualidadesAPIView.as_view(), name='mensualidades-lista'),
]
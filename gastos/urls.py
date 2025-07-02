from django.urls import path
from .views import ListaGastosExtraAPIView,CrearGastoExtraAPIView

urlpatterns = [
    path('', ListaGastosExtraAPIView.as_view(), name='gastos-extra-lista'),
    path('crear/', CrearGastoExtraAPIView.as_view(), name='crear-gasto-extra'),
]
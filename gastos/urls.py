from django.urls import path
from .views import (
    ListaGastosExtraAPIView,
    CrearGastoExtraAPIView,
    DetalleGastoExtraAPIView,
    ActualizarGastoExtraAPIView,
    EliminarGastoExtraAPIView
)

urlpatterns = [
    path('', ListaGastosExtraAPIView.as_view(), name='gastos-extra-lista'), # Lista de gastos extra (Todos los usuarios)
    path('crear/', CrearGastoExtraAPIView.as_view(), name='crear-gasto-extra'), # Crear un gasto extra manual (solo arrendador o superusuario)
    path('detalle/<int:pk>/', DetalleGastoExtraAPIView.as_view(), name='detalle-gasto-extra'), # Detalle de un gasto extra (Todos los usuarios)
    path('editar/<int:pk>/', ActualizarGastoExtraAPIView.as_view(), name='editar-gasto-extra'), # Actualizar un gasto extra (solo arrendador o superusuario)
    path('eliminar/<int:pk>/', EliminarGastoExtraAPIView.as_view(), name='eliminar-gasto-extra'), # Eliminar un gasto extra (solo arrendador o superusuario)
]
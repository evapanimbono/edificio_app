from django.urls import path
from .views import (
    ListaEdificiosAPIView,
    DetalleEdificioAPIView,
    CrearEdificioAPIView,
    ActualizarEdificioAPIView,
    EliminarEdificioAPIView,

    ListaApartamentosAPIView,
    DetalleApartamentoAPIView,
    CrearApartamentoAPIView,
    ActualizarApartamentoAPIView,
    EliminarApartamentoAPIView,

)

#from .views import ListaApartamentosAPIView

urlpatterns = [
    path('', ListaEdificiosAPIView.as_view(), name='lista-edificios'), # Listar edificios (SuperUser/Arrendador)
    path('detalle/<int:pk>/', DetalleEdificioAPIView.as_view(), name='detalle-edificio'), # Detalle edificio (todos pueden ver)
    path('crear/', CrearEdificioAPIView.as_view(), name='crear-edificio'), # Crear edificio (solo superuser)
    path('actualizar/<int:pk>/', ActualizarEdificioAPIView.as_view(), name='actualizar-edificio'), # Actualizar edificio (solo superuser)
    path('eliminar/<int:pk>/', EliminarEdificioAPIView.as_view(), name='eliminar-edificio'), # Eliminar edificio (solo superuser)

    path('apartamentos/', ListaApartamentosAPIView.as_view(), name='lista_apartamentos'), # Listar apartamentos (SuperUser/Arrendador)
    path('apartamentos/detalle/<int:pk>/', DetalleApartamentoAPIView.as_view(), name='detalle_apartamento'), # Detalle apartamento (todos pueden ver)
    path('apartamentos/crear/', CrearApartamentoAPIView.as_view(), name='crear_apartamento'), # Crear apartamento (SuperUser/Arrendador)
    path('apartamentos/actualizar/<int:pk>/', ActualizarApartamentoAPIView.as_view(), name='actualizar_apartamento'), # Actualizar apartamento (SuperUser/Arrendador)
]
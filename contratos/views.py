from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import PermissionDenied

from rest_framework import generics
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Contrato
from .serializers_contratos import ContratoSerializer
from .filters import ContratosFilter, MensualidadFilter

from .models_mensualidades import Mensualidad
from .serializers_mensualidades import MensualidadSerializer
from .filters import MensualidadFilter

from .permisos import(
    PuedeModificarOMostrarMensualidad,
    PuedeEliminarMensualidadSinPagos,
    EsArrendadorYAdministraLaMensualidad
)
from usuarios.permissions import EsArrendador

#Vista de contatos filtrada por tipo de usuario
class ListaContratosAPIView(generics.ListAPIView):
    # Arrendatario: lista de contratos donde es arrendatario
    # Arrendador: lista de contratos de los apartamentos que administra
    serializer_class = ContratoSerializer 
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContratosFilter

    def get_queryset(self):
        user = self.request.user

        if user.tipo_usuario == 'arrendatario':
            return Contrato.objects.filter(arrendatario=user)
        
        elif user.tipo_usuario == 'arrendador':
            edificios = user.edificios_asignados.values_list('edificio_id', flat=True)
            return Contrato.objects.filter(apartamento__edificio_id__in=edificios)
        
        if user.is_superuser:
            return Contrato.objects.all()

        return Contrato.objects.none()

#Vista de mensualidades filtrada por tipo de usuario
class ListaMensualidadesAPIView(generics.ListAPIView):
    # Arrendatario: lista de mensualidades de sus contratos
    # Arrendador: lista de mensualidades de los apartamentos que administra

    serializer_class = MensualidadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = MensualidadFilter

    def get_queryset(self):
        user = self.request.user

        if user.tipo_usuario == 'arrendatario':
            return Mensualidad.objects.filter(contrato__arrendatario=user)
    
        elif user.tipo_usuario == 'arrendador':
            edificios = user.edificios_asignados.values_list('edificio_id', flat=True)
            return Mensualidad.objects.filter(contrato__apartamento__edificio_id__in=edificios)
        
        if user.is_superuser:
            return Mensualidad.objects.all()

        return Mensualidad.objects.none()

#============================= CONTRATOS =============================
#Vista para crear contratos, solo accesible por arrendadores o superusuarios
class CrearContratoAPIView(CreateAPIView):
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        usuario = self.request.user
        
        #Solo arrendadores y superusuarios pueden crear contratos
        if usuario.tipo_usuario != 'arrendador' and not usuario.is_superuser:
            raise PermissionDenied("No tienes permiso para crear contratos.")
        
        serializer.save()

#Vista para obtener detalles de un contrato, accesible por arrendatario
class ContratoDetailArrendatarioAPIView(generics.RetrieveAPIView):
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.tipo_usuario == 'arrendatario':
            return Contrato.objects.filter(arrendatario=user)
        
        return Contrato.objects.none()

#Vista para ver detalle, actualizar o eliminar un contrato, accesible por arrendador o superusuario 
class ContratoDetailArrendadorAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContratoSerializer
    permission_classes = [IsAuthenticated, EsArrendador]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Contrato.objects.all()
        edificios = user.edificios_asignados.values_list('edificio_id', flat=True)
        return Contrato.objects.filter(apartamento__edificio_id__in=edificios)
    
#============================= MENSUALIDADES =============================
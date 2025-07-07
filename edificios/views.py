from django.shortcuts import render

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Edificio
from .serializers import EdificioListSerializer, EdificioDetailSerializer, EdificioCrearEditarSerializer
from .permisos import EsSuperuser

from .models_apartamentos import Apartamento
from .serializers_apartamentos import ApartamentoSerializer

# Listar edificios (SuperUser/Arrendador)
class ListaEdificiosAPIView(generics.ListAPIView):
    serializer_class = EdificioListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Edificio.objects.all()
        elif user.tipo_usuario == 'arrendador':
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            return Edificio.objects.filter(id__in=edificios_ids)
        # Arrendatarios no pueden ver lista de edificios
        return Edificio.objects.none()

# Detalle edificio (todos pueden ver)
class DetalleEdificioAPIView(generics.RetrieveAPIView):
    serializer_class = EdificioDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Edificio.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Edificio.objects.all()
        elif user.tipo_usuario == 'arrendador':
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            return Edificio.objects.filter(id__in=edificios_ids)
        elif user.tipo_usuario == 'arrendatario':
            # Importar aquí para evitar circular imports
            from contratos.models import Contrato
            contratos = Contrato.objects.filter(arrendatario=user)
            edificios_ids = contratos.values_list('apartamento__edificio_id', flat=True)
            return Edificio.objects.filter(id__in=edificios_ids)
        return Edificio.objects.none()

# Crear edificio (solo superuser)
class CrearEdificioAPIView(generics.CreateAPIView):
    permission_classes = [EsSuperuser]
    serializer_class = EdificioCrearEditarSerializer
    queryset = Edificio.objects.all()

# Actualizar edificio (solo superuser)
class ActualizarEdificioAPIView(generics.UpdateAPIView):
    serializer_class = EdificioCrearEditarSerializer
    permission_classes = [EsSuperuser]
    queryset = Edificio.objects.all()

# Eliminar edificio (solo superuser)
class EliminarEdificioAPIView(generics.DestroyAPIView):
    permission_classes = [EsSuperuser]
    queryset = Edificio.objects.all()

from django.shortcuts import render

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Contrato
from .serializers_contratos import ContratoSerializer
from .filters import ContratosFilter

from .models_mensualidades import Mensualidad
from .serializers_mensualidades import MensualidadSerializer
from .filters import MensualidadFilter

from django_filters.rest_framework import DjangoFilterBackend

class ListaContratosAPIView(generics.ListAPIView):
    serializer_class = ContratoSerializer 
    permission_classes = [IsAuthenticated]

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

class ListaMensualidadesAPIView(generics.ListAPIView):
    serializer_class = MensualidadSerializer
    permission_classes = [IsAuthenticated]

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
# Create your views here.

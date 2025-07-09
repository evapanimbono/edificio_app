from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.renderers import JSONRenderer
from rest_framework import generics,filters
from rest_framework.permissions import IsAdminUser,IsAuthenticated

from .models import LogAccion
from .serializers import LogAccionesSerializer
from .filters import LogAccionesFilter

from usuarios.permissions import EsArrendador 

class ListaLogAccionesAPIView(generics.ListAPIView):
    queryset = LogAccion.objects.all()
    serializer_class = LogAccionesSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = LogAccionesFilter
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticated, EsArrendador | IsAdminUser]
    ordering_fields = ['fecha']

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return LogAccion.objects.all()

        elif user.tipo_usuario == 'arrendador':
            # 1. Obtener los usuarios que pertenecen a los edificios que el arrendador administra o colabora
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
        
            # 2. Obtener IDs de usuarios (arrendadores y arrendatarios) de esos edificios
            from usuarios.models import UsuarioEdificio
            usuarios_ids = UsuarioEdificio.objects.filter(
                edificio_id__in=edificios_ids
            ).values_list('usuario_id', flat=True)

            return LogAccion.objects.filter(usuario_id__in=usuarios_ids)

        return LogAccion.objects.none()

class DetalleLogAccionAPIView(generics.RetrieveAPIView):
    queryset = LogAccion.objects.all()
    serializer_class = LogAccionesSerializer
    permission_classes = [IsAuthenticated, EsArrendador | IsAdminUser]

# Create your views here.

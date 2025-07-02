from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.permissions import IsAuthenticated
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from .models import GastoExtra
from contratos.models import Contrato
from .serializers import GastoExtraSerializer
from .filters import GastoExtraFilter
from log.models import LogAccion
from usuarios.permissions import EsArrendador

from pagos.tareas import crear_recibo_para_gasto_extra

class ListaGastosExtraAPIView(generics.ListAPIView): # Listar gastos extra según el tipo de usuario
    queryset = GastoExtra.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = GastoExtraSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = GastoExtraFilter
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        user = self.request.user
        if user.tipo_usuario == 'arrendatario':
            # Buscar apartamentos con contratos activos para este usuario
            from contratos.models import Contrato
            apartamentos_ids = Contrato.objects.filter(
                arrendatario=user, activo=True
            ).values_list('apartamento_id', flat=True)

            return GastoExtra.objects.filter(apartamento_id__in=apartamentos_ids)
        
        elif user.tipo_usuario == 'arrendador' or user.is_superuser:
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            return GastoExtra.objects.filter(apartamento__edificio_id__in=edificios_ids)
    
        return GastoExtra.objects.none()

class CrearGastoExtraAPIView(generics.CreateAPIView): # Crear un gasto extra manual
    queryset = GastoExtra.objects.all()
    serializer_class = GastoExtraSerializer
    permission_classes = [IsAuthenticated, EsArrendador]

    def perform_create(self, serializer):
        gasto = serializer.save()
        crear_recibo_para_gasto_extra(gasto, creado_por=self.request.user)

        # Log de creación
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="Creó gasto extra",
            tabla_afectada="gastos_extra",
            registro_id=gasto.id,
            descripcion=f"Gasto extra creado para apartamento {gasto.apartamento} con monto {gasto.monto_usd}"
        )
        
# Create your views here.

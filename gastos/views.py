from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView,UpdateAPIView,DestroyAPIView,GenericAPIView
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework import serializers

from .models import GastoExtra
from .serializers import GastoExtraSerializer,GastoExtraCreateSerializer,GastoExtraUpdateSerializer,GastoExtraDetailSerializer 
from .filters import GastoExtraFilter

from contratos.models import Contrato
from contratos.serializers_mensualidades import ComentarioAnulacionSerializer

from log.models import LogAccion

from usuarios.permissions import EsArrendador

from pagos.models import PagoGastoExtra

#Lista de gastos extra según el tipo de usuario (Todos)
class ListaGastosExtraAPIView(generics.ListAPIView):
    queryset = GastoExtra.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = GastoExtraSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = GastoExtraFilter
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        user = self.request.user
        
        # 🛑 Si es arrendatario, restringimos algunos filtros
        if user.tipo_usuario == 'arrendatario':
            forbidden_filters = ['apartamento', 'fecha_generacion_desde', 'fecha_generacion_hasta']
            for key in forbidden_filters:
                if key in self.request.GET:
                    raise PermissionDenied(f"No tienes permiso para filtrar por {key}.")

            from contratos.models import Contrato
            apartamentos_ids = Contrato.objects.filter(
                arrendatario=user, activo=True
            ).values_list('apartamento_id', flat=True)

            return GastoExtra.objects.filter(apartamento_id__in=apartamentos_ids)

        # ✅ Si es arrendador
        elif user.tipo_usuario == 'arrendador':
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            return GastoExtra.objects.filter(apartamento__edificio_id__in=edificios_ids)
        # ✅ Si es superusuario
        elif user.is_superuser:
            return GastoExtra.objects.all()

        return GastoExtra.objects.none()

#Vista para crear un gasto extra manual (superusuario o arrendador)
class CrearGastoExtraAPIView(generics.CreateAPIView):
    queryset = GastoExtra.objects.all()
    serializer_class = GastoExtraCreateSerializer
    permission_classes = [IsAuthenticated, EsArrendador]

    def perform_create(self, serializer):
        gasto = serializer.save()

        # Log de creación
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="Creó gasto extra",
            tabla_afectada="gastos_extra",
            registro_id=gasto.id,
            descripcion=(
                f"Gasto extra #{gasto.id} creado para apartamento {gasto.apartamento} "
                f"con monto ${gasto.monto_usd} y vencimiento {gasto.fecha_vencimiento}"
            )
        )

#Vista para ver el detalle de un gasto extra (según tipo de usuario)
class DetalleGastoExtraAPIView(RetrieveAPIView):
    queryset = GastoExtra.objects.all()
    serializer_class = GastoExtraDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        gasto = super().get_object()
        user = self.request.user

        if user.tipo_usuario == 'arrendatario':
            contrato_activo = Contrato.objects.filter(
                arrendatario=user,
                apartamento=gasto.apartamento,
                activo=True
            ).exists()
            if not contrato_activo:
                raise PermissionDenied("No tienes permiso para ver este gasto.")

        elif user.tipo_usuario == 'arrendador':
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            if gasto.apartamento.edificio_id not in edificios_ids:
                raise PermissionDenied("No tienes permiso para ver este gasto.")
        elif user.is_superuser:
            # superuser puede ver todo, no limitar
            pass
        else:
            raise PermissionDenied("No tienes permiso para ver este gasto.")

        return gasto

# Vista para actualizar un gasto extra (solo arrendador o superusuario)
class ActualizarGastoExtraAPIView(UpdateAPIView):
    queryset = GastoExtra.objects.all()
    serializer_class = GastoExtraUpdateSerializer
    permission_classes = [IsAuthenticated, EsArrendador]  # Usamos permiso que tengas para arrendador

    def perform_update(self, serializer):
        instance = serializer.save()
        user = self.request.user

        # Estado actualizado según fecha
        if instance.fecha_vencimiento:
            hoy = timezone.now().date()
            instance.estado = 'atrasado' if instance.fecha_vencimiento < hoy else 'pendiente'
            instance.save()

        # Log
        LogAccion.objects.create(
            usuario=user,
            accion="actualizó gasto extra",
            tabla_afectada="gastos_extra",
            registro_id=instance.id,
            descripcion=f"Gasto extra #{instance.id} editado para apartamento {instance.apartamento.numero_apartamento if instance.apartamento else 'desconocido'}"
        )

#Vista para anular un gasto extra si hay un pago asociado anulado (solo arrendador o superusuario)
class AnularGastoExtraAPIView(GenericAPIView):
    queryset = GastoExtra.objects.all()
    serializer_class = ComentarioAnulacionSerializer  # puedes reutilizar el mismo
    permission_classes = [IsAuthenticated, EsArrendador]

    def post(self, request, *args, **kwargs):
        gasto = self.get_object()
        self.check_object_permissions(request, gasto)

        if gasto.estado == 'pagado':
            return Response({"detail": "No se puede anular un gasto extra pagado. Primero anule el pago."}, status=400)

        if gasto.estado == 'anulado':
            return Response({"detail": "Este gasto ya está anulado."}, status=400)

        pagos_activos = gasto.pagogastoextra_set.exclude(pago__estado_validacion__in=['anulado', 'rechazado'])
        if pagos_activos.exists():
            return Response(
            {"error": "No se puede anular el gasto extra porque tiene pagos activos asociados."},
            status=400
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comentario = serializer.validated_data['comentario']

        gasto.estado = 'anulado'
        gasto.comentario_anulacion = comentario
        gasto.save()

        LogAccion.objects.create(
            usuario=request.user,
            accion="anuló gasto extra",
            tabla_afectada="gastos_extra",
            registro_id=gasto.id,
            descripcion=f"Gasto extra anulado con comentario: {comentario}"
        )

        return Response({"detail": "Gasto extra anulado correctamente."}, status=200)

# Vista para eliminar un gasto extra si no hay pago asociado (solo arrendador o superusuario) 
class EliminarGastoExtraAPIView(DestroyAPIView):
    queryset = GastoExtra.objects.all()
    permission_classes = [IsAuthenticated, EsArrendador]

    def perform_destroy(self, instance):
        user = self.request.user

        # 🚨 Verificar que el gasto esté anulado
        if instance.estado != 'anulado':
            raise ValidationError("Solo se pueden eliminar gastos extras anulados.")
        
        # 🚨 Verificar si tiene pagos pendientes o validados asociados
        pagos_activos = PagoGastoExtra.objects.filter(
            gasto_extra=instance,
            pago__estado_validacion__in=['pendiente', 'validado']
        ).exists()
        if pagos_activos:
            raise ValidationError("No se puede eliminar este gasto extra porque tiene pagos activos asociados.")

        # 🗑️ Eliminar el gasto extra
        gasto_id = instance.id
        apartamento = instance.apartamento
        instance.delete()

        # 📝 Log
        LogAccion.objects.create(
            usuario=user,
            accion="eliminó gasto extra",
            tabla_afectada="gastos_extra",
            registro_id=gasto_id,
            descripcion=f"Eliminó el gasto extra #{gasto_id} del apartamento {apartamento.numero_apartamento if apartamento else 'desconocido'}"
        )

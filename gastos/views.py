from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView,UpdateAPIView,DestroyAPIView
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework import serializers

from .models import GastoExtra
from .serializers import GastoExtraSerializer,GastoExtraCreateSerializer,GastoExtraUpdateSerializer
from .filters import GastoExtraFilter

from contratos.models import Contrato

from log.models import LogAccion

from usuarios.permissions import EsArrendador

from pagos.models import PagoGastoExtra
from pagos.tareas import crear_recibo_para_gasto_extra

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

        # ✅ Si es arrendador o superusuario
        elif user.tipo_usuario == 'arrendador' or user.is_superuser:
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            return GastoExtra.objects.filter(apartamento__edificio_id__in=edificios_ids)

        return GastoExtra.objects.none()

#Vista para crear un gasto extra manual (superusuario o arrendador)
class CrearGastoExtraAPIView(generics.CreateAPIView):
    queryset = GastoExtra.objects.all()
    serializer_class = GastoExtraCreateSerializer
    permission_classes = [IsAuthenticated, EsArrendador]

    def perform_create(self, serializer):
        gasto = serializer.save()
        recibo = crear_recibo_para_gasto_extra(gasto, creado_por=self.request.user)
        if not recibo:
            raise serializers.ValidationError("No se pudo crear recibo para el gasto extra. Verifique que el apartamento tenga contrato activo.")

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
    serializer_class = GastoExtraSerializer
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

        elif user.tipo_usuario == 'arrendador' or user.is_superuser:
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            if gasto.apartamento.edificio_id not in edificios_ids:
                raise PermissionDenied("No tienes permiso para ver este gasto.")
        else:
            raise PermissionDenied("No tienes permiso para ver este gasto.")

        return gasto

# Vista para actualizar un gasto extra (solo arrendador o superusuario)
class ActualizarGastoExtraAPIView(UpdateAPIView):
    queryset = GastoExtra.objects.all()
    serializer_class = GastoExtraUpdateSerializer
    permission_classes = [IsAuthenticated, EsArrendador]  # Usamos permiso que tengas para arrendador

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        # Verificar si ya hay pagos asociados al gasto extra
        from pagos.models import PagoGastoExtra

        if PagoGastoExtra.objects.filter(gasto_extra=instance).exists():
            raise PermissionDenied("No se puede editar un gasto que ya tiene pagos asociados.")

        instance = serializer.save()

        # Estado actualizado según fecha
        if instance.fecha_vencimiento:
            hoy = timezone.now().date()
            instance.estado = 'atrasado' if instance.fecha_vencimiento < hoy else 'pendiente'
            instance.save()

        # Actualizar recibo asociado aunque no haya cambios explícitos en monto o vencimiento
        instance.actualizar_recibo()

        # Log
        LogAccion.objects.create(
            usuario=user,
            accion="actualizó gasto extra",
            tabla_afectada="gastos_extra",
            registro_id=instance.id,
            descripcion=f"Gasto extra #{instance.id} editado para apartamento {instance.apartamento.numero_apartamento if instance.apartamento else 'desconocido'}"
        )

# Vista para eliminar un gasto extra (solo arrendador o superusuario)
class EliminarGastoExtraAPIView(DestroyAPIView):
    queryset = GastoExtra.objects.all()
    permission_classes = [IsAuthenticated, EsArrendador]

    def perform_destroy(self, instance):
        user = self.request.user

        # 🚨 Verificar si el gasto está en estado pagado
        if instance.estado == 'pagado':
            raise ValidationError("Este gasto extra no puede eliminarse porque ya está marcado como pagado.")

        # 🚨 También verificar si hay pagos registrados explícitamente
        pagos_asociados = PagoGastoExtra.objects.filter(gasto_extra=instance).exists()
        if pagos_asociados:
            raise ValidationError("Este gasto extra no puede eliminarse porque tiene pagos registrados.")

        # 🧹 Eliminar recibo y vínculo ReciboGastoExtra si existen
        instance.eliminar_recibo_vinculado()

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

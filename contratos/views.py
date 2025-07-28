from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import PermissionDenied, ValidationError

from rest_framework import generics,status
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Contrato
from .serializers_contratos import ContratoSerializer
from .filters import ContratosFilter, MensualidadFilter

from .models_mensualidades import Mensualidad
from .serializers_mensualidades import MensualidadSerializer, MensualidadCrearSerializer, MensualidadEditarSerializer, ComentarioAnulacionSerializer
from .filters import MensualidadFilter

from pagos.models_recibos import ReciboMensualidad

from log.models import LogAccion

from .permisos import(
    PuedeModificarOMostrarMensualidad,
    PuedeEliminarMensualidad,
    EsArrendadorYAdministraLaMensualidad,
    PuedeAnularMensualidad
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
        
        contrato = serializer.save()

        LogAccion.objects.create(
            usuario=usuario,
            accion="creó contrato",
            tabla_afectada="Contrato",
            registro_id=contrato.id,
            descripcion=f"Contrato #{contrato.id} creado para arrendatario {contrato.arrendatario.username} en apartamento {contrato.apartamento.numero_apartamento}."
        )

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
    
    def perform_update(self, serializer):
        contrato = serializer.save()

        LogAccion.objects.create(
            usuario=self.request.user,
            accion="actualizó contrato",
            tabla_afectada="Contrato",
            registro_id=contrato.id,
            descripcion=f"Contrato #{contrato.id} actualizado."
        )

    def perform_destroy(self, instance):
        contrato_id = instance.id
        instance.delete()

        LogAccion.objects.create(
            usuario=self.request.user,
            accion="eliminó contrato",
            tabla_afectada="Contrato",
            registro_id=contrato_id,
            descripcion=f"Contrato #{contrato_id} eliminado."
        )

#============================= MENSUALIDADES =============================
#Vista para ver detalle de una mensualidad, accesible por arrendador, arrendatario o superusuario
class DetalleMensualidadAPIView(generics.RetrieveAPIView):
    queryset = Mensualidad.objects.all()
    serializer_class = MensualidadSerializer
    permission_classes = [IsAuthenticated, PuedeModificarOMostrarMensualidad]

#Vista para crear mensualidad, accesible por superusuario
class CrearMensualidadAPIView(generics.CreateAPIView):
    queryset = Mensualidad.objects.all()
    serializer_class = MensualidadCrearSerializer
    permission_classes = [IsAdminUser]

#Vista para modificar una mensualidad, accesible por arrendador o superusuario (solo campo fecha_vencimiento)
class ActualizarMensualidadAPIView(generics.UpdateAPIView):
    queryset = Mensualidad.objects.all()
    serializer_class = MensualidadEditarSerializer
    permission_classes = [IsAuthenticated, PuedeModificarOMostrarMensualidad]
    
    def get_object(self):
        obj = super().get_object()
        # Forzar chequeo explícito del permiso de objeto
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_update(self, serializer):
        mensualidad = serializer.save()
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="actualizó mensualidad",
            tabla_afectada="Mensualidad",
            registro_id=mensualidad.id,
            descripcion=f"Mensualidad #{mensualidad.id} actualizada. Nueva fecha vencimiento: {mensualidad.fecha_vencimiento}."
        )

#Vista para eliminar una mensualidad, accesible por arrendador o superusuario (sin pagos asociados)
class EliminarMensualidadAPIView(generics.DestroyAPIView):
    queryset = Mensualidad.objects.all()
    permission_classes = [PuedeEliminarMensualidad]

    def perform_destroy(self, instance):
        usuario = self.request.user

        # Verificar que la mensualidad esté anulada
        if instance.estado != 'anulado':
            raise ValidationError("Solo se pueden eliminar mensualidades anuladas.")

        # Verificar que no tenga pagos pendientes o validados asociados
        pagos_activos = instance.pagomensualidad_set.filter(pago__estado_validacion__in=['pendiente', 'validado']).exists()
        if pagos_activos:
            raise ValidationError("No se puede eliminar esta mensualidad porque tiene pagos activos asociados.")

        descripcion = f"Eliminó mensualidad ID {instance.id} del contrato ID {instance.contrato_id}"

        # Log
        LogAccion.objects.create(
            usuario=usuario,
            accion='eliminar',
            tabla_afectada='Mensualidad',
            descripcion=descripcion
        )

        instance.delete()

# Vista para anular una mensualidad con pagos, accesible por arrendador o superusuario
class AnularMensualidadAPIView(generics.GenericAPIView):
    queryset = Mensualidad.objects.all()
    serializer_class = ComentarioAnulacionSerializer
    permission_classes = [PuedeAnularMensualidad]

    def post(self, request, *args, **kwargs):
        mensualidad = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comentario = serializer.validated_data.get("comentario", "").strip()

        if mensualidad.estado == 'anulado':
            raise ValidationError("La mensualidad ya está anulada.")
        
        if mensualidad.estado == 'pagado':
            raise ValidationError("No se puede anular una mensualidad pagada. Anule el pago primero.")

        pagos_activos = mensualidad.pagomensualidad_set.exclude(pago__estado_validacion__in=['anulado', 'rechazado'])
        if pagos_activos.exists():
           return Response(
            {"error": "No se puede anular la mensualidad porque tiene pagos activos asociados."},
            status=400
            )

        if not comentario:
            raise ValidationError("Debe proporcionar un comentario para anular la mensualidad.")

        # Aquí marcas la mensualidad como anulada
        mensualidad.estado = 'anulado'
        mensualidad.comentario_anulacion = comentario
        mensualidad.save()

        # Registrar log
        LogAccion.objects.create(
            usuario=request.user,
            accion="anuló mensualidad",
            tabla_afectada="Mensualidad",
            registro_id=mensualidad.id,
            descripcion=f"Mensualidad #{mensualidad.id} anulada. Comentario: {comentario}"
        )

        return Response({"detail": "Mensualidad anulada correctamente."}, status=status.HTTP_200_OK)


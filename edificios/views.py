from django.shortcuts import render
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Edificio
from .serializers import (
    EdificioListSerializer,
    EdificioDetailSerializer,
    EdificioCrearEditarSerializer
)    
from .permisos import EsSuperuser
from .filters import EdificioFilter

from .models_apartamentos import Apartamento
from .serializers_apartamentos import (
    ApartamentoListSerializer,
    ApartamentoDetailSerializer,
    ApartamentoCrearEditarSerializer
)

from log.models import LogAccion


#========================================= EDIFICIOS =========================================
# Listar edificios (SuperUser/Arrendador)
class ListaEdificiosAPIView(generics.ListAPIView):
    serializer_class = EdificioListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EdificioFilter

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
    
    def perform_create(self, serializer):
        edificio = serializer.save()
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="creó edificio",
            tabla_afectada="Edificio",
            registro_id=edificio.id,
            descripcion=f"Edificio #{edificio.id} '{edificio.nombre}' creado."
        )

# Actualizar edificio (solo superuser)
class ActualizarEdificioAPIView(generics.UpdateAPIView):
    serializer_class = EdificioCrearEditarSerializer
    permission_classes = [EsSuperuser]
    queryset = Edificio.objects.all()

    def perform_update(self, serializer):
        edificio = serializer.save()
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="actualizó edificio",
            tabla_afectada="Edificio",
            registro_id=edificio.id,
            descripcion=f"Edificio #{edificio.id} '{edificio.nombre}' actualizado."
        )

# Eliminar edificio (solo superuser)
class EliminarEdificioAPIView(generics.DestroyAPIView):
    permission_classes = [EsSuperuser]
    queryset = Edificio.objects.all()

    def perform_destroy(self, instance):
        if instance.usuarios_asignados.exists():
            raise ValidationError("No se puede eliminar el edificio porque aún tiene usuarios asignados.")
        if instance.apartamento_set.exists():
            raise ValidationError("No se puede eliminar el edificio porque tiene apartamentos asociados.")

        log_descripcion = f"Edificio #{instance.id} '{instance.nombre}' eliminado."
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="eliminó edificio",
            tabla_afectada="Edificio",
            registro_id=instance.id,
            descripcion=log_descripcion
        )
        instance.delete()

#========================================= APARTAMENTOS =========================================
# Listar apartamentos (Superuser / Arrendador)
class ListaApartamentosAPIView(generics.ListAPIView):
    serializer_class = ApartamentoListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Apartamento.objects.all()
        elif user.tipo_usuario == 'arrendador':
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            return Apartamento.objects.filter(edificio_id__in=edificios_ids)
        # Arrendatarios no tienen lista de apartamentos
        return Apartamento.objects.none()

# Detalle apartamento (todos)
class DetalleApartamentoAPIView(generics.RetrieveAPIView):
    serializer_class = ApartamentoDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Apartamento.objects.all()
        elif user.tipo_usuario == 'arrendador':
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            return Apartamento.objects.filter(edificio_id__in=edificios_ids)
        elif user.tipo_usuario == 'arrendatario':
            # Obtener apartamentos relacionados al arrendatario via contratos
            from contratos.models import Contrato
            contratos = Contrato.objects.filter(arrendatario=user)
            apartamentos_ids = contratos.values_list('apartamento_id', flat=True)
            return Apartamento.objects.filter(id__in=apartamentos_ids)
        return Apartamento.objects.none()

# Crear apartamento (superuser y arrendador)
class CrearApartamentoAPIView(generics.CreateAPIView):
    serializer_class = ApartamentoCrearEditarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or user.tipo_usuario == 'arrendador'):
            raise ValidationError("No tienes permiso para crear apartamentos.")
        # Para arrendador, validar que el apartamento sea de un edificio que administra
        if user.tipo_usuario == 'arrendador':
            edificio = serializer.validated_data.get('edificio')
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            if edificio.id not in edificios_ids:
                raise ValidationError("No puedes crear apartamentos en edificios que no administras.")

        apartamento = serializer.save()

        # Log de creación
        LogAccion.objects.create(
            usuario=user,
            accion="creó apartamento",
            tabla_afectada="Apartamento",
            registro_id=apartamento.id,
            descripcion=f"Apartamento #{apartamento.id} creado en edificio '{apartamento.edificio.nombre}'"
        )

# Actualizar apartamento (superuser y arrendador)
class ActualizarApartamentoAPIView(generics.UpdateAPIView):
    serializer_class = ApartamentoCrearEditarSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Apartamento.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Apartamento.objects.all()
        elif user.tipo_usuario == 'arrendador':
            edificios_ids = user.edificios_asignados.values_list('edificio_id', flat=True)
            return Apartamento.objects.filter(edificio_id__in=edificios_ids)
        return Apartamento.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        apartamento = serializer.save()

        # Log de actualización
        LogAccion.objects.create(
            usuario=user,
            accion="actualizó apartamento",
            tabla_afectada="Apartamento",
            registro_id=apartamento.id,
            descripcion=f"Apartamento #{apartamento.id} actualizado en edificio '{apartamento.edificio.nombre}'"
        )

# Eliminar apartamento (solo superuser)
class EliminarApartamentoAPIView(generics.DestroyAPIView):
    permission_classes = [EsSuperuser]
    queryset = Apartamento.objects.all()

    def perform_destroy(self, instance):
        # Opcional: validar que no tenga contratos o pagos asociados (por simplicidad aquí no se hace)
        nombre = instance.numero_apartamento
        edificio_nombre = instance.edificio.nombre
        instance.delete()

        # Log de eliminación
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="eliminó apartamento",
            tabla_afectada="Apartamento",
            registro_id=instance.id,
            descripcion=f"Apartamento #{instance.id} '{nombre}' del edificio '{edificio_nombre}' eliminado."
        )
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, status
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .permissions import EsArrendador
from .models import(
    UsuarioEdificio,
    SolicitudUsuarioEdificio,
) 
from .serializers_solicitudes import (
    CrearSolicitudUsuarioEdificioSerializer,
    DetalleSolicitudUsuarioEdificioSerializer,
    ValidarSolicitudUsuarioEdificioSerializer
)
from .filters import SolicitudUsuarioEdificioFilter

from log.models import LogAccion

#Enviar solicitud para vincularse a un edificio (usuario)
class SolicitarVinculacionAPIView(generics.CreateAPIView):
    queryset = SolicitudUsuarioEdificio.objects.all()
    serializer_class = CrearSolicitudUsuarioEdificioSerializer
    permission_classes = [IsAuthenticated]

#Validar o rechazar solicitudes de vinculacion (superuser o arrendador)
class ValidarSolicitudAPIView(generics.UpdateAPIView):
    queryset = SolicitudUsuarioEdificio.objects.all()
    serializer_class = ValidarSolicitudUsuarioEdificioSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        solicitud = self.get_object()

        # Verificar permisos de validación
        if solicitud.tipo_solicitado == 'arrendador' and not request.user.is_superuser:
            return Response({'error': 'Solo el superusuario puede validar solicitudes de arrendadores.'}, status=403)

        if solicitud.tipo_solicitado == 'arrendatario' and not (
            request.user.is_superuser or
            request.user.tipo_usuario == 'arrendador' and
            solicitud.edificio in [rel.edificio for rel in request.user.edificios_asignados.all()]
        ):
            return Response({'error': 'No tiene permisos para validar esta solicitud de arrendatario.'}, status=403)
        
        if solicitud.estado != 'pendiente':
            return Response({'error': 'Esta solicitud ya fue procesada.'}, status=400)

        serializer = self.get_serializer(solicitud, data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Nuevo: uso del campo aprobado
        if data['aprobado']:
            solicitud.estado = 'aprobado'
        else:
            solicitud.estado = 'rechazado'

        solicitud.comentario_validador = data.get('comentario_validador')
        solicitud.save()

        # Asignación si fue aprobada
        if solicitud.estado == 'aprobado':
            solicitud.usuario.tipo_usuario = solicitud.tipo_solicitado
            solicitud.usuario.estado = 'activo'

            if solicitud.tipo_solicitado == 'arrendador':
                solicitud.usuario.is_staff = True
                from usuarios.models import UsuarioEdificio
                UsuarioEdificio.objects.create(
                    usuario=solicitud.usuario,
                    edificio=solicitud.edificio,
                    rol=data['rol_asignado'],
                    fecha_asignacion=timezone.now().date()
                )

                LogAccion.objects.create(
                    usuario=request.user,
                    accion="Aprobó solicitud de usuario",
                    tabla_afectada="solicitudes_usuario_edificio",
                    registro_id=solicitud.id,
                    descripcion=f"Solicitud de {solicitud.usuario.username} aprobada como {solicitud.tipo_solicitado} en {solicitud.edificio} por {request.user.username}"
                )

            solicitud.usuario.save()    

        # Si fue rechazada, registrar log
        if solicitud.estado == 'rechazado':
            solicitud.usuario.estado = 'rechazado'  # O el valor que uses para marcado
            solicitud.usuario.save()

            LogAccion.objects.create(
                usuario=request.user,
                accion="Rechazó solicitud de usuario",
                tabla_afectada="solicitudes_usuario_edificio",
                registro_id=solicitud.id,
                descripcion=f"Solicitud de {solicitud.usuario.username} fue rechazada por {request.user.username}. Comentario: {solicitud.comentario_validador or 'Sin comentario'}"
            )

        return Response({'mensaje': f'Solicitud {solicitud.estado} correctamente.'})          

#Ver solicitudes pendientes para vincular (superuser o arrendador)
class ListarSolicitudesPendientesAPIView(generics.ListAPIView):
    serializer_class = DetalleSolicitudUsuarioEdificioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user

        if usuario.is_superuser:
            return SolicitudUsuarioEdificio.objects.filter(estado='pendiente')

        if usuario.tipo_usuario == 'arrendador':
            edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)
            return SolicitudUsuarioEdificio.objects.filter(
                estado='pendiente',
                edificio_id__in=edificios_ids,
                tipo_solicitado='arrendatario'
            )

        return SolicitudUsuarioEdificio.objects.none()  

#Ver un listado de todas las solicitudes con opcion a filtrar por:estado, tipo de usuario solicitado, edificio, usuario (superuser)
class HistorialSolicitudesAPIView(generics.ListAPIView):
    serializer_class = DetalleSolicitudUsuarioEdificioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SolicitudUsuarioEdificioFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('estado', openapi.IN_QUERY, description="Estado de la solicitud", type=openapi.TYPE_STRING),
        openapi.Parameter('tipo_solicitado', openapi.IN_QUERY, description="Tipo solicitado", type=openapi.TYPE_STRING),
        openapi.Parameter('edificio_id', openapi.IN_QUERY, description="ID edificio", type=openapi.TYPE_INTEGER),
        openapi.Parameter('fecha_creacion_after', openapi.IN_QUERY, description="Fecha creación desde (YYYY-MM-DD)", type=openapi.TYPE_STRING, format='date'),
        openapi.Parameter('fecha_creacion_before', openapi.IN_QUERY, description="Fecha creación hasta (YYYY-MM-DD)", type=openapi.TYPE_STRING, format='date'),
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        usuario = self.request.user
        if usuario.is_superuser:
            return SolicitudUsuarioEdificio.objects.all()
        return SolicitudUsuarioEdificio.objects.filter(usuario=usuario)
  
#===================== ARRENDADOR ======================= 
#Ver un listado de todas las solicitudes de arrendatarios con opcion a filtrar por:estado, tipo de usuario solicitado, edificio, usuario (superuser)
class SolicitudesEdificiosArrendadorAPIView(generics.ListAPIView):
    serializer_class = DetalleSolicitudUsuarioEdificioSerializer
    permission_classes = [IsAuthenticated, EsArrendador]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SolicitudUsuarioEdificioFilter
    ordering_fields = ['created_at']

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('estado', openapi.IN_QUERY, description="Estado de la solicitud", type=openapi.TYPE_STRING),
        openapi.Parameter('edificio_id', openapi.IN_QUERY, description="ID del edificio", type=openapi.TYPE_INTEGER),
        openapi.Parameter('fecha_creacion_after', openapi.IN_QUERY, description="Desde (YYYY-MM-DD)", type=openapi.TYPE_STRING, format='date'),
        openapi.Parameter('fecha_creacion_before', openapi.IN_QUERY, description="Hasta (YYYY-MM-DD)", type=openapi.TYPE_STRING, format='date'),
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        usuario = self.request.user
        edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)
        return SolicitudUsuarioEdificio.objects.filter(
            edificio_id__in=edificios_ids,
            tipo_solicitado='arrendatario'  # 👈 clave: solo solicitudes de arrendatarios
        )
    
    


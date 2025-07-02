from django_filters.rest_framework import DjangoFilterBackend

from django.template.loader import render_to_string
from django.shortcuts import render
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_str
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response

from log.models import LogAccion

from .permissions import EsArrendador
from .models import Usuario
from .models_usuario_edificio import UsuarioEdificio
from .filters import (
    UsuarioEdificioFilter,
    UsuarioAsignadoFilter  
)    
from .serializers import (
    UsuarioSerializer,
    AdminEditarUsuarioSerializer,
    RegistroUsuarioSerializer,
    EditarPerfilSerializer,
    PerfilUsuarioSerializer,
    UsuarioListSerializer,
    UsuarioBasicoSerializer,
    UsuarioEdificioSerializer,
    AdminAsociarUsuarioEdificioSerializer,
    ActivarDesactivarUsuarioSerializer,
    ArrendadorActivarDesactivarUsuarioSerializer,
    SolicitarCambioCorreoSerializer,
)    

#===================== SUPERUSER =========================
#Lista general de usuarios (superuser)
class ListaUsuariosAPIView(generics.ListAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioListSerializer  # Usa uno reducido para no devolver todo
    permission_classes = [IsAuthenticated, IsAdminUser] # Solo superusuario puede ver

#Detalle de usuario(superuser)
class DetalleUsuarioAPIView(generics.RetrieveAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAdminUser]  # Solo superusuario

#Vista para editar cargos (tipo_usuario,estado,is_active,is_staff) (superuser)
class AdminEditarUsuarioAPIView(generics.UpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = AdminEditarUsuarioSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'  # se usará /usuarios/admin/<id>/ para acceder

    def perform_update(self, serializer):
        usuario = self.get_object()
        serializer.save()

        LogAccion.objects.create(
            usuario=self.request.user,
            accion="Editó usuario",
            tabla_afectada="usuarios",
            registro_id=usuario.id,
            descripcion=f"Usuario {usuario.username} fue editado por {self.request.user.username}. Campos actualizados: {list(serializer.validated_data.keys())}"
        )

#Vista para activar/desactivar un usuario (superuser)
class ActivarDesactivarUsuarioAPIView(generics.UpdateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = ActivarDesactivarUsuarioSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'  # Usaremos /usuarios/admin/<id>/activar-desactivar/

    def perform_update(self, serializer):
        usuario = self.get_object()
        serializer.save()
    
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="Activó/Desactivó usuario",
            tabla_afectada="usuarios",
            registro_id=usuario.id,
            descripcion=f"Usuario {usuario.username} fue {'activado' if usuario.is_active else 'desactivado'} por {self.request.user.username}."
        )

#Eliminar un usuario (superuser)
class EliminarUsuarioAPIView(generics.DestroyAPIView):
    queryset = Usuario.objects.all()
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="Eliminó usuario",
            tabla_afectada="usuarios",
            registro_id=instance.id,
            descripcion=f"El usuario {instance.username} fue eliminado por {self.request.user.username}"
        )
        instance.delete()

#Lista de usuarios y sus asociaciones a edificios (superuser)
class ListaAsociacionesUsuarioEdificioAPIView(generics.ListAPIView):
    queryset = UsuarioEdificio.objects.all()
    serializer_class = UsuarioEdificioSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UsuarioEdificioFilter

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('usuario_id', openapi.IN_QUERY, description="ID del usuario", type=openapi.TYPE_INTEGER),
        openapi.Parameter('edificio_id', openapi.IN_QUERY, description="ID del edificio", type=openapi.TYPE_INTEGER),
        openapi.Parameter('rol', openapi.IN_QUERY, description="Rol asignado", type=openapi.TYPE_STRING),
        openapi.Parameter('fecha_asignacion_after', openapi.IN_QUERY, description="Desde (YYYY-MM-DD)", type=openapi.TYPE_STRING, format='date'),
        openapi.Parameter('fecha_asignacion_before', openapi.IN_QUERY, description="Hasta (YYYY-MM-DD)", type=openapi.TYPE_STRING, format='date'),
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

#Vista para asociar manualmente un usuario a un edificio (superuser)
class AdminAsociarUsuarioEdificioAPIView(generics.CreateAPIView):
    queryset = UsuarioEdificio.objects.all()
    serializer_class = AdminAsociarUsuarioEdificioSerializer
    permission_classes = [permissions.IsAdminUser]     

    def perform_create(self, serializer):
        asociacion = serializer.save()

        LogAccion.objects.create(
            usuario=self.request.user,
            accion="Asoció usuario a edificio",
            tabla_afectada="usuarios_usuarioedificio",
            registro_id=asociacion.id,
            descripcion=f"Usuario {asociacion.usuario.username} asociado al edificio {asociacion.edificio.nombre} con rol {asociacion.rol} por {self.request.user.username}."
        )     

#Eliminar la asociacion de un usuario a un edificio (superuser)    
class EliminarAsociacionUsuarioEdificioAPIView(generics.DestroyAPIView):
    queryset = UsuarioEdificio.objects.all()
    serializer_class = UsuarioEdificioSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'pk'    

    def perform_destroy(self, instance):
        LogAccion.objects.create(
            usuario=self.request.user,
            accion="Eliminó asociación usuario-edificio",
            tabla_afectada="usuarios_usuarioedificio",
            registro_id=instance.id,
            descripcion=f"Se eliminó la asociación del usuario {instance.usuario.username} con el edificio {instance.edificio.nombre}"
        )
        instance.delete()

    
#===================== ARRENDADOR =========================
#Lista general de usuarios asignados a edificios (arrendador)  
class UsuariosAsignadosAPIView(generics.ListAPIView):
    serializer_class = UsuarioBasicoSerializer
    permission_classes = [IsAuthenticated, EsArrendador]  # Usa tu permiso personalizado
    filter_backends = [DjangoFilterBackend]
    filterset_class = UsuarioAsignadoFilter

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('username', openapi.IN_QUERY, description="Username (contiene)", type=openapi.TYPE_STRING),
        openapi.Parameter('correo', openapi.IN_QUERY, description="Correo (contiene)", type=openapi.TYPE_STRING),
        openapi.Parameter('estado', openapi.IN_QUERY, description="Estado (ej: activo)", type=openapi.TYPE_STRING),
    ])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        usuario = self.request.user

        # Obtener edificios donde el arrendador está asignado
        edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)

        # Obtener arrendatarios que tienen apartamentos en esos edificios
        from contratos.models import Contrato  # Ajusta según tu estructura
        usuarios_ids = Contrato.objects.filter(
            apartamento__edificio_id__in=edificios_ids,
            activo=True
        ).values_list('usuario_id', flat=True).distinct()

        return Usuario.objects.filter(id__in=usuarios_ids)

#Vista para activar/desactivar un arrendatario asociado a un edificio
class ArrendadorActivarDesactivarArrendatarioAPIView(generics.UpdateAPIView):
    serializer_class = ArrendadorActivarDesactivarUsuarioSerializer
    permission_classes = [IsAuthenticated, EsArrendador]
    queryset = Usuario.objects.filter(tipo_usuario='arrendatario')  # Solo arrendatarios
    lookup_field = 'pk'  # /usuarios/arrendador/<id>/activar-desactivar/

    def get_queryset(self):
        usuario = self.request.user
        edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)

        # Solo usuarios con contratos activos en edificios que administra
        from contratos.models import Contrato
        usuarios_ids = Contrato.objects.filter(
            apartamento__edificio_id__in=edificios_ids,
            activo=True
        ).values_list('usuario_id', flat=True)

        return Usuario.objects.filter(id__in=usuarios_ids, tipo_usuario='arrendatario')

    def perform_update(self, serializer):
        usuario_editado = self.get_object()
        serializer.save()

        LogAccion.objects.create(
            usuario=self.request.user,
            accion="Activó/desactivó arrendatario",
            tabla_afectada="usuarios",
            registro_id=usuario_editado.id,
            descripcion=f"El usuario {usuario_editado.username} fue {'activado' if usuario_editado.is_active else 'desactivado'} por {self.request.user.username}"
        )

#Vista de detalle de arrendatario asociado a edificio que administra
class DetalleUsuarioAsignadoAPIView(generics.RetrieveAPIView):
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [IsAuthenticated, EsArrendador]
    lookup_field = 'pk'  # accede con /usuarios/asignados/<id>/

    def get_queryset(self):
        usuario = self.request.user
        edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)

        # Usuarios arrendatarios activos con contratos en esos edificios
        from contratos.models import Contrato
        usuarios_ids = Contrato.objects.filter(
            apartamento__edificio_id__in=edificios_ids,
            activo=True
        ).values_list('usuario_id', flat=True)

        return Usuario.objects.filter(id__in=usuarios_ids)

#===================== ARRENDATARIO =======================
#Registro general de usuario (publica)
class RegistroUsuarioAPIView(generics.CreateAPIView):
    serializer_class = RegistroUsuarioSerializer 

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context   

#Vista para validar correo con Token
class VerificarCorreoAPIView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            from usuarios.models import Usuario
            usuario = Usuario.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return Response({"error": "Enlace inválido."}, status=400)

        if default_token_generator.check_token(usuario, token):
            usuario.is_active = True
            usuario.estado = 'activo'
            usuario.save()

            LogAccion.objects.create(
                usuario=usuario,
                accion="Verificó correo electrónico",
                tabla_afectada="usuarios",
                registro_id=usuario.id,
                descripcion=f"Correo verificado y cuenta activada para {usuario.username}."
            )
            
            return Response({"mensaje": "Correo verificado correctamente. Ya puedes iniciar sesión."})
        else:
            return Response({"error": "Token inválido o expirado."}, status=400)

#Ver perfil propio (usuario)
class PerfilUsuarioAPIView(generics.RetrieveAPIView):
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

#Editar perfil propio (usuario)
class EditarPerfilAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = EditarPerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Retorna el usuario autenticado
        return self.request.user  
    
    def perform_update(self, serializer):
        usuario = self.get_object()
        serializer.save()

        LogAccion.objects.create(
            usuario=usuario,
            accion="Editó su perfil",
            tabla_afectada="usuarios",
            registro_id=usuario.id,
            descripcion=f"Usuario {usuario.username} editó su perfil."
        )
    
#Vista para solicitar cambio de correo (usuario)
class SolicitarCambioCorreoAPIView(generics.UpdateAPIView):
    serializer_class = SolicitarCambioCorreoSerializer  # lo creamos abajo
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Usuario.objects.filter(pk=self.request.user.pk)
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        nuevo_correo = serializer.validated_data['nuevo_correo']

        user = request.user
        user.nuevo_correo = nuevo_correo
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        path = reverse('confirmar-cambio-correo', kwargs={'uidb64': uid, 'token': token})
        url = request.build_absolute_uri(path)

        # Personalizar el email con plantilla HTML
        html_message = render_to_string('emails/confirmar_correo.html', {
            'usuario': user,
            'url': url,
            'nuevo_correo': nuevo_correo,
        })

        send_mail(
            subject='Confirma tu nuevo correo electrónico',
            message=f'Haz clic en este enlace para confirmar tu nuevo correo: {url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[nuevo_correo],
            fail_silently=False,
            html_message=html_message
        )

        LogAccion.objects.create(
            usuario=user,
            accion="Solicitó cambio de correo",
            tabla_afectada="usuarios",
            registro_id=user.id,
            descripcion=f"Solicitud para cambiar correo a {nuevo_correo} enviada."
        )

        return Response({'mensaje': 'Se envió un enlace de confirmación al nuevo correo.'})

#Vista para confirmar el cambio de correo
class ConfirmarCambioCorreoAPIView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Usuario.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return Response({"error": "Enlace inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            if not user.nuevo_correo:
                return Response({"error": "No hay un correo nuevo pendiente de confirmar."}, status=status.HTTP_400_BAD_REQUEST)

            user.correo = user.nuevo_correo
            user.nuevo_correo = ''
            user.save()

            LogAccion.objects.create(
                usuario=user,
                accion="Confirmó cambio de correo",
                tabla_afectada="usuarios",
                registro_id=user.id,
                descripcion=f"Correo cambiado correctamente a {user.correo}."
            )

            return Response({"mensaje": "Correo actualizado correctamente."})
        else:
            return Response({"error": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)


        







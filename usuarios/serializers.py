from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from rest_framework import serializers

from .models import Usuario
from .models_usuario_edificio import UsuarioEdificio
from log.models import LogAccion

#====================== SUPERUSER =======================
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'correo', 'nombre_completo', 'telefono', 'foto',
            'tipo_usuario', 'estado', 'fecha_registro', 'created_at', 'updated_at',
            'password'  # usamos este nombre para que lo entienda DRF
        ]
        extra_kwargs = {
            'password': {'write_only': True},  # no se muestra al hacer GET
        }

    def create(self, validated_data):
       password = validated_data.pop('password', None)
       usuario = Usuario(**validated_data)
       if password:
           usuario.set_password(password)
       usuario.save()
       return usuario

class UsuarioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'correo', 'tipo_usuario', 'estado', 'fecha_registro']    

class AdminEditarUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['tipo_usuario', 'estado', 'is_active', 'is_staff','is_superuser']

    def validate_tipo_usuario(self, value):
        if value not in ['arrendador', 'arrendatario']:
            raise serializers.ValidationError("Tipo de usuario inválido.")
        return value

    def validate_estado(self, value):
        if value not in ['activo', 'pendiente', 'rechazado']:
            raise serializers.ValidationError("Estado inválido.")
        return value
    
class AdminAsociarUsuarioEdificioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioEdificio
        fields = ['usuario', 'edificio', 'rol']

    def validate_rol(self, value):
        if value not in ['administrador', 'colaborador']:
            raise serializers.ValidationError("Rol inválido.")
        return value

    def create(self, validated_data):
        return UsuarioEdificio.objects.create(**validated_data)    

class UsuarioEdificioSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()
    edificio = serializers.StringRelatedField()

    class Meta:
        model = UsuarioEdificio
        fields = ['id', 'usuario', 'edificio', 'rol', 'fecha_asignacion', 'created_at', 'updated_at']        

class ActivarDesactivarUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['is_active']       

#===================== ARRENDADOR ========================

class UsuarioBasicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'correo', 'nombre_completo', 'tipo_usuario']       

class ArrendadorActivarDesactivarUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['is_active']

    def update(self, instance, validated_data):
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance

#==================== ARRENDATARIO ========================
class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    tipo_usuario = serializers.ChoiceField(choices=['arrendador', 'arrendatario'])

    class Meta:
        model = Usuario
        fields = ['username', 'correo', 'password', 'tipo_usuario']

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.estado = 'pendiente'  # queda pendiente para activar luego
        usuario.is_active = False
        usuario.save()

        # Log de creación de usuario
        LogAccion.objects.create(
            usuario=usuario,
            accion="Registro de usuario",
            tabla_afectada="usuarios",
            registro_id=usuario.id,
            descripcion=f"Usuario registrado con correo {usuario.correo} y estado pendiente."
        )

        self.enviar_correo_verificacion(usuario)

        return usuario   

    def enviar_correo_verificacion(self, usuario):
        request = self.context.get('request')
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        path = reverse('verificar-correo', kwargs={'uidb64': uid, 'token': token})

        # Construir URL absoluta con request.build_absolute_uri
        url = request.build_absolute_uri(path) if request else f"http://localhost:8000{path}"
        
        # Renderizar plantilla HTML (crea este archivo luego)
        html_message = render_to_string('emails/activar_cuenta.html', {
            'usuario': usuario,
            'url': url,
        })

        send_mail(
            subject="Verifica tu correo",
            message=f"Hola {usuario.username}, por favor activa tu cuenta usando este enlace: {url}",
            from_email="noreply@tuapp.com",
            recipient_list=[usuario.correo],
            fail_silently=False,
            html_message=html_message
        )
    
class EditarPerfilSerializer(serializers.ModelSerializer):
    correo = serializers.EmailField(read_only=True)  # El correo solo se muestra, no se puede editar

    class Meta:
        model = Usuario
        fields = ['username', 'correo', 'nombre_completo', 'telefono', 'foto']

    def validate_username(self, value):
        user = self.context['request'].user
        if Usuario.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("Este username ya está en uso.")
        return value    
    
class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'correo', 'nombre_completo', 'telefono', 'foto', 'tipo_usuario', 'estado', 'is_active']
        read_only_fields = fields    

class SolicitarCambioCorreoSerializer(serializers.Serializer):
    nuevo_correo = serializers.EmailField()

    def validate_nuevo_correo(self, value):
        user = self.context['request'].user
        if Usuario.objects.filter(correo=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Ese correo ya está en uso.")
        return value

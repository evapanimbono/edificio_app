from rest_framework import serializers

from .models_usuario_solicitud import SolicitudUsuarioEdificio

from log.models import LogAccion

class CrearSolicitudUsuarioEdificioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudUsuarioEdificio
        fields = ['edificio', 'tipo_solicitado']  # solo lo que puede enviar el usuario

    def create(self, validated_data):
        usuario = self.context['request'].user
        solicitud =  SolicitudUsuarioEdificio(usuario=usuario, **validated_data)
        solicitud.save()
        
        # Aquí creamos el log de la acción
        LogAccion.objects.create(
            usuario=usuario,
            accion="Solicitó vinculación a edificio",
            tabla_afectada="solicitudes_usuario_edificio",
            registro_id=solicitud.id,
            descripcion=f"Solicitud creada por {usuario.username} para el edificio {solicitud.edificio.nombre} como {solicitud.tipo_solicitado}"
        )
        
        return solicitud
     
class ValidarSolicitudUsuarioEdificioSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField(read_only=True)  # solo ver, no modificar
    edificio = serializers.StringRelatedField(read_only=True)
    tipo_solicitado = serializers.CharField(read_only=True)

    rol_asignado = serializers.ChoiceField(
        choices=SolicitudUsuarioEdificio.ROL_CHOICES,
        required=False, allow_null=True
    )

    aprobado = serializers.BooleanField(required=True)  # NUEVO CAMPO
    comentario_validador = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = SolicitudUsuarioEdificio
        fields = ['usuario', 'edificio', 'tipo_solicitado', 'rol_asignado', 'aprobado', 'comentario_validador']
    def validate(self, data):
        tipo = self.instance.tipo_solicitado if self.instance else None
        rol = data.get('rol_asignado')

        if tipo == 'arrendatario' and rol is not None:
            raise serializers.ValidationError("No se debe asignar rol a arrendatarios.")

        if tipo == 'arrendador' and not rol:
            raise serializers.ValidationError("Debe asignarse un rol si el tipo solicitado es arrendador.")

        return data    
    
class DetalleSolicitudUsuarioEdificioSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()
    edificio = serializers.StringRelatedField()

    class Meta:
        model = SolicitudUsuarioEdificio
        fields = '__all__'  



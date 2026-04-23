from rest_framework import serializers
from .models import Notificacion

class NotificacionListSerializer(serializers.ModelSerializer):
    emisor_nombre = serializers.SerializerMethodField()
    receptor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            'id',
            'titulo',
            'mensaje',
            'tipo',
            'estado',
            'leido',
            'fecha_envio',
            'objeto_tipo',
            'objeto_id',
            'emisor_nombre',
            'receptor_nombre',
            'created_at'
        ]
        read_only_fields = (
            'id',
            'estado',
            'leido',
            'fecha_envio',
            'emisor_nombre',
            'receptor_nombre',
            'created_at',
        )

    def get_emisor_nombre(self, obj):
        if obj.emisor:
            return obj.emisor.nombre_completo or obj.emisor.username
        return "Sistema"

    def get_receptor_nombre(self, obj):
        if obj.receptor:
            return obj.receptor.nombre_completo or obj.receptor.username
        return None

class MarcarNotificacionLeidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['leido', 'estado']

    def update(self, instance, validated_data):
        instance.leido = True
        instance.estado = 'leida'
        instance.save(update_fields=['leido', 'estado', 'updated_at'])
        return instance
    
class ArchivarNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['estado']

    def update(self, instance, validated_data):
        instance.estado = 'archivada'
        instance.save(update_fields=['estado', 'updated_at'])
        return instance
    
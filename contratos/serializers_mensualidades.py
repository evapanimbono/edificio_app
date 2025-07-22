from rest_framework import serializers
from django.utils import timezone

from .models_mensualidades import Mensualidad
from log.models import LogAccion

from pagos.tareas import crear_recibo_para_mensualidad

class MensualidadSerializer(serializers.ModelSerializer):
    monto_bs_actual = serializers.SerializerMethodField()
    comentario_anulacion = serializers.CharField(read_only=True)

    class Meta:
        model = Mensualidad
        fields = [
            'id', 'contrato', 'fecha_generacion', 'fecha_vencimiento',
            'monto_usd', 'saldo_pendiente', 'estado',
            'monto_bs_actual', 'comentario_anulacion',
        ]

    def get_monto_bs_actual(self, obj):
        return obj.monto_bs_actual  # Propiedad del modelo

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # Eliminar campos que no aplican
        if instance.estado != 'pagado':
            rep.pop('monto_bs_pagado', None)
            rep.pop('tasa_usada', None)

        if instance.estado != 'anulado':
            rep.pop('comentario_anulacion', None)

        return rep

class MensualidadParaPagoSerializer(serializers.ModelSerializer):
    monto_bs_actual = serializers.SerializerMethodField()
    contrato_id = serializers.IntegerField(source='contrato.id', read_only=True)

    class Meta:
        model = Mensualidad
        fields = ['id', 'contrato_id', 'fecha_vencimiento', 'monto_usd', 'monto_bs_actual', 'estado']

    def get_monto_bs_actual(self, obj):
        return obj.monto_bs_actual

class MensualidadCrearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensualidad
        fields = ['contrato', 'fecha_vencimiento', 'monto_usd']

    def validate(self, data):
        contrato = data.get('contrato')
        if not contrato.activo:
            raise serializers.ValidationError("El contrato debe estar activo.")
        
        if not data.get("fecha_vencimiento"):
            raise serializers.ValidationError("La fecha de vencimiento es obligatoria.")
        
        return data

    def create(self, validated_data):
        mensualidad = Mensualidad.objects.create(
            contrato=validated_data['contrato'],
            fecha_generacion=timezone.now().date(),
            fecha_vencimiento=validated_data['fecha_vencimiento'],
            monto_usd=validated_data['monto_usd'],
            saldo_pendiente=validated_data['monto_usd'],
            estado='atrasado' if validated_data['fecha_vencimiento'] < timezone.now().date() else 'pendiente'
        )

        LogAccion.objects.create(
            usuario=self.context['request'].user,
            accion="creó mensualidad",
            tabla_afectada="Mensualidad",
            registro_id=mensualidad.id,
            descripcion=f"Mensualidad #{mensualidad.id} creada desde serializer. Contrato #{mensualidad.contrato.id}, fecha vencimiento: {mensualidad.fecha_vencimiento}."
        )
        
        return mensualidad
  
class MensualidadEditarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensualidad
        fields = ['fecha_vencimiento']

    def validate(self, data):
        mensualidad = self.instance
        if mensualidad.estado in ['pagado', 'anulado']:
            raise serializers.ValidationError("No se puede modificar una mensualidad pagada o anulada.")
        
        return data

    def update(self, instance, validated_data):
        nueva_fecha = validated_data['fecha_vencimiento']
        estado_mensualidad = 'atrasado' if nueva_fecha < timezone.now().date() else 'pendiente'

        # Actualizar la mensualidad
        instance.fecha_vencimiento = nueva_fecha
        instance.estado = estado_mensualidad
        instance.save()

         # Agregar log de modificación
        LogAccion.objects.create(
            usuario=self.context['request'].user,
            accion="modificó mensualidad",
            tabla_afectada="Mensualidad",
            registro_id=instance.id,
            descripcion=f"Mensualidad #{instance.id} modificada. Nueva fecha de vencimiento: {instance.fecha_vencimiento}, nuevo estado: {instance.estado}."
        )       

        return instance
    
class ComentarioAnulacionSerializer(serializers.Serializer):
    comentario = serializers.CharField(required=True, max_length=500)
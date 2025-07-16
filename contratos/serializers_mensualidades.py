from rest_framework import serializers
from django.utils import timezone

from .models_mensualidades import Mensualidad
from log.models import LogAccion

from pagos.tareas import crear_recibo_para_mensualidad

class MensualidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensualidad
        fields = '__all__'

class MensualidadCrearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensualidad
        fields = ['contrato', 'fecha_vencimiento', 'monto_usd']

    def validate(self, data):
        contrato = data.get('contrato')
        if not contrato.activo:
            raise serializers.ValidationError("El contrato debe estar activo.")
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
        
        if mensualidad.pagomensualidad_set.exists():
            raise serializers.ValidationError("No se puede modificar una mensualidad con pagos registrados.")
    
        return data

    def update(self, instance, validated_data):
        nueva_fecha = validated_data['fecha_vencimiento']
        estado_mensualidad = 'atrasado' if nueva_fecha < timezone.now().date() else 'pendiente'

        # Actualizar la mensualidad
        instance.fecha_vencimiento = nueva_fecha
        instance.estado = estado_mensualidad
        instance.save()

        # Buscar recibo asociado si existe
        recibo_rel = instance.recibomensualidad_set.first()
        if recibo_rel:
            recibo = recibo_rel.recibo
            if recibo.estado in ['pendiente', 'atrasado']:
                recibo.fecha_vencimiento = nueva_fecha
                recibo.estado = estado_mensualidad
                recibo.save()

        return instance
    
class AnularMensualidadSerializer(serializers.Serializer):
    comentario = serializers.CharField(required=True, max_length=500)
from rest_framework import serializers
from django.utils import timezone

from .models import Contrato
from .models_mensualidades import Mensualidad
from log.models import LogAccion

from pagos.tareas import crear_recibo_para_mensualidad

class MensualidadSerializer(serializers.ModelSerializer):
    monto_bs_actual = serializers.SerializerMethodField()
    comentario_anulacion = serializers.CharField(read_only=True)
    apartamento_numero = serializers.SerializerMethodField()

    class Meta:
        model = Mensualidad
        fields = [
            'id','apartamento_numero','fecha_generacion', 'fecha_vencimiento',
            'monto_usd', 'saldo_pendiente', 'estado',
            'monto_bs_actual', 'comentario_anulacion',
        ]

    def get_apartamento_numero(self, obj):
        # Asegúrate que contrato y apartamento existen antes de acceder
        if obj.contrato and obj.contrato.apartamento:
            return obj.contrato.apartamento.numero_apartamento
        return None

    def get_monto_bs_actual(self, obj):
        return obj.monto_bs_actual  # Propiedad del modelo

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # Ocultar monto_bs_actual si la mensualidad está pagada o anulada
        if instance.estado in ['pagado', 'anulado']:
            rep.pop('monto_bs_actual', None)

        if instance.estado != 'anulado':
            rep.pop('comentario_anulacion', None)

        return rep

class MensualidadParaPagoSerializer(serializers.ModelSerializer):
    monto_bs_actual = serializers.SerializerMethodField()
    apartamento_numero = serializers.SerializerMethodField()

    class Meta:
        model = Mensualidad
        fields = ['id', 'apartamento_numero', 'fecha_vencimiento', 'monto_usd', 'monto_bs_actual', 'estado']

    def get_monto_bs_actual(self, obj):
        return obj.monto_bs_actual
    
    def get_apartamento_numero(self, obj):
        # Accedemos al número del apartamento a través del contrato relacionado
        return obj.contrato.apartamento.numero_apartamento if obj.contrato and obj.contrato.apartamento else None

class MensualidadCrearSerializer(serializers.ModelSerializer):
    numero_apartamento = serializers.IntegerField(write_only=True)

    class Meta:
        model = Mensualidad
        fields = ['numero_apartamento', 'fecha_vencimiento', 'monto_usd']

    def validate(self, data):
        numero_apto = data.get('numero_apartamento')
        fecha_vencimiento = data.get('fecha_vencimiento')

        # Busca el contrato activo para el apartamento
        contratos = Contrato.objects.filter(
            apartamento__numero_apartamento=numero_apto,
            activo=True
        )

        if not contratos.exists():
            raise serializers.ValidationError(f"No existe contrato activo para el apartamento #{numero_apto}")

        contrato = contratos.first()

        data['contrato'] = contrato

        if not fecha_vencimiento:
            raise serializers.ValidationError("La fecha de vencimiento es obligatoria.")

        return data

    def create(self, validated_data):
        contrato = validated_data.pop('contrato')
        mensualidad = Mensualidad.objects.create(
            contrato=contrato,
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
        if mensualidad.estado not in ['pendiente', 'atrasada']:
            raise serializers.ValidationError("Solo se puede editar una mensualidad en estado pendiente o atrasada.")
        
        if mensualidad.pagos.filter(estado='validado').exists():
            raise serializers.ValidationError("No se puede editar una mensualidad que tiene pagos validados.")

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
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from datetime import date,timedelta

from edificios.models import Apartamento

from contratos.models import Contrato

from .models import GastoExtra

from pagos.models import PagoGastoExtra

class GastoExtraSerializer(serializers.ModelSerializer):
    apartamento_numero = serializers.SerializerMethodField()
    comentario_anulacion = serializers.CharField(read_only=True) 
    monto_bs_actual = serializers.SerializerMethodField()

    class Meta:
        model = GastoExtra
        exclude = ['apartamento','created_at', 'updated_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # Ocultar monto_bs_actual si la mensualidad está pagada o anulada
        if instance.estado in ['pagado', 'anulado']:
            rep.pop('monto_bs_actual', None)

        if instance.estado != 'anulado':
            # Quitar comentario_anulacion si no está anulado
            rep.pop('comentario_anulacion', None)
        return rep
    
    def get_monto_bs_actual(self, obj):
        return obj.monto_bs_actual  # Propiedad del modelo

    def get_apartamento_numero(self, obj):
        return obj.apartamento.numero_apartamento if obj.apartamento else None

class GastoExtraCreateSerializer(serializers.ModelSerializer):
    apartamento_numero = serializers.IntegerField(write_only=True)  # recibe número, no ID

    class Meta:
        model = GastoExtra
        # Excluimos los campos automáticos para que no los pidan
        exclude = ['apartamento','saldo_pendiente', 'fecha_generacion', 'estado','comentario_anulacion', 'created_at', 'updated_at']

    def validate(self, data):
        if not data.get("fecha_vencimiento"):
            raise serializers.ValidationError("La fecha de vencimiento es obligatoria.")
        return data

    def validate_apartamento_numero(self, value):
        # Buscar apartamento por número
        try:
            apto = Apartamento.objects.get(numero_apartamento=value)
        except Apartamento.DoesNotExist:
            raise serializers.ValidationError("Apartamento no encontrado con ese número.")

        # Validar que tenga contrato activo
        contratos_activos = Contrato.objects.filter(apartamento=apto, activo=True)
        if not contratos_activos.exists():
            raise serializers.ValidationError("El apartamento no tiene contrato activo.")

        # Guardamos el apartamento en el serializer para usar luego
        self.apartamento_obj = apto
        return value

    def validate_monto_usd(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0.")
        return value

    def create(self, validated_data):

        # Quitamos apartamento_numero de los datos para no pasar al modelo
        validated_data.pop('apartamento_numero', None)

        # Preparamos estado, fecha y saldo
        monto = validated_data['monto_usd']
        fecha_vencimiento = validated_data.get('fecha_vencimiento')
        hoy = date.today()

        estado = 'pendiente'
        if fecha_vencimiento and fecha_vencimiento < hoy:
            estado = 'atrasado'

        gasto = GastoExtra.objects.create(
            apartamento=self.apartamento_obj,
            saldo_pendiente=monto,
            fecha_generacion=hoy,
            estado=estado,
            **validated_data
        )
        return gasto

class GastoExtraUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GastoExtra
        fields = ['descripcion', 'monto_usd', 'fecha_vencimiento']

    def validate_monto_usd(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0.")
        return value
    
    def validate(self, data):
        instance = self.instance

        if instance.estado in ['pagado', 'anulado']:
            raise serializers.ValidationError("No se puede editar un gasto pagado o anulado.")

        # Solo se bloquea si existen pagos pendientes o validados
        pagos_activos = PagoGastoExtra.objects.filter(
            gasto_extra=instance,
            estado__in=['pendiente', 'validado']
        ).exists()

        if pagos_activos:
            raise serializers.ValidationError("No se puede editar un gasto que tiene pagos activos (pendientes o validados).")
        
        return data

class GastoExtraDetailSerializer(serializers.ModelSerializer):
    comentario_anulacion = serializers.CharField(read_only=True)
    apartamento_numero = serializers.SerializerMethodField()
    monto_bs_actual = serializers.SerializerMethodField()

    class Meta:
        model = GastoExtra
        exclude = ['apartamento','created_at', 'updated_at']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Ocultar monto_bs_actual si la mensualidad está pagada o anulada
        if instance.estado in ['pagado', 'anulado']:
            rep.pop('monto_bs_actual', None)
            
        if instance.estado != 'anulado':
            # Quitar comentario_anulacion si no está anulado
            rep.pop('comentario_anulacion', None)
        return rep

    def validate(self, data):
        monto = data.get("monto_usd")
        fecha_vencimiento = data.get("fecha_vencimiento")

        if monto is not None and monto <= 0:
            raise ValidationError("El monto debe ser mayor a 0.")
        
        #Valida que se ingrese una fecha de vencimiento
        if not fecha_vencimiento:
            raise ValidationError("La fecha de vencimiento es obligatoria.")

        #Valida que la fecha de vencimiento no sea mas alla de 2 años
        limite_antiguo = date.today() - timedelta(days=365*2)
        if fecha_vencimiento and fecha_vencimiento < limite_antiguo:
            raise ValidationError("La fecha de vencimiento no puede ser anterior a 2 años atrás.")

        #Valida que la fecha de vencimiento no sea mayor a 3 años en el futuro
        limite_futuro = date.today() + timedelta(days=365*3)
        if fecha_vencimiento and fecha_vencimiento > limite_futuro:
            raise ValidationError("La fecha de vencimiento no puede ser más de 3 años en el futuro.")

        return data

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
    def get_monto_bs_actual(self, obj):
        return obj.monto_bs_actual  # Propiedad del modelo

    def get_apartamento_numero(self, obj):
        return obj.apartamento.numero_apartamento if obj.apartamento else None

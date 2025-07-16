from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from datetime import date

from edificios.models import Apartamento

from contratos.models import Contrato

from .models import GastoExtra

from pagos.models import PagoGastoExtra

class GastoExtraSerializer(serializers.ModelSerializer):
    apartamento_numero = serializers.SerializerMethodField()

    class Meta:
        model = GastoExtra
        fields = '__all__'

    def get_apartamento_numero(self, obj):
        return obj.apartamento.numero_apartamento if obj.apartamento else None

class GastoExtraCreateSerializer(serializers.ModelSerializer):
    apartamento_numero = serializers.IntegerField(write_only=True)  # recibe número, no ID

    class Meta:
        model = GastoExtra
        # Excluimos los campos automáticos para que no los pidan
        exclude = ['apartamento','saldo_pendiente', 'fecha_generacion', 'estado', 'created_at', 'updated_at']

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

        if PagoGastoExtra.objects.filter(gasto_extra=instance).exists():
            raise serializers.ValidationError("No se puede editar un gasto que ya tiene pagos registrados.")

        return data

class GastoExtraDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = GastoExtra
        fields = '__all__'

    def validate(self, data):
        monto = data.get("monto_usd")
        fecha_vencimiento = data.get("fecha_vencimiento")

        if monto is not None and monto <= 0:
            raise ValidationError("El monto debe ser mayor a 0.")

        return data

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from datetime import date

from .models import GastoExtra
from pagos.models_recibos import ReciboGastoExtra, Recibo

class GastoExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = GastoExtra
        fields = '__all__'

class GastoExtraDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GastoExtra
        fields = '__all__'

    def validate(self, data):
        monto = data.get("monto_usd")
        fecha_vencimiento = data.get("fecha_vencimiento")

        if monto is not None and monto <= 0:
            raise ValidationError("El monto debe ser mayor a 0.")

        # Evaluar y ajustar estado automáticamente según la fecha
        if fecha_vencimiento:
            if fecha_vencimiento < date.today():
                data['estado'] = 'atrasado'
            else:
                data['estado'] = 'pendiente'

        return data

    def update(self, instance, validated_data):
        monto_cambiado = 'monto_usd' in validated_data and validated_data['monto_usd'] != instance.monto_usd
        vencimiento_cambiado = 'fecha_vencimiento' in validated_data and validated_data['fecha_vencimiento'] != instance.fecha_vencimiento

        instance = super().update(instance, validated_data)

        # Actualizar recibo solo si no ha sido pagado y si cambió algo relevante
        try:
            recibo_gasto = ReciboGastoExtra.objects.get(gasto_extra=instance)
            recibo = recibo_gasto.recibo
            if recibo.estado == 'pendiente' or recibo.estado == 'atrasado':
                if monto_cambiado:
                    recibo.total_usd = instance.monto_usd
                    recibo_gasto.monto_usd = instance.monto_usd
                    recibo_gasto.save()
                if vencimiento_cambiado:
                    recibo.fecha_vencimiento = instance.fecha_vencimiento
                recibo.save()
        except ReciboGastoExtra.DoesNotExist:
            pass  # No hay recibo asociado (muy raro pero posible si hubo error)

        return instance

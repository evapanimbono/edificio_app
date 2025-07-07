from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from .models import Contrato

class ContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contrato
        fields = '__all__'

    def validate(self, data):
        apartamento = data.get('apartamento')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        monto_mensual = data.get('monto_mensual_usd')

        # Validar que apartamento esté activo
        if apartamento.estado != 'activo':
            raise ValidationError("No se puede crear un contrato para un apartamento inactivo.")

        # Validar que fecha_inicio sea antes de fecha_fin
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")

        # Validar que no haya contratos activos o que se solapen en fechas para el mismo apartamento
        contratos_conflicto = Contrato.objects.filter(
            apartamento=apartamento,
            fecha_fin__gte=fecha_inicio,
            fecha_inicio__lte=fecha_fin
        )
        if self.instance:
            # Excluir contrato actual si estamos en update
            contratos_conflicto = contratos_conflicto.exclude(pk=self.instance.pk)
        if contratos_conflicto.exists():
            raise ValidationError("Ya existe un contrato activo o con fechas que se solapan para este apartamento.")

        # ✅ Validar monto mensual positivo
        if monto_mensual is not None and monto_mensual <= 0:
            raise ValidationError("El monto mensual debe ser mayor que cero.")

        return data
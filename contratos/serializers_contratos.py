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
    
class ContratoDetalleSerializer(serializers.ModelSerializer):
    # Esto traerá el nombre del edificio y el número de apto en lugar de IDs
    edificio_nombre = serializers.ReadOnlyField(source='apartamento.edificio.nombre')
    apartamento_numero = serializers.ReadOnlyField(source='apartamento.numero_apartamento')

    class Meta:
        model = Contrato
        fields = [
            'id', 'edificio_nombre', 'apartamento_numero', 
            'fecha_inicio', 'fecha_fin', 'fecha_pago_mensual', 
            'monto_usd_mensual', 'activo', 'archivo_contrato_pdf'
        ]

class ContratoListaArrendadorSerializer(serializers.ModelSerializer):
    arrendatario_nombre = serializers.ReadOnlyField(source='arrendatario.nombre_completo')
    arrendatario_email = serializers.ReadOnlyField(source='arrendatario.correo')
    arrendatario_telefono = serializers.ReadOnlyField(source='arrendatario.telefono') # Si tienes este campo
    
    edificio_nombre = serializers.ReadOnlyField(source='apartamento.edificio.nombre')
    apartamento_numero = serializers.ReadOnlyField(source='apartamento.numero_apartamento')

    class Meta:
        model = Contrato
        fields = [
            'id', 'arrendatario_nombre', 'arrendatario_email', 'arrendatario_telefono',
            'edificio_nombre', 'apartamento_numero', 'monto_usd_mensual', 
            'fecha_pago_mensual', 'fecha_inicio', 'fecha_fin', 'activo', 'archivo_contrato_pdf'
        ]
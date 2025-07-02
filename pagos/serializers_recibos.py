
from django.db.models import Q
from rest_framework import serializers
from decimal import Decimal

from .models_recibos import Recibo, ReciboMensualidad, ReciboGastoExtra
from .models import PagoEfectivo,PagoTransferencias, Pago
from tasas.models import TasaDia

class ReciboMensualidadSerializer(serializers.ModelSerializer):
    mensualidad_monto_usd = serializers.DecimalField(source="mensualidad.monto_usd", max_digits=10, decimal_places=2, read_only=True)
    mensualidad_fecha_vencimiento = serializers.DateField(source="mensualidad.fecha_vencimiento", read_only=True)

    class Meta:
        model = ReciboMensualidad
        fields = ['id', 'mensualidad', 'mensualidad_monto_usd', 'monto_bs_pagado', 'mensualidad_fecha_vencimiento']

class ReciboGastoExtraSerializer(serializers.ModelSerializer):
    gasto_descripcion = serializers.CharField(source="gasto_extra.descripcion", read_only=True)
    gasto_monto_usd = serializers.DecimalField(source="gasto_extra.monto_usd", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ReciboGastoExtra
        fields = ['id', 'gasto_extra', 'gasto_monto_usd', 'monto_bs_pagado', 'gasto_descripcion']

class ReciboSerializer(serializers.ModelSerializer):
    mensualidades = ReciboMensualidadSerializer(many=True, read_only=True)
    gastos = ReciboGastoExtraSerializer(many=True, read_only=True)
    monto_estimado_bs = serializers.SerializerMethodField()
    pagado_en = serializers.SerializerMethodField()

    class Meta:
        model = Recibo
        fields = [
            'id', 'usuario', 'estado', 'fecha_emision', 'fecha_vencimiento',
            'total_usd', 'total_bs', 'monto_estimado_bs',
            'observaciones', 'creado_por', 'created_at', 'updated_at',
            'mensualidades', 'gastos',
            'pagado_en'
        ]

    def get_monto_estimado_bs(self, obj):
        if obj.estado == 'pagado':
            return obj.total_bs

        saldo_usd = Decimal('0.00')
        for rm in obj.mensualidades.all():
            saldo_usd += rm.mensualidad.saldo_pendiente
        for rg in obj.gastos.all():
            saldo_usd += rg.gasto_extra.saldo_pendiente

        tasa = TasaDia.objects.order_by('-fecha').first()
        if not tasa:
            return None
        
        return round(saldo_usd * tasa.valor_usd_bs, 2)
    
    def get_pagado_en(self, obj):
        if obj.estado != 'pagado':
            return None

        # Buscar los pagos asociados al recibo a través de las mensualidades y gastos
        pagos = Pago.objects.filter(
            Q(mensualidades_pagadas__mensualidad__in=[rm.mensualidad for rm in obj.mensualidades.all()]) |
            Q(gastos_pagados__gasto_extra__in=[rg.gasto_extra for rg in obj.gastos.all()])
        ).distinct()

        if not pagos.exists():
            return None

        efectivo_total = Decimal('0.00')
        transferencia_total = Decimal('0.00')
        resultado = {}

        for pago in pagos:
            efectivo_qs = getattr(pago, 'pagos_efectivo', pago.pagoefectivo_set).all()
            transferencia_qs = getattr(pago, 'pagos_transferencias', pago.pagotransferencias_set).all()

            efectivo_total += sum((e.denominacion or 0) for e in efectivo_qs)
            transferencia_total += sum((t.monto_bs or 0) for t in transferencia_qs)

        if efectivo_total > 0:
            resultado["efectivo_usd"] = float(efectivo_total)

        if transferencia_total > 0:
            resultado["transferencia_bs"] = float(transferencia_total)

        return resultado if resultado else None

class GenerarReciboSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField()
    mensualidades_id = serializers.ListField(
        child=serializers.IntegerField(), required=False)
    gastos_extra_id = serializers.ListField(
        child=serializers.IntegerField(), required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get('mensualidades_id') and not data.get('gastos_extra_id'):
            raise serializers.ValidationError("Debes seleccionar al menos una mensualidad o gasto extra.")
        return data

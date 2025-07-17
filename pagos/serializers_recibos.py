
from django.db.models import Q
from rest_framework import serializers
from decimal import Decimal

from .models_recibos import Recibo, ReciboMensualidad, ReciboGastoExtra
from .models import PagoEfectivo,PagoTransferencias, Pago
from tasas.models import TasaDia

from contratos.serializers_mensualidades import MensualidadSerializer
from gastos.serializers import GastoExtraSerializer

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
    pagado_en = serializers.SerializerMethodField()

    class Meta:
        model = Recibo
        fields = [
            'id', 'usuario', 'estado', 'fecha_emision',
            'total_usd', 'total_bs',
            'observaciones', 'creado_por', 'created_at', 'updated_at',
            'mensualidades', 'gastos',
            'pagado_en'
        ]
    
    def get_pagado_en(self, obj):
        if obj.estado != 'pagado':
            return None

        # Obtener listas de mensualidades y gastos para filtro
        mensualidades_list = [rm.mensualidad for rm in obj.mensualidades.all()]
        gastos_list = [rg.gasto_extra for rg in obj.gastos.all()]

        # Buscar los pagos asociados al recibo a través de las mensualidades y gastos
        pagos = Pago.objects.filter(
            Q(mensualidades_pagadas__mensualidad__in=mensualidades_list) |
            Q(gastos_pagados__gasto_extra__in=gastos_list)
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

        return resultado or None
       
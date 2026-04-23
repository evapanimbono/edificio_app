from rest_framework import serializers
from django.utils import timezone

from tasas.models import TasaDia
from tasas.serializers import TasaDiaSerializer

from .models import Pago,PagoEfectivo,PagoTransferencias

class PagoSerializer(serializers.ModelSerializer):
    tasa_dia = TasaDiaSerializer(read_only=True)

    class Meta:
        model = Pago
        fields = '__all__'

class PagoEfectivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoEfectivo
        fields = '__all__'

class PagoTransferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoTransferencias
        fields = '__all__'

#=================================================================

class ItemPagoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)

class BilleteSerializer(serializers.Serializer):
    denominacion = serializers.DecimalField(max_digits=10, decimal_places=2)
    serial = serializers.CharField()
    foto_billete = serializers.CharField(required=False)  # si es Base64 o URL

class TransferenciaSerializer(serializers.Serializer):
    banco_destino = serializers.CharField()
    cuenta_destino = serializers.CharField()
    referencia = serializers.CharField()
    monto_bs = serializers.DecimalField(max_digits=15, decimal_places=2)
    comprobante_img = serializers.CharField(required=False)
    fecha_transferencia = serializers.DateField() 
    
class PagoRegistroSerializer(serializers.Serializer):

    monto_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    tipo_pago = serializers.ChoiceField(choices=['efectivo', 'transferencia', 'mixto'])
    fecha_pago = serializers.DateField()

    mensualidades = ItemPagoSerializer(many=True, required=False)
    gastos_extra = ItemPagoSerializer(many=True, required=False)

    efectivo = BilleteSerializer(many=True, required=False)
    transferencia = TransferenciaSerializer(required=False)
    
    def validate(self, data):
        usuario = self.context["request"].user

        # 1. Validar que haya al menos una mensualidad o gasto
        if not data.get("mensualidades") and not data.get("gastos_extra"):
            raise serializers.ValidationError("Debes incluir al menos una mensualidad o gasto extra.")

        # 2. Validar tipo de pago y datos correspondientes
        tipo_pago = data.get("tipo_pago")

        if tipo_pago == "efectivo" and not data.get("efectivo"):
            raise serializers.ValidationError("Debes incluir los datos del efectivo.")

        if tipo_pago == "transferencia" and not data.get("transferencia"):
            raise serializers.ValidationError("Debes incluir los datos de la transferencia.")

        if tipo_pago == "mixto":
            if not data.get("efectivo") and not data.get("transferencia"):
                raise serializers.ValidationError("Debes incluir efectivo o transferencia si seleccionas tipo mixto.")

        # 3. Obtener la fecha relevante para aplicar la tasa
        fecha_base = None

        if tipo_pago == "transferencia" or tipo_pago == "mixto":
            transferencia_data = data.get("transferencia")
            if not transferencia_data:
                raise serializers.ValidationError("Faltan los datos de la transferencia.")

            fecha_transferencia = transferencia_data.get("fecha_transferencia")

            if not fecha_transferencia:
                raise serializers.ValidationError("Debes especificar la fecha de la transferencia.")

            if fecha_transferencia > timezone.now().date():
                raise serializers.ValidationError("La fecha de la transferencia no puede ser en el futuro.")

            fecha_base = fecha_transferencia
        else:
            # tipo efectivo
            fecha_base = data.get("fecha_pago")

        # 4. Buscar tasa activa para esa fecha
        tasa = TasaDia.objects.filter(fecha=fecha_base, estado="activa").first()
        if not tasa:
            raise serializers.ValidationError(f"No se encontró una tasa activa para el día {fecha_base}.")

        # 5. Almacenar la tasa para usar luego en create()
        data["tasa_dia"] = tasa
        
        return data

class DetallePagoSerializer(serializers.ModelSerializer):       
    mensualidades = serializers.SerializerMethodField()
    gastos_extra = serializers.SerializerMethodField()
    efectivo = serializers.SerializerMethodField()
    transferencias = serializers.SerializerMethodField()
    tasa_usd = serializers.SerializerMethodField()
    tasa_dia = TasaDiaSerializer(read_only=True)  

    class Meta:
        model = Pago
        fields = [
            'id',
            'usuario',
            'fecha_pago',
            'tipo_pago',
            'monto_total',
            'monto_bs',
            'tasa_usd',
            'tasa_dia',
            'estado_validacion',
            'fecha_validacion',
            'mensualidades',
            'gastos_extra',
            'efectivo',
            'transferencias',
        ]

    def get_tasa_usd(self, obj):
        return obj.tasa_usd if obj.tasa_usd is not None else None   

    def get_mensualidades(self, obj):
        return [
            {
                "id": pm.mensualidad.id,
                "fecha_vencimiento": pm.mensualidad.fecha_vencimiento,
                "monto_pagado": pm.monto_pagado,
                "monto_total": pm.mensualidad.monto_usd,
            }
            for pm in obj.mensualidades_pagadas.select_related("mensualidad")
        ]

    def get_gastos_extra(self, obj):
        return [
            {
                "id": pg.gasto_extra.id,
                "descripcion": pg.gasto_extra.descripcion,
                "monto_pagado": pg.monto_pagado,
                "monto_total": pg.gasto_extra.monto_usd,
            }
            for pg in obj.gastos_pagados.select_related("gasto_extra")
        ]

    def get_efectivo(self, obj):
        return [
            {
                "denominacion": e.denominacion,
                "serial": e.serial,
                "foto_billete": e.foto_billete
            }
            for e in obj.pagoefectivo_set.all()
        ]

    def get_transferencias(self, obj):
        return [
            {
                "banco_destino": t.banco_destino,
                "cuenta_destino": t.cuenta_destino,
                "referencia": t.referencia,
                "monto_bs": t.monto_bs,
                "comprobante_img": t.comprobante_img,
                "fecha_transferencia": t.fecha_transferencia
            }
            for t in obj.pagotransferencias_set.all()
        ]

class AnularPagoSerializer(serializers.Serializer):
    comentario = serializers.CharField(max_length=255, required=True, allow_blank=False)

class AccionValidarPagoSerializer(serializers.Serializer):
    accion = serializers.ChoiceField(choices=['validar', 'rechazar'])
    observacion = serializers.CharField(required=False, allow_blank=True)
    
class EstadoCuentaSerializer(serializers.Serializer):
    id_apartamento = serializers.IntegerField(read_only=True)
    nombre_apartamento = serializers.CharField(read_only=True)
    total_mensualidades = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_gastos_extra = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_pagado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    saldo_pendiente = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    moneda = serializers.CharField(read_only=True)
    
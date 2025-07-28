# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from usuarios.models import Usuario

from tasas.models import TasaDia 

class Pago(models.Model):
    TIPO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('mixto', 'Mixto'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('validado', 'Validado'),
        ('rechazado', 'Rechazado'),
        ('anulado', 'Anulado'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True, related_name='pagos_realizados')
    tipo_pago = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha_pago = models.DateField()
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_bs = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    tasa_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tasa_dia = models.ForeignKey(TasaDia,on_delete=models.PROTECT,blank=True,null=True,related_name='pagos',help_text="Tasa del día usada para calcular este pago")
    estado_validacion = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    validado_por = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='validado_por', blank=True, null=True, related_name='pagos_validados')
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    comentario_anulacion = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return f"Pago #{self.id} - {self.tipo_pago} - {self.estado_validacion}"

    class Meta:
        db_table = 'pagos'

class PagoMensualidad(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name="mensualidades_pagadas")
    mensualidad = models.ForeignKey('contratos.Mensualidad', on_delete=models.CASCADE)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'pagos_mensualidades'
        unique_together = ('pago', 'mensualidad')

    def __str__(self):
        return f"Pago {self.pago_id} → Mensualidad {self.mensualidad_id}: {self.monto_pagado}"

class PagoGastoExtra(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name="gastos_pagados")
    gasto_extra = models.ForeignKey('gastos.GastoExtra', on_delete=models.CASCADE)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'pagos_gastos_extra'
        unique_together = ('pago', 'gasto_extra')

    def __str__(self):
        return f"Pago {self.pago_id} → GastoExtra {self.gasto_extra_id}: {self.monto_pagado}"

class PagoEfectivo(models.Model):
    pago = models.ForeignKey('pagos.Pago', models.DO_NOTHING)
    denominacion = models.DecimalField(max_digits=10, decimal_places=2)
    serial = models.CharField(max_length=50, blank=True, null=True)
    foto_billete = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.denominacion} - {self.serial}"
    
    class Meta:
        db_table = 'pagos_efectivo'

class PagoTransferencias(models.Model):
    pago = models.ForeignKey('pagos.Pago', models.DO_NOTHING)
    banco_destino = models.CharField(max_length=100)
    cuenta_destino = models.CharField(max_length=50)
    referencia = models.CharField(max_length=100)
    monto_bs = models.DecimalField(max_digits=15, decimal_places=2)
    comprobante_img = models.TextField(blank=True, null=True)
    fecha_transferencia = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pago} - Ref: {self.referencia} - {self.monto_bs} Bs"
    
    class Meta:
        db_table = 'pagos_transferencias'


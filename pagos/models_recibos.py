from django.db import models
from usuarios.models import Usuario

class Recibo(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('atrasado', 'Atrasado'),
        ('anulado', 'Anulado'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    total_usd = models.DecimalField(max_digits=10, decimal_places=2)
    total_bs = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey('usuarios.Usuario', related_name='recibos_creados', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recibos'

    def __str__(self):
        return f"Recibo #{self.id} - {self.usuario.username} - {self.fecha_emision.strftime('%Y-%m-%d')}"        

class ReciboMensualidad(models.Model):
    recibo = models.ForeignKey('pagos.Recibo', on_delete=models.CASCADE, related_name='mensualidades')
    mensualidad = models.ForeignKey('contratos.Mensualidad', on_delete=models.DO_NOTHING)
    monto_usd = models.DecimalField(max_digits=10, decimal_places=2)
    monto_bs_pagado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Mensualidad {self.mensualidad.id} - Recibo {self.recibo.id}"

    class Meta:
        db_table = 'recibo_mensualidades'

class ReciboGastoExtra(models.Model):
    recibo = models.ForeignKey('pagos.Recibo', on_delete=models.CASCADE, related_name='gastos')
    gasto_extra = models.ForeignKey('gastos.GastoExtra', on_delete=models.DO_NOTHING)
    monto_usd = models.DecimalField(max_digits=10, decimal_places=2)
    monto_bs_pagado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"GastoExtra {self.gasto_extra.id} - Recibo {self.recibo.id}"

    class Meta:
        db_table = 'recibo_gastos_extra'
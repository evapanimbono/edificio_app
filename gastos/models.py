# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)

class GastoExtra(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('atrasado', 'Atrasado'),
        ('anulado', 'Anulado'),
    ]
    apartamento = models.ForeignKey('edificios.Apartamento', models.DO_NOTHING)
    descripcion = models.TextField()
    monto_usd = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha_generacion = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES,default='pendiente')
    comentario_anulacion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Si es un gasto nuevo (no tiene ID aún) y no se ha modificado manualmente el saldo_pendiente
        if not self.pk and (self.saldo_pendiente == 0 or self.saldo_pendiente is None):
            self.saldo_pendiente = self.monto_usd
        super().save(*args, **kwargs)

    def __str__(self):
       return f"{self.apartamento} - {self.descripcion[:30]}..."

    class Meta:
        db_table = 'gastos_extra'

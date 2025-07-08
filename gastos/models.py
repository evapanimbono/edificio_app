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
    ]
    apartamento = models.ForeignKey('edificios.Apartamento', models.DO_NOTHING)
    descripcion = models.TextField()
    monto_usd = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha_generacion = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES,default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def actualizar_recibo(self):
        from pagos.models_recibos import ReciboGastoExtra

        try:
            recibo_gasto = self.recibogastoextra_set.first()
            recibo = recibo_gasto.recibo if recibo_gasto else None

            if recibo and recibo.estado in ['pendiente', 'atrasado']:
                recibo.total_usd = self.monto_usd
                recibo.fecha_vencimiento = self.fecha_vencimiento

                # 🔁 Recalcular estado del recibo también
                hoy = timezone.now().date()
                if self.fecha_vencimiento and self.fecha_vencimiento < hoy:
                    recibo.estado = 'atrasado'
                else:
                    recibo.estado = 'pendiente'

                recibo_gasto.monto_usd = self.monto_usd
                recibo_gasto.save()
                recibo.save()

        except AttributeError as e:
            logger.warning(f"No se pudo actualizar recibo vinculado al gasto extra #{self.id}: {e}")

    def eliminar_recibo_vinculado(self):
        try:
            recibo_gasto = self.recibogastoextra_set.first()
            if recibo_gasto:
                recibo = recibo_gasto.recibo
                recibo_gasto.delete()
                recibo.delete()
        except AttributeError as e:
            logger.warning(f"No se pudo eliminar recibo vinculado al gasto extra #{self.id}: {e}")


    def save(self, *args, **kwargs):
        # Si es un gasto nuevo (no tiene ID aún) y no se ha modificado manualmente el saldo_pendiente
        if not self.pk and (self.saldo_pendiente == 0 or self.saldo_pendiente is None):
            self.saldo_pendiente = self.monto_usd
        super().save(*args, **kwargs)

    def __str__(self):
       return f"{self.apartamento} - {self.descripcion[:30]}..."

    class Meta:
        db_table = 'gastos_extra'

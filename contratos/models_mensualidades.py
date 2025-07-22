# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

from tasas.models import TasaDia

class Mensualidad(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('atrasado', 'Atrasado'),
        ('anulado', 'Anulado'),
    ]
    contrato = models.ForeignKey('contratos.Contrato', models.DO_NOTHING)
    fecha_generacion = models.DateField()
    fecha_vencimiento = models.DateField()
    monto_usd = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    comentario_anulacion = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk and (self.saldo_pendiente == 0 or self.saldo_pendiente is None):
            self.saldo_pendiente = self.monto_usd
        super().save(*args, **kwargs)

    @property
    def monto_bs_actual(self):
        # Si la mensualidad está pagada, devolver 0 o None porque no hay saldo
        if self.estado == 'pagado' or self.estado == 'anulado' :
            return Decimal('0.00')
    
        # Obtener la tasa del día más reciente (sin filtro de 'activa' porque no existe)
        tasa = TasaDia.objects.order_by('-fecha').first()
        if not tasa:
            # Si no hay tasa registrada, devolver None o 0, según convenga
            return None
        
        # Calcular monto en bolívares con la tasa actual
        monto_bs = Decimal(self.monto_usd) * tasa.valor_usd_bs
        return monto_bs.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def __str__(self):
        return f"{self.contrato} - {self.fecha_vencimiento} - {self.estado}"

    class Meta:
        db_table = 'mensualidades'

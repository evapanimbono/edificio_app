# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils import timezone

class TasaDia(models.Model):
    ESTADOS = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('anulada', 'Anulada'),
    ]
    fecha = models.DateField(unique=True)
    valor_usd_bs = models.DecimalField(max_digits=12, decimal_places=4)
    fuente = models.TextField(blank=True, null=True)
    registrada_por = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='registrada_por', blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='inactiva',editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        if not self.pk:  # Solo si es una nueva tasa
            # Desactivar cualquier otra tasa activa
            TasaDia.objects.filter(estado='activa').update(estado='inactiva')
            self.estado = 'activa'

        super().save(*args, **kwargs)

    def anular(self):
        from pagos.models import Pago  # Evitar import circular si lo necesitas

        if self.estado == 'anulada':
            return  # ya está anulada

        # Validar si hay pagos no anulados asociados a esta tasa
        pagos_asociados = Pago.objects.filter(tasa_usada=self, estado__in=["pendiente", "validado"])
        if pagos_asociados.exists():
            raise ValueError("No se puede anular la tasa porque tiene pagos asociados que no han sido anulados o rechazados.")

        self.estado = 'anulada'
        self.save()

        # Buscar la última tasa no anulada por fecha para reactivar
        ultima_activa = TasaDia.objects.filter(estado__in=['inactiva']).exclude(id=self.id).order_by('-fecha').first()
        if ultima_activa:
            ultima_activa.estado = 'activa'
            ultima_activa.save()

    def puede_eliminarse(self):
        return self.estado == 'anulada'

    def __str__(self):
        return f"{self.fecha} - {self.valor_usd_bs} Bs/USD"

    class Meta:
        db_table = 'tasas_dia'
        ordering = ['-fecha']

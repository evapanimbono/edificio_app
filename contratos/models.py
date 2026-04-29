# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .models_mensualidades import Mensualidad

class Contrato(models.Model):
    arrendatario = models.ForeignKey('usuarios.Usuario',on_delete=models.DO_NOTHING, related_name='contratos')
    apartamento = models.ForeignKey('edificios.Apartamento',  on_delete=models.DO_NOTHING, related_name='contratos')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    fecha_pago_mensual = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])
    monto_usd_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    archivo_contrato_pdf = models.FileField(
        upload_to='contratos/', 
        storage=None, # Opcional, usa el default
        max_length=255, 
        null=True, 
        blank=True
    )
    activo = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contrato de {self.arrendatario} en {self.apartamento}"

    class Meta:
        db_table = 'contratos'

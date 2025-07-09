# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class TasaDia(models.Model):
    fecha = models.DateField(unique=True)
    valor_usd_bs = models.DecimalField(max_digits=12, decimal_places=4)
    fuente = models.TextField(blank=True, null=True)
    registrada_por = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='registrada_por', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.fecha} - {self.valor_usd_bs} Bs/USD"

    class Meta:
        db_table = 'tasas_dia'

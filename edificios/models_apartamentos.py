# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Apartamento(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('en_mantenimiento', 'En mantenimiento'),
    ]
    edificio = models.ForeignKey('edificios.Edificio', models.DO_NOTHING)
    numero_apartamento = models.CharField(max_length=20)
    piso = models.IntegerField(blank=True, null=True)
    habitaciones = models.IntegerField()
    banos = models.IntegerField()
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True,choices=ESTADO_CHOICES)

    def __str__(self):
        return f"{self.edificio.nombre} - Apto {self.numero_apartamento}"

    class Meta:
        db_table = 'apartamentos'

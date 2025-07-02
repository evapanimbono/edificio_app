# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class LogAccion(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, blank=True, null=True)
    accion = models.TextField()
    tabla_afectada = models.TextField()
    registro_id = models.IntegerField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario} hizo {self.accion} en {self.tabla_afectada} (ID {self.registro_id})"

    class Meta:
        db_table = 'log_acciones'

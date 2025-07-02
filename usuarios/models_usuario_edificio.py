# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class UsuarioEdificio(models.Model):
    ROL_CHOICES = [
        ('administrador', 'Administrador'),
        ('colaborador', 'Colaborador'),
    ]
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.DO_NOTHING, related_name='edificios_asignados')
    edificio = models.ForeignKey('edificios.Edificio',on_delete=models.DO_NOTHING, related_name='usuarios_asignados')
    rol = models.CharField(max_length=50, choices=ROL_CHOICES)
    fecha_asignacion = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.usuario} en {self.edificio} como {self.rol}"

    class Meta:
        db_table = 'usuario_edificio'

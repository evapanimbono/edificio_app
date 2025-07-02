# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('recordatorio', 'Recordatorio'),
        ('anuncio', 'Anuncio'),
        ('personal', 'Mensaje Personal'),
    ]
    emisor = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, blank=True, null=True)
    receptor = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, related_name='notificaciones_receptor_set', blank=True, null=True)
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    leido = models.BooleanField(blank=True, null=True,default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.titulo} para {self.receptor}"

    class Meta:
        db_table = 'notificaciones'

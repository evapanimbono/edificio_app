# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from .models_respuestas import RespuestaEncuestas

class Encuesta(models.Model):
    titulo = models.TextField()
    descripcion = models.TextField(blank=True, null=True)
    enlace_formulario = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    creada_por = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='creada_por', blank=True, null=True)

    def __str__(self):
        return self.titulo

    class Meta:
        db_table = 'encuestas'

from django.db import models
from django.utils import timezone

class SolicitudUsuarioEdificio(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    ROL_CHOICES = [
        ('administrador', 'Administrador'),
        ('colaborador', 'Colaborador'),
    ]
    TIPO_CHOICES = [
        ('arrendador', 'Arrendador'),
        ('arrendatario', 'Arrendatario'),
    ]
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='solicitudes')
    edificio = models.ForeignKey('edificios.Edificio', on_delete=models.CASCADE, related_name='solicitudes')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    tipo_solicitado = models.CharField(max_length=20, choices=TIPO_CHOICES)
    rol_asignado = models.CharField(max_length=50, choices=ROL_CHOICES, null=True, blank=True)
    comentario_validador = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'solicitudes_usuario_edificio'
        ordering = ['-created_at']

    def __str__(self):
        return f"Solicitud de {self.usuario.username} para {self.edificio.nombre} como {self.tipo_solicitado} - Estado: {self.estado}"
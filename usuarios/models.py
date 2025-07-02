# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone

from .models_usuario_edificio import UsuarioEdificio
from .models_usuario_solicitud import SolicitudUsuarioEdificio

class UsuarioManager(BaseUserManager):
    def create_user(self, username, correo, password=None, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio")
        if not correo:
            raise ValueError("El correo es obligatorio")

        correo = self.normalize_email(correo)
        user = self.model(username=username, correo=correo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, correo, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(username, correo, password, **extra_fields)      

class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_CHOICES = [
        ('admin', 'Administrador del sistema'),
        ('arrendador', 'Arrendador'),
        ('arrendatario', 'Arrendatario'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('suspendido', 'Suspendido'),
        ('rechazado', 'Rechazado'),    
    ]
    username = models.CharField(max_length=150, unique=True)
    correo = models.EmailField(unique=True) 
    nuevo_correo = models.EmailField(null=True, blank=True)
    nombre_completo = models.TextField()
    telefono = models.TextField(blank=True, null=True)
    foto = models.TextField(blank=True, null=True)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, blank=True, null=True, choices=ESTADO_CHOICES)
    fecha_registro = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'correo'

    # Campos requeridos por Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['correo']

    objects = UsuarioManager()

    def __str__(self):
        return f"{self.username} ({self.tipo_usuario})"

    class Meta:
        db_table = 'usuarios'
 

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import Usuario, UsuarioEdificio

class CustomUserAdmin(UserAdmin):
    model = Usuario
    add_form = UserCreationForm
    form = UserChangeForm
    list_display = ('username', 'correo', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'tipo_usuario')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Información personal'), {'fields': ('correo', 'nombre_completo')}),
        (_('Permisos'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Fechas importantes'), {'fields': ('last_login',)}),
        (_('Tipo'), {'fields': ('tipo_usuario',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'correo', 'password1', 'password2', 'tipo_usuario', 'is_staff', 'is_active')}
        ),
    )
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('username', 'correo')
    ordering = ('username',)

admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(UsuarioEdificio)

# Register your models here.

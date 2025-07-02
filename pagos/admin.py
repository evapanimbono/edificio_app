from django.contrib import admin
from .models import Pago,PagoEfectivo,PagoTransferencias
from .models_recibos import Recibo, ReciboMensualidad, ReciboGastoExtra

@admin.register(Recibo)
class ReciboAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'total_usd', 'estado', 'created_at')
    search_fields = ('usuario__email',)
    list_filter = ('estado',)
    readonly_fields = ('created_at', 'updated_at')

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Solo superusers pueden eliminar

@admin.register(ReciboMensualidad)
class ReciboMensualidadAdmin(admin.ModelAdmin):
    list_display = ('recibo', 'mensualidad', 'monto_usd')

@admin.register(ReciboGastoExtra)
class ReciboGastoExtraAdmin(admin.ModelAdmin):
    list_display = ('recibo', 'gasto_extra', 'monto_usd')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'monto_total', 'estado_validacion', 'fecha_pago', 'fecha_validacion')
    list_filter = ('estado_validacion', 'tipo_pago')
    search_fields = ('usuario__email',)
    readonly_fields = ('created_at', 'updated_at', 'fecha_validacion')
    
admin.site.register(PagoEfectivo)
admin.site.register(PagoTransferencias)

# Register your models here.

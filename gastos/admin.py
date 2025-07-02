from django.contrib import admin
from .models import GastoExtra
from pagos.tareas import crear_recibo_para_gasto_extra
from log.models import LogAccion

@admin.register(GastoExtra)
class GastoExtraAdmin(admin.ModelAdmin):
    list_display = ('apartamento', 'descripcion', 'monto_usd', 'fecha_vencimiento')
    search_fields = ('descripcion',)
    exclude = ('saldo_pendiente', 'estado', 'fecha_generacion', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)

        if is_new:
            crear_recibo_para_gasto_extra(obj, creado_por=request.user)
            LogAccion.objects.create(
                usuario=request.user,
                accion="Creó gasto extra vía admin",
                tabla_afectada="gastos_extra",
                registro_id=obj.id,
                descripcion=f"Gasto extra creado para apartamento {obj.apartamento} con monto {obj.monto_usd}"
            )
# Register your models here.

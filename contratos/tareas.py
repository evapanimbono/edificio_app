from datetime import date,timedelta
from django.utils import timezone

from celery import shared_task

from contratos.models import Contrato
from contratos.models_mensualidades import Mensualidad
from tasas.models import TasaDia
from log.models import LogAccion
from usuarios.models import Usuario

from pagos.tareas import crear_recibo_para_mensualidad

@shared_task
def generar_mensualidades_automaticas(): #Genera mensualidades automáticas para contratos activos en la fecha de pago mensual

    hoy = date.today()
    contratos_activos = Contrato.objects.filter(activo=True)

    try:
        usuario_sistema = Usuario.objects.get(username='sistema')
    except Usuario.DoesNotExist:
        print("❌ Usuario 'sistema' no encontrado. No se pueden registrar logs.")
        usuario_sistema = None

    if not contratos_activos.exists():
        print("No hay contratos activos.")
        return

    tasa = TasaDia.objects.order_by('-fecha').first()
    if not tasa:
        print("⚠️ Advertencia: No hay tasa registrada. Se generarán mensualidades igual.")
    
    total_generadas = 0

    for contrato in contratos_activos:
        try:
            fecha_pago  = contrato.fecha_pago_mensual
            fecha_pago_este_mes = date(hoy.year, hoy.month, fecha_pago)

            if hoy < fecha_pago_este_mes:
                continue

            # Verificar si ya existe una mensualidad generada para esta fecha
            ya_generada = Mensualidad.objects.filter(
                contrato=contrato,
                fecha_generacion=fecha_pago_este_mes
            ).exists()

            if ya_generada:
                print(f"⚠️ Ya existe una mensualidad para contrato {contrato.id} en {fecha_pago_este_mes}")
                continue

            mensualidad = Mensualidad.objects.create(
                contrato=contrato,
                fecha_generacion=fecha_pago_este_mes,
                fecha_vencimiento=fecha_pago_este_mes + timedelta(days=5),
                monto_usd=contrato.monto_usd_mensual,
                saldo_pendiente=contrato.monto_usd_mensual,
                estado='pendiente',
            )

            if usuario_sistema:
                LogAccion.objects.create(
                    usuario=usuario_sistema,  # o un usuario del sistema si tienes uno definido para tareas automáticas
                    accion="generó mensualidad automática",
                    tabla_afectada="mensualidades",
                    registro_id=mensualidad.id,
                    descripcion=f"Mensualidad generada automáticamente para el contrato {contrato.id} con vencimiento {mensualidad.fecha_vencimiento}"
                )

            print(f"✅ Mensualidad generada para contrato {contrato.id} - {fecha_pago_este_mes}")
        
            total_generadas += 1

        except Exception as e:
            print(f"❌ Error generando mensualidad para contrato {contrato.id}: {e}")

    if total_generadas == 0:
        print("No se generaron nuevas mensualidades hoy.")
    else:
        print(f"🎉 Se generaron {total_generadas} mensualidades.")

        
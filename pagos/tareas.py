from datetime import date
from django.utils import timezone
from django.db import transaction

from celery import shared_task

from usuarios.models import Usuario
from contratos.models_mensualidades import Mensualidad
from gastos.models import GastoExtra
from pagos.models_recibos import Recibo, ReciboMensualidad, ReciboGastoExtra
from tasas.models import TasaDia
from log.models import LogAccion


@shared_task
def actualizar_estados_vencidos(): #Actualiza los estados de mensualidades y gastos extra vencidos
    hoy = date.today()
    usuario_sistema = Usuario.objects.filter(username='sistema').first()

    # Mensualidades vencidas
    mensualidades = Mensualidad.objects.filter(
        estado='pendiente',
        fecha_vencimiento__lt=hoy,
        saldo_pendiente__gt=0
    )
    for m in mensualidades:
        m.estado = 'atrasado'
        m.save()

        LogAccion.objects.create(
            usuario=usuario_sistema,  # lo hace el sistema
            accion='actualizó estado a atrasado',
            tabla_afectada='Mensualidad',
            registro_id=m.id,
            descripcion=f"Se marcó como atrasada la mensualidad con vencimiento {m.fecha_vencimiento}."
        )

    # Gastos extra vencidos
    gastos = GastoExtra.objects.filter(
        estado='pendiente',
        fecha_vencimiento__lt=hoy,
        saldo_pendiente__gt=0
    )
    for g in gastos:
        g.estado = 'atrasado'
        g.save()

        LogAccion.objects.create(
            usuario=usuario_sistema,
            accion='actualizó estado a atrasado',
            tabla_afectada='GastoExtra',
            registro_id=g.id,
            descripcion=f"Se marcó como atrasado el gasto extra con vencimiento {g.fecha_vencimiento}."
        )

def generar_recibo_para_pago(pago, usuario):
    """
    Crea un único recibo para un pago validado, incluyendo todas las mensualidades
    y gastos extra pagados, y sus asociaciones correspondientes.
    """

    if not pago.validado_por:
        raise ValueError("No se puede generar un recibo para un pago no validado.")

    recibo = Recibo.objects.create(
        usuario=pago.usuario,  # El arrendatario dueño del pago
        fecha_emision=pago.fecha_pago,
        total_usd=pago.monto_total,
        total_bs=pago.monto_bs,
        estado='pagado',
        observaciones=f"Recibo generado por el pago #{pago.id}.",
        creado_por=usuario,
        pago=pago
    )

    LogAccion.objects.create(
        usuario=usuario,
        accion="creó un recibo",
        tabla_afectada="recibos",
        registro_id=recibo.id,
        descripcion=f"Recibo #{recibo.id} creado para pago #{pago.id}."
    )

    #Asociar mensualidades al recibo
    for pm in pago.mensualidades_pagadas.all(): # asegúrate de tener esta lista antes
        ReciboMensualidad.objects.create(
            recibo=recibo,
            mensualidad=pm.mensualidad,
            monto_usd=pm.monto_pagado
        )

        LogAccion.objects.create(
            usuario=usuario,
            accion="asoció mensualidad a recibo",
            tabla_afectada="ReciboMensualidad",
            registro_id=pm.mensualidad.id,
            descripcion=f"Mensualidad #{pm.mensualidad.id} asociada al recibo #{recibo.id}"
        )

    # Asociar gastos extra al mismo recibo
    for pg in pago.gastos_pagados.all():  # asegúrate de tener esta lista antes
        ReciboGastoExtra.objects.create(
            recibo=recibo,
            gasto_extra=pg.gasto,
            monto_usd=pg.monto_pagado
        )

        LogAccion.objects.create(
            usuario=usuario,
            accion="asoció gasto extra a recibo",
            tabla_afectada="ReciboGastoExtra",
            registro_id=pg.gasto.id,
            descripcion=f"Gasto extra #{pg.gasto.id} asociado al recibo #{recibo.id}"
        )

#====================================================================================================================================================================
#YA NO SE USAN PORQUE EL RECIBO SE CREA EN LAS VISTAS REGISTRARPAGO (PARA ARRENDADOR) Y VALIDARPAGO (PARA ARRENDATARIO)
def crear_recibo_para_mensualidad(mensualidad, pago, creado_por): #Crea un recibo para una mensualidad nueva (depende de contratos.tareas.crear_mensualidad)
    """
    Crea un recibo automático para un pago de mensualidad.

    Args:
        mensualidad (Mensualidad): Instancia de la mensualidad pagada.
        pago (Pago): Instancia del pago validado.
        creado_por (Usuario): Usuario que registra o valida el pago.

    Returns:
        Recibo: El recibo creado.
    """

    if not mensualidad:
        raise ValueError("La mensualidad no puede ser None.")

    if not pago:
        raise ValueError("El pago no puede ser None.")

    if not creado_por:
        raise ValueError("El usuario que crea el recibo no puede ser None.")

    recibo = Recibo.objects.create(
        usuario=mensualidad.contrato.arrendatario,
        fecha_emision=pago.fecha_pago,
        total_usd=pago.monto_total,
        total_bs=pago.monto_bs,
        estado='pagado',
        observaciones=f"Recibo generado por pago de mensualidad #{mensualidad.id}",
        creado_por=creado_por
    )

    ReciboMensualidad.objects.create(
        recibo=recibo,
        mensualidad=mensualidad,
        monto_usd=pago.monto_total,
    )

    # 📝 Log de creación de recibo por mensualidad
    LogAccion.objects.create(
        usuario=creado_por,
        accion="generó un recibo para mensualidad",
        tabla_afectada="Recibo",
        registro_id=recibo.id,
        descripcion=(
            f"Recibo #{recibo.id} generado tras pago de mensualidad #{mensualidad.id}. "
            f"Monto: ${pago.monto_total} / Bs {pago.monto_bs}."
        )
    )

    print(f"🧾 Recibo #{recibo.id} generado para mensualidad {mensualidad.id}")
    return recibo

def crear_recibo_para_gasto_extra(gasto,pago, creado_por): #Crea un recibo para un gasto extra manual
    """
    Crea un recibo automático para un pago de gasto extra.

    Args:
        gasto_extra (GastoExtra): Instancia del gasto extra pagado.
        pago (Pago): Objeto de pago asociado.
        creado_por (Usuario): Usuario que registra o valida el pago.

    Returns:
        Recibo: El recibo creado.
    """

    if not gasto:
        raise ValueError("El gasto extra no puede ser None.")

    if not pago:
        raise ValueError("El pago no puede ser None.")

    if not creado_por:
        raise ValueError("El usuario que crea el recibo no puede ser None.")

    recibo = Recibo.objects.create(
        usuario=gasto.arrendatario,
        fecha_emision=pago.fecha_pago,
        total_usd=pago.monto_total,
        total_bs=pago.monto_bs,
        estado='pagado',
        observaciones=f"Recibo generado por pago de gasto extra #{gasto.id}",
        creado_por=creado_por
    )

    ReciboGastoExtra.objects.create(
        recibo=recibo,
        gasto_extra=gasto,
        monto_usd=pago.monto_total
    )

    # 📝 Log de creación de recibo por gasto extra
    LogAccion.objects.create(
        usuario=creado_por,
        accion="generó un recibo para gasto extra",
        tabla_afectada="Recibo",
        registro_id=recibo.id,
        descripcion=(
            f"Recibo #{recibo.id} generado tras pago de gasto extra #{gasto.id}. "
            f"Monto: ${pago.monto_total} / Bs {pago.monto_bs}."
        )
    )

    print(f"🧾 Recibo #{recibo.id} generado para gasto extra {gasto.id}")
    return recibo

def actualizar_estado_recibo_si_pagado(recibo, pago=None): #Actualiza el estado del recibo a pagado si todos los items están pagados y validados
    """
    Revisa si todos los ítems del recibo están pagados.
    Si es así, marca el recibo como 'pagado'.
    Además, actualiza monto_bs_pagado en cada item si se pasó un pago con tasa.
    """
    recibo.refresh_from_db()
    tiene_items = False

    for rm in recibo.mensualidades.all():
        tiene_items = True
        if rm.mensualidad.saldo_pendiente > 0:
            print(f"⛔ Recibo #{recibo.id} tiene mensualidad #{rm.mensualidad.id} con saldo pendiente: {rm.mensualidad.saldo_pendiente}")
            return
        
        # ✅ Actualizar monto_bs_pagado si hay un pago con tasa
        if pago and pago.tasa_usd:
            rm.monto_bs_pagado = rm.monto_usd * pago.tasa_usd
            rm.save()

    for rg in recibo.gastos.all():
        tiene_items = True
        if rg.gasto_extra.saldo_pendiente > 0:
            print(f"⛔ Recibo #{recibo.id} tiene gasto #{rg.gasto_extra.id} con saldo pendiente: {rg.gasto_extra.saldo_pendiente}")
            return
        
        # ✅ Actualizar monto_bs_pagado si hay un pago con tasa
        if pago and pago.tasa_usd:
            rg.monto_bs_pagado = rg.monto_usd * pago.tasa_usd
            rg.save()

    if tiene_items and recibo.estado != 'pagado':

        # ✅ Calcular total_bs del recibo como suma de lo pagado en Bs
        if pago and pago.tasa_usd:
            total_bs_pagado = 0

            for rm in recibo.mensualidades.all():
                total_bs_pagado += rm.monto_bs_pagado or 0

            for rg in recibo.gastos.all():
                total_bs_pagado += rg.monto_bs_pagado or 0

            recibo.total_bs = total_bs_pagado

        recibo.estado = 'pagado'
        recibo.save()

        descripcion_log = f"Recibo marcado como pagado."
        if pago:
            descripcion_log += f" Causado por pago #{pago.id} validado."

        # Crear log de cambio de estado
        usuario_sistema = Usuario.objects.filter(username='sistema').first()
        LogAccion.objects.create(
            usuario=usuario_sistema,
            accion='actualizó estado a pagado',
            tabla_afectada='Recibo',
            registro_id=recibo.id,
            descripcion=descripcion_log
        )

        print(f"✅ Recibo #{recibo.id} marcado como pagado.")
#====================================================================================================================================================================


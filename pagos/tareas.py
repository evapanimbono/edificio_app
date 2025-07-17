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

def crear_recibo_para_mensualidad(mensualidad, creado_por): #Crea un recibo para una mensualidad nueva (depende de contratos.tareas.crear_mensualidad)
    """
    Crea un recibo automático para una mensualidad nueva.

    Args:
        mensualidad (Mensualidad): Instancia de la mensualidad.
        creado_por (Usuario or None): Usuario que dispara la acción (puede ser None si es automático).

    Returns:
        Recibo or None: El recibo creado, o None si ya existía uno pendiente/atrasado.
    """
    if not mensualidad:
        raise ValueError("La mensualidad no puede ser None.")

    # Evitar duplicados si ya hay un recibo activo para esta mensualidad
    if ReciboMensualidad.objects.filter(
        mensualidad=mensualidad,
        recibo__estado__in=['pendiente', 'atrasado']
    ).exists():
        print(f"⚠️ Ya existe un recibo pendiente/atrasado para mensualidad {mensualidad.id}")
        return None

    # Buscar la tasa más reciente
    tasa = TasaDia.objects.order_by('-fecha').first()
    if not tasa:
        raise ValueError("❌ No hay tasa registrada para generar el recibo.")

    total_usd = mensualidad.monto_usd
    total_bs = None

    if not creado_por:
        try:
            creado_por = Usuario.objects.get(username='sistema')
        except Usuario.DoesNotExist:
            print("❌ Usuario 'sistema' no encontrado. No se puede crear el recibo.")
            return

    estado = 'atrasado' if mensualidad.fecha_vencimiento < timezone.now().date() else 'pendiente'

    recibo = Recibo.objects.create(
        usuario=mensualidad.contrato.arrendatario,
        fecha_vencimiento=mensualidad.fecha_vencimiento,
        total_usd=total_usd,
        total_bs=None,
        estado=estado,
        observaciones="Recibo generado automáticamente para mensualidad.",
        creado_por=creado_por
    )

    ReciboMensualidad.objects.create(
        recibo=recibo,
        mensualidad=mensualidad,
        monto_usd=total_usd
    )

    # 📝 Log de creación de recibo por mensualidad
    LogAccion.objects.create(
        usuario=creado_por,
        accion="generó un recibo para mensualidad",
        tabla_afectada="Recibo",
        registro_id=recibo.id,
        descripcion=(
            f"Recibo #{recibo.id} generado automáticamente para mensualidad #{mensualidad.id}. "
            f"Vencimiento: {recibo.fecha_vencimiento}, Monto: ${total_usd}."
        )
    )

    print(f"🧾 Recibo #{recibo.id} generado para mensualidad {mensualidad.id}")
    return recibo

def crear_recibo_para_gasto_extra(gasto, creado_por): #Crea un recibo para un gasto extra manual
    """
    Crea un recibo automáticamente para un gasto extra manual.
    """
    if not gasto or not gasto.apartamento:
        return None

    # Evitar duplicados
    ya_existe = ReciboGastoExtra.objects.filter(
        gasto_extra=gasto,
        recibo__estado__in=['pendiente', 'atrasado']
    ).exists()
    if ya_existe:
        return None

    tasa = TasaDia.objects.order_by('-fecha').first()
    if not tasa:
        raise ValueError("No hay tasa registrada para generar el recibo")

    total_usd = gasto.monto_usd
    total_bs = None

    # Buscar contrato activo para saber a qué usuario se le asigna
    contrato = gasto.apartamento.contratos.filter(activo=True).first()
    if not contrato:
        raise ValueError("No hay contrato activo para el apartamento asociado al gasto")

    if not creado_por:
        creado_por = Usuario.objects.filter(username='sistema').first()

    recibo = Recibo.objects.create(
        usuario=contrato.arrendatario,
        fecha_vencimiento=gasto.fecha_vencimiento,
        total_usd=total_usd,
        total_bs=None,
        observaciones="Recibo generado automáticamente para gasto extra.",
        creado_por=creado_por
    )

    ReciboGastoExtra.objects.create(
        recibo=recibo,
        gasto_extra=gasto,
        monto_usd=total_usd
    )

    # 📝 Log de creación de recibo por gasto extra
    LogAccion.objects.create(
        usuario=creado_por,
        accion="generó un recibo para gasto extra",
        tabla_afectada="Recibo",
        registro_id=recibo.id,
        descripcion=(
            f"Recibo #{recibo.id} generado automáticamente para mensualidad #{gasto.id}. "
            f"Vencimiento: {recibo.fecha_vencimiento}, Monto: ${total_usd}."
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
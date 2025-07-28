from django.shortcuts import render,get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics,status,filters,permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView,RetrieveAPIView
from rest_framework.exceptions import PermissionDenied

from datetime import datetime
from decimal import Decimal,InvalidOperation

from .models import Pago,PagoEfectivo,PagoTransferencias,PagoMensualidad, PagoGastoExtra
from .serializers_pagos import (
    PagoSerializer,
    PagoRegistroSerializer,
    DetallePagoSerializer,
    AnularPagoSerializer,
    AccionValidarPagoSerializer
)
from .filters import PagoFilter
from .permisos import EsArrendadorYAdministraElPago, EsArrendadorYAdministraElRecibo, EsArrendatarioYEsDueñoDelRecibo
from pagos.tareas import generar_recibo_para_pago

from .models_recibos import Recibo
from .serializers_recibos import (
    ReciboSerializer,
)

from usuarios.permissions import EsArrendatario,EsArrendador

from contratos.models import Contrato
from contratos.models_mensualidades import Mensualidad

from gastos.models import GastoExtra

from tasas.models import TasaDia

from edificios.models import Apartamento

from log.models import LogAccion

#====================================================== PAGOS ================================================================== 
#Muestra los pagos asociados al arrendador (sus apartamentos)
class ListaPagosAPIView(generics.ListAPIView):
    
    serializer_class = PagoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PagoFilter
    permission_classes = [IsAuthenticated] 
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        usuario = self.request.user

        if usuario.tipo_usuario == 'arrendatario':
            return Pago.objects.filter(usuario=usuario)
        
        elif usuario.tipo_usuario == 'arrendador':
            edificios = usuario.edificios_asignados.values_list('edificio_id', flat=True)
            apartamentos = Apartamento.objects.filter(edificio_id__in=edificios)
            contratos = Contrato.objects.filter(apartamento__in=apartamentos)
            usuarios = contratos.values_list('arrendatario_id', flat=True).distinct()
            return Pago.objects.filter(usuario_id__in=usuarios)

        return Pago.objects.none()

#Permite registrar un pago de mensualidades y/o gastos extra. El arrendatario lo deja en estado pendiente, el arrendador lo puede validar automáticamente.
class RegistrarPagoView(GenericAPIView):
    """Permite registrar un pago de mensualidades y/o gastos extra. El arrendatario lo deja en estado pendiente, el arrendador lo puede validar automáticamente."""

    
    permission_classes = [IsAuthenticated]
    serializer_class = PagoRegistroSerializer

    @transaction.atomic
    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        data = serializer.validated_data

        mensualidades_data = data.get("mensualidades", [])
        gastos_extra_data = data.get("gastos_extra", [])

        mensualidades = Mensualidad.objects.filter(id__in=[m["id"] for m in mensualidades_data])
        gastos_extra = GastoExtra.objects.filter(id__in=[g["id"] for g in gastos_extra_data])

        # Si el usuario es arrendador, el dueño real es el arrendatario asociado
        if request.user.tipo_usuario == 'arrendador':
            if mensualidades.exists():
                usuario_dueño = mensualidades.first().usuario
            elif gastos_extra.exists():
                usuario_dueño = gastos_extra.first().usuario
            else:
                raise ValidationError("No se especificaron mensualidades ni gastos extra.")
        else:
            usuario_dueño = request.user

        tipo_usuario = request.user.tipo_usuario

        try:
            monto = Decimal(data.get("monto_total"))
        except (InvalidOperation, TypeError):
            return Response({"error": "Monto total inválido."}, status=400)
            
        tipo_pago = data.get("tipo_pago", "efectivo")  # 'efectivo', 'transferencia', 'mixto'
        fecha_pago = data.get("fecha_pago")
        
        mensualidades_data = data.get("mensualidades", [])
        gastos_extra_data = data.get("gastos_extra", [])

        if not mensualidades_data and not gastos_extra_data:
            return Response({"error": "Debes especificar al menos una mensualidad o gasto extra."}, status=400)

        monto_acumulado = Decimal('0.00')

        tasa = data.get("tasa_dia")
        if tipo_usuario == 'arrendador':
            if not tasa:
                return Response({"error": "Debes seleccionar una tasa si eres arrendador."}, status=400)
        else:
            tasa = TasaDia.objects.order_by('-fecha').first()
            if not tasa:
                return Response({"error": "No hay una tasa registrada para calcular el monto en Bs."}, status=400)

        monto_bs = round(monto * tasa.valor_usd_bs)

        # Crear el pago principal
        pago = Pago.objects.create(
            usuario=usuario_dueño,
            monto_total=monto,
            monto_bs=monto_bs,
            tasa_usd=tasa.valor_usd_bs,
            tasa_dia=tasa, 
            fecha_pago=fecha_pago,
            tipo_pago=tipo_pago,
            estado_validacion="validado" if tipo_usuario == 'arrendador' else "pendiente",
            validado_por=request.user if tipo_usuario == 'arrendador' else None,
            fecha_validacion=timezone.now() if tipo_usuario == 'arrendador' else None
        )

        # 💬 Agregar log del registro de pago
        LogAccion.objects.create(
            usuario=request.user,
            accion="registró un nuevo pago",
            tabla_afectada="pagos",
            registro_id=pago.id,
            descripcion=f"Tipo: {tipo_pago}, Monto: {monto}, Fecha: {fecha_pago}"
        )

        mensualidades_pagadas = []
        # Procesar mensualidades
        for item in mensualidades_data:
            mensualidad = get_object_or_404(Mensualidad, id=item["id"], estado__in=["pendiente", "atrasado"])

            if tipo_usuario == "arrendatario" and mensualidad.contrato.arrendatario_id != request.user.id:
                return Response({"error": f"No tienes permiso para pagar la mensualidad {mensualidad.id}."}, status=403)

            try:
                monto_item = Decimal(item["monto"])
            except (InvalidOperation, TypeError):
                return Response({"error": f"Monto inválido en mensualidad {item['id']}."}, status=400) 
            
            if monto_item <= 0 or monto_item > mensualidad.saldo_pendiente:
                return Response({"error": f"El monto para la mensualidad {mensualidad.id} excede el saldo pendiente o es inválido."}, status=400)
    
            PagoMensualidad.objects.create(
                pago=pago,
                mensualidad=mensualidad,
                monto_pagado=monto_item
            )

            # Si el que registra es arrendador, actualizar saldo y estado aquí
            if tipo_usuario == 'arrendador':
                mensualidad.saldo_pendiente -= monto_item
                mensualidad.saldo_pendiente = max(Decimal('0.00'), mensualidad.saldo_pendiente)
                if mensualidad.saldo_pendiente == 0:
                    mensualidad.estado = 'pagado'
                mensualidad.save()

            mensualidades_pagadas.append((mensualidad, monto_item))

            # 💬 Agregar log del registro de pago de una mensualidad
            LogAccion.objects.create(
                usuario=request.user,
                accion="asoció una mensualidad al pago",
                tabla_afectada="pagos_mensualidades",
                registro_id=mensualidad.id,
                descripcion=f"Pago #{pago.id}, Mensualidad #{mensualidad.id}, Monto pagado: {monto_item}"
            )

            monto_acumulado += monto_item

        gastos_pagados = []
        # Procesar gastos extra
        for item in gastos_extra_data:
            gasto = get_object_or_404(GastoExtra, id=item["id"], estado__in=["pendiente", "atrasado"])

            if tipo_usuario == "arrendatario":
                contrato = Contrato.objects.filter(apartamento=gasto.apartamento, arrendatario=request.user, activo=True).first()
                if not contrato:
                    return Response({"error": f"No tienes permiso para pagar el gasto extra {gasto.id}."}, status=403)

            try:
                monto_item = Decimal(item["monto"])
            except (InvalidOperation, TypeError):
                return Response({"error": f"Monto inválido en gasto extra {item['id']}."}, status=400)
                
            if monto_item <= 0 or monto_item > gasto.saldo_pendiente:
                return Response({"error": f"El monto para el gasto extra {gasto.id} excede el saldo pendiente o es inválido."}, status=400)

            PagoGastoExtra.objects.create(
                pago=pago,
                gasto_extra=gasto,
                monto_pagado=monto_item
            )

            # Si el que registra es arrendador, actualizar saldo y estado aquí
            if tipo_usuario == 'arrendador':
                gasto.saldo_pendiente -= monto_item
                gasto.saldo_pendiente = max(Decimal('0.00'), gasto.saldo_pendiente)
                if gasto.saldo_pendiente == 0:
                    gasto.estado = 'pagado'
                gasto.save()

            gastos_pagados.append((gasto, monto_item))

            # 💬 Agregar log del registro de pago de un gasto extra
            LogAccion.objects.create(
                usuario=request.user,
                accion="asoció un gasto extra al pago",
                tabla_afectada="pagos_gastos_extra",
                registro_id=gasto.id,
                descripcion=f"Pago #{pago.id}, GastoExtra #{gasto.id}, Monto pagado: {monto_item}"
            )

            monto_acumulado += monto_item

        # Verificación final del total
        if monto_acumulado != monto:

            LogAccion.objects.create(
                usuario=request.user,
                accion="falló intento de registro de pago",
                tabla_afectada="pagos",
                registro_id=pago.id,
                descripcion=f"El monto total asignado ({monto_acumulado}) no coincide con el monto ingresado ({monto})."
            )
            
            return Response({
                "error": f"El total asignado ({monto_acumulado}) no coincide con el monto enviado ({monto})."
            }, status=400)

        # Registrar efectivo (opcional)
        efectivo_data = data.get("efectivo", [])
        for billete in efectivo_data:
            PagoEfectivo.objects.create(
                pago=pago,
                denominacion=billete.get("denominacion"),
                serial=billete.get("serial"),
                foto_billete=billete.get("foto_billete")
            )
        
        if efectivo_data:
            LogAccion.objects.create(
                usuario=request.user,
                accion="registró pago en efectivo",
                tabla_afectada="pagos_efectivo",
                registro_id=pago.id,
                descripcion=f"Pago #{pago.id} con {len(efectivo_data)} billetes registrados en efectivo."
            )

        # Registrar transferencia (opcional)
        transferencia_data = data.get("transferencia")
        if transferencia_data:
            try:
                monto_bs_transferido = Decimal(transferencia_data.get("monto_bs", "0.00"))
            except (InvalidOperation, TypeError):
                return Response({"error": "Monto Bs. de la transferencia inválido."}, status=400)

            # Validar que venga la fecha de transferencia
            fecha_transferencia_str = transferencia_data.get("fecha_transferencia")
            if not fecha_transferencia_str:
                return Response({"error": "Debes indicar la fecha de la transferencia."}, status=400)

            fecha_transferencia = fecha_transferencia_str
            if isinstance(fecha_transferencia, str):
                try:
                    fecha_transferencia = datetime.strptime(fecha_transferencia, "%Y-%m-%d").date()
                except ValueError:
                    return Response({"error": "Formato de fecha de transferencia inválido. Usa AAAA-MM-DD."}, status=400)

            # Buscar la tasa correspondiente a esa fecha
            tasa_fecha = TasaDia.objects.filter(fecha=fecha_transferencia).first()
            if not tasa_fecha:
                return Response({"error": f"No hay tasa registrada para el día {fecha_transferencia}."}, status=400)

             # Calcular cuánto debería haber transferido en Bs
            total_efectivo = sum(Decimal(b.get("denominacion") or 0) for b in data.get("efectivo", []))
            monto_usd_a_transferir = pago.monto_total - total_efectivo

            monto_bs_esperado = round(monto_usd_a_transferir * tasa_fecha.valor_usd_bs, 2)
            diferencia = abs(monto_bs_transferido - monto_bs_esperado)

            if diferencia > Decimal("1.00"):
                return Response({
                    "error": f"El monto Bs. transferido ({monto_bs_transferido}) no coincide con el estimado ({monto_bs_esperado}) según la tasa del {fecha_transferencia}."
                }, status=400)
            
            PagoTransferencias.objects.create(
                pago=pago,
                banco_destino=transferencia_data.get("banco_destino"),
                cuenta_destino=transferencia_data.get("cuenta_destino"),
                referencia=transferencia_data.get("referencia"),
                monto_bs=monto_bs_transferido,
                fecha_transferencia=fecha_transferencia,
                comprobante_img=transferencia_data.get("comprobante_img")
            )

            # ✅ Agregar log de transferencia
            LogAccion.objects.create(
                usuario=request.user,
                accion="registró pago por transferencia",
                tabla_afectada="pagos_transferencias",
                registro_id=pago.id,
                descripcion=f"Pago #{pago.id} registrado por transferencia. Referencia: {transferencia_data.get('referencia')}, Monto Bs: {monto_bs_transferido}"
            )

        if tipo_usuario == 'arrendador':
            generar_recibo_para_pago(pago, request.user)

        return Response({
            "mensaje": "Pago registrado correctamente",
            "pago_id": pago.id
        })

#Permite que el arrendador valide un pago registrado por un arrendatario     
class ValidarPagoView(APIView): 
    
    permission_classes = [IsAuthenticated, EsArrendador, EsArrendadorYAdministraElPago]

    @swagger_auto_schema(request_body=AccionValidarPagoSerializer)
    @transaction.atomic
    def post(self, request, pago_id):
        try:
            pago = get_object_or_404(Pago, id=pago_id, estado_validacion='pendiente')
            self.check_object_permissions(request, pago)

        except Pago.DoesNotExist:
            return Response({'error': 'Pago no encontrado o ya validado'}, status=status.HTTP_404_NOT_FOUND)
            
        # Verifica que el usuario sea arrendador ahora se hace desde permisos
        #if request.user.tipo != 'arrendador':
        #    return Response({'error': 'No tiene permisos para validar pagos'}, status=status.HTTP_403_FORBIDDEN)

        accion = request.data.get("accion", "validar")  # Puede ser 'validar' o 'rechazar'
        observacion = request.data.get("observacion", "")  # Opcional para rechazos

        if accion not in ['validar', 'rechazar']:
            return Response({'error': 'Acción inválida. Usa "validar" o "rechazar".'}, status=400)

        if accion == "rechazar" and not observacion:
            return Response({'error': 'Debes indicar una observación al rechazar un pago.'}, status=400)

        if accion == "validar":
            # Validar el pago
            pago.estado_validacion = 'validado'
            pago.validado_por = request.user
            pago.fecha_validacion = timezone.now()
            pago.observaciones = ''
            pago.save()

            # 🔐 Log de validación
            LogAccion.objects.create(
                usuario=request.user,
                accion="validó un pago",
                tabla_afectada="pagos",
                registro_id=pago.id,
                descripcion=f"Pago validado por {request.user.username} el {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Actualizar mensualidades
            for pago_m in pago.mensualidades_pagadas.all():
                mensualidad = pago_m.mensualidad
                mensualidad.saldo_pendiente -= pago_m.monto_pagado
                mensualidad.saldo_pendiente = max(Decimal('0.00'), mensualidad.saldo_pendiente)
                if mensualidad.saldo_pendiente == 0:
                    mensualidad.estado = 'pagado'
                mensualidad.save()

            # Actualizar gastos extra
            for pago_g in pago.gastos_pagados.all():
                gasto = pago_g.gasto_extra
                gasto.saldo_pendiente -= pago_g.monto_pagado
                gasto.saldo_pendiente = max(Decimal('0.00'), gasto.saldo_pendiente)
                if gasto.saldo_pendiente == 0:
                    gasto.estado = 'pagado'
                gasto.save()

            # Crear recibo general
            recibo = generar_recibo_para_pago(pago, request.user)

            return Response({
                'mensaje': 'Pago validado correctamente y recibo generado',
                'recibo_id': recibo.id
            }, status=status.HTTP_200_OK)
            
        elif accion == "rechazar":
            # ❌ Rechazar pago
            pago.estado_validacion = 'rechazado'
            pago.validado_por = request.user
            pago.fecha_validacion = timezone.now()
            pago.observaciones = observacion 
            pago.save()

            # 📝 Log de rechazo
            LogAccion.objects.create(
                usuario=request.user,
                accion="rechazó un pago",
                tabla_afectada="pagos",
                registro_id=pago.id,
                descripcion=f"Pago rechazado por {request.user.username} el {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}. Motivo: {observacion or 'No especificado'}"
            )

            return Response({'mensaje': 'Pago rechazado correctamente'}, status=200)

#Permite que el arrendatario vea su historial de pagos (solo los ya validados)    
class HistorialPagosView(APIView): 
    
    permission_classes = [IsAuthenticated, EsArrendatario]

    def get(self, request):
        usuario = request.user

        pagos = Pago.objects.filter(usuario=usuario, estado_validacion="validado").order_by('-fecha_pago')

        data = []
        for pago in pagos:
            mensualidades = pago.mensualidades_pagadas.select_related('mensualidad').all()
            gastos_extra = pago.gastos_pagados.select_related('gasto_extra').all()

            mensualidades_data = [{
                "id": pm.mensualidad.id,
                "fecha_vencimiento": pm.mensualidad.fecha_vencimiento,
                "monto_asignado": pm.monto_pagado,
                "monto_total_mensualidad": pm.mensualidad.monto_usd,
            } for pm in mensualidades]

            gastos_extra_data = [{
                "id": ge.gasto_extra.id,
                "descripcion": ge.gasto_extra.descripcion,
                "monto_asignado": ge.monto_pagado,
                "monto_total_gasto": ge.gasto_extra.monto_usd,
            } for ge in gastos_extra]

            data.append({
                "pago_id": pago.id,
                "fecha_pago": pago.fecha_pago,
                "monto_total": pago.monto_total,
                "tipo_pago": pago.tipo_pago,
                "mensualidades": mensualidades_data,
                "gastos_extra": gastos_extra_data,
            })

        return Response(data)   
    
#Permite que el arrendador vea los detalles de un pago específico (pendiente, validado o rechazado)
class DetallePagoView(RetrieveAPIView): 
    permission_classes = [IsAuthenticated]
    queryset = Pago.objects.all()
    serializer_class = DetallePagoSerializer
    lookup_field = 'id'  # se usará en la URL como /pagos/detalle/<id>/

    def get_object(self):
        pago = super().get_object()
        user = self.request.user

        # Solo arrendadores pueden entrar
        if user.tipo_usuario != 'arrendador':
            raise PermissionDenied("Solo los arrendadores pueden acceder a esta vista.")

        # Verificar que administre edificio relacionado con el pago
        edificio_ids = user.edificios_asignados.values_list('edificio_id', flat=True)

        tiene_mensualidad = pago.mensualidades_pagadas.filter(
            mensualidad__contrato__apartamento__edificio_id__in=edificio_ids
        ).exists()

        tiene_gasto = pago.gastos_pagados.filter(
            gasto_extra__apartamento__edificio_id__in=edificio_ids
        ).exists()

        if not (tiene_mensualidad or tiene_gasto):
            raise PermissionDenied("No tienes permiso para ver este pago.")

        return pago

#Detalle de pago previo (antes de registrar el pago)
class DetallePagoPrevioAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuario = request.user
        mensualidades_ids = request.data.get('mensualidades', [])
        gastos_extra_ids = request.data.get('gastos_extra', [])
        tipo_pago = request.data.get('tipo_pago')
        fecha_transferencia_str = request.data.get('fecha_transferencia', None)

        if not mensualidades_ids and not gastos_extra_ids:
            return Response({"error": "Debes enviar al menos una mensualidad o gasto extra."}, status=400)
        
        if tipo_pago not in ['efectivo', 'transferencia', 'mixto']:
            return Response({"error": "Tipo de pago inválido."}, status=400)

        # Validar formato y existencia de fecha transferencia si aplica
        if tipo_pago in ['transferencia', 'mixto']:
            if not fecha_transferencia_str:
                return Response({"error": "Debes enviar la fecha de transferencia para este tipo de pago."}, status=400)
            try:
                fecha_transferencia = datetime.strptime(fecha_transferencia_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Formato inválido para fecha_transferencia. Usa AAAA-MM-DD."}, status=400)
            tasa = TasaDia.objects.filter(fecha=fecha_transferencia).first()
            if not tasa:
                return Response({"error": f"No hay tasa registrada para la fecha {fecha_transferencia}."}, status=400)
        else:
            tasa = TasaDia.objects.order_by('-fecha').first()
            if not tasa:
                return Response({"error": "No hay tasa registrada."}, status=400)

        # Validar que mensualidades_ids y gastos_extra_ids sean listas de dicts con 'id'
        try:
            mensualidades_id_list = [m['id'] for m in mensualidades_ids if 'id' in m]
            gastos_extra_id_list = [g['id'] for g in gastos_extra_ids if 'id' in g]
        except Exception:
            return Response({"error": "Formato inválido para mensualidades o gastos extra."}, status=400)

        # Obtener mensualidades y validar acceso
        mensualidades = Mensualidad.objects.filter(
            id__in=mensualidades_id_list,
            estado__in=['pendiente', 'atrasado']
        ).select_related('contrato', 'contrato__arrendatario')

        for m in mensualidades:
            if usuario.tipo_usuario == 'arrendatario' and m.contrato.arrendatario_id != usuario.id:
                return Response({"error": f"No tienes permiso para la mensualidad {m.id}."}, status=403)

        # Obtener gastos extra y validar acceso
        gastos = GastoExtra.objects.filter(
            id__in=gastos_extra_id_list,
            estado__in=['pendiente', 'atrasado']
        ).select_related('apartamento')

        for g in gastos:
            if usuario.tipo_usuario == 'arrendatario':
                contrato = Contrato.objects.filter(apartamento=g.apartamento, arrendatario=usuario, activo=True).first()
                if not contrato:
                    return Response({"error": f"No tienes permiso para el gasto extra {g.id}."}, status=403)

        total_usd = Decimal('0.00')
        detalle = {"mensualidades": [], "gastos_extra": []}

        for m in mensualidades:
            if m.saldo_pendiente > 0:
                monto_usd = m.saldo_pendiente
                monto_bs = monto_usd * tasa.valor_usd_bs
                total_usd += monto_usd
                detalle["mensualidades"].append({
                    "id": m.id,
                    "monto_usd": float(monto_usd),
                    "monto_bs": float(round(monto_bs, 2)),
                    "fecha_vencimiento": m.fecha_vencimiento,
                    "estado": m.estado
                })

        for g in gastos:
            if g.saldo_pendiente > 0:
                monto_usd = g.saldo_pendiente
                monto_bs = monto_usd * tasa.valor_usd_bs
                total_usd += monto_usd
                detalle["gastos_extra"].append({
                    "id": g.id,
                    "monto_usd": float(monto_usd),
                    "monto_bs": float(round(monto_bs, 2)),
                    "descripcion": g.descripcion,
                    "fecha_vencimiento": g.fecha_vencimiento,
                    "estado": g.estado
                })

        if total_usd == 0:
            return Response({"error": "No hay deuda activa en las mensualidades o gastos seleccionados."}, status=400)

        total_bs = total_usd * tasa.valor_usd_bs

        return Response({
            "total_usd": float(total_usd),
            "tasa_usd_bs": float(tasa.valor_usd_bs),
            "total_bs_estimado": float(round(total_bs, 2)),
            "detalle": detalle
        })

#Vista para anular un pago (arrendador o superusuario)
class AnularPagoView(APIView):
    permission_classes = [IsAuthenticated, EsArrendadorYAdministraElPago]

    @swagger_auto_schema(request_body=AnularPagoSerializer)
    @transaction.atomic
    def post(self, request, pago_id):
        pago = get_object_or_404(Pago, id=pago_id)

        # Chequea permiso
        self.check_object_permissions(request, pago)

        # Validar que el pago esté validado para poder anularlo
        if pago.estado_validacion != 'validado':
            if pago.estado_validacion == 'rechazado':
                return Response({"error": "No se pueden anular pagos rechazados."}, status=400)
            elif pago.estado_validacion == 'anulado':
                return Response({"error": "Este pago ya fue anulado."}, status=400)
            return Response({"error": "Solo se pueden anular pagos en estado validado."}, status=400)

        # Validar datos con serializer
        serializer = AnularPagoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comentario = serializer.validated_data['comentario']

        hoy = timezone.now().date()

        # Anulación lógica:
        # 1. Volver a aumentar saldo pendiente en mensualidades y gastos según monto_pagado en este pago
        for pago_mensualidad in pago.mensualidades_pagadas.all():
            mensualidad = pago_mensualidad.mensualidad
            monto = pago_mensualidad.monto_pagado

            mensualidad.saldo_pendiente += monto
            if mensualidad.saldo_pendiente > 0:
                if mensualidad.fecha_vencimiento < hoy:
                    mensualidad.estado = 'atrasado'
                else:
                    mensualidad.estado = 'pendiente'
            mensualidad.save()

        for pago_gasto in pago.gastos_pagados.all():
            gasto = pago_gasto.gasto_extra
            monto = pago_gasto.monto_pagado

            gasto.saldo_pendiente += monto
            if gasto.saldo_pendiente > 0:
                if gasto.fecha_vencimiento < hoy:
                    gasto.estado = 'atrasado'
                else:
                    gasto.estado = 'pendiente'
            gasto.save()

        # Cambiar estado del pago a 'anulado'
        pago.estado_validacion = 'anulado'
        pago.comentario_anulacion = comentario
        pago.save()

        # Anular recibos asociados a este pago
        recibos_asociados = Recibo.objects.filter(pago=pago, estado='pagado')
        for recibo in recibos_asociados:
            recibo.estado = 'anulado'
            recibo.save()

        # Log
        LogAccion.objects.create(
            usuario=request.user,
            accion='anuló un pago',
            tabla_afectada='pagos',
            registro_id=pago.id,
            descripcion=f'Pago #{pago.id} anulado por {request.user.username} el {hoy}. Motivo: {comentario}'
        )

        return Response({"mensaje": "Pago anulado correctamente"}, status=status.HTTP_200_OK)

#Vista para eliminar un pago (solo si está rechazado y solo arrendador o superusuario) 
class EliminarPagoView(APIView):
    permission_classes = [IsAuthenticated, EsArrendadorYAdministraElPago]

    @transaction.atomic
    def delete(self, request, pago_id):
        pago = get_object_or_404(Pago, id=pago_id)

        # Verificar permiso
        self.check_object_permissions(request, pago)

        # Solo se puede eliminar si el pago fue anulado o rechazado
        if pago.estado_validacion not in ['rechazado', 'anulado']:
            return Response(
                {"error": "Solo se pueden eliminar pagos en estado rechazado o anulado."},
            status=status.HTTP_400_BAD_REQUEST
            )

        # Guardar datos para el log antes de eliminar
        id_pago = pago.id
        username = request.user.username

        # Eliminar relaciones directas
        if hasattr(pago, 'pagoefectivo'):
            pago.pagoefectivo.delete()

        if hasattr(pago, 'pagotransferencias'):
            pago.pagotransferencias.all().delete()

        pago.mensualidades_pagadas.through.objects.filter(pago=pago).delete()
        pago.gastos_pagados.through.objects.filter(pago=pago).delete()

        # Eliminar recibos asociados (si existen)
        recibos = Recibo.objects.filter(pago=pago)
        for recibo in recibos:
            # Eliminar recibos hijos primero
            recibo.recibomensualidad_set.all().delete()
            recibo.recibogastoextra_set.all().delete()
            recibo.delete()

        # Eliminar el pago
        pago.delete()

        # Log
        LogAccion.objects.create(
            usuario=request.user,
            accion=f'eliminó un pago {pago.estado_validacion}',
            tabla_afectada='pagos',
            registro_id=id_pago,
            descripcion=f"Pago #{id_pago} (estado: {pago.estado_validacion}) y sus recibos asociados fueron eliminados por {username}"
        )

        return Response(
            {"mensaje": f"Pago #{id_pago} eliminado correctamente con sus recibos asociados."},
            status=status.HTTP_200_OK
        )

#========================================================================================================================    
#Vistas recibos
# Vista para listar recibos (filtrables por estado, usuario, fechas)    
class ListaRecibosAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReciboSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['estado', 'usuario', 'fecha_emision']
    ordering_fields = ['fecha_emision']

    def get_queryset(self):
        usuario = self.request.user

        if usuario.tipo_usuario == 'arrendatario':
            # Solo recibos propios, sin filtro por usuario para evitar filtrado inapropiado
            return Recibo.objects.filter(usuario=usuario).order_by('-created_at')

        elif usuario.is_superuser:
            # Superusuario ve todo
            return Recibo.objects.all()

        elif usuario.tipo_usuario == 'arrendador':
            edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)
            return Recibo.objects.filter(
                Q(mensualidades__mensualidad__contrato__apartamento__edificio_id__in=edificios_ids) |
                Q(gastos__gasto_extra__apartamento__edificio_id__in=edificios_ids)
            ).distinct()

        # Otros tipos no autorizados
        return Recibo.objects.none()

#Vista detalle de un recibo específico
class ReciboDetalleAPIView(RetrieveAPIView):
    queryset = Recibo.objects.all()
    serializer_class = ReciboSerializer
    permission_classes = [IsAuthenticated, 
                          # Custom permissions para que solo arrendatarios vean sus recibos y arrendadores los suyos
                          permissions.OR(EsArrendatarioYEsDueñoDelRecibo, EsArrendadorYAdministraElRecibo)]
    lookup_field = 'id'


from django.shortcuts import render,get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from rest_framework import generics,status,filters,permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.generics import GenericAPIView,RetrieveAPIView
from rest_framework.exceptions import PermissionDenied

from datetime import datetime
from decimal import Decimal,InvalidOperation

from .models import Pago,PagoEfectivo,PagoTransferencias,PagoMensualidad, PagoGastoExtra
from .serializers_pagos import PagoSerializer,PagoEfectivoSerializer,PagoTransferenciaSerializer,PagoRegistroSerializer,DetallePagoSerializer
from .filters import PagoFilter
from .permisos import EsArrendadorYAdministraElPago, EsArrendatarioYEsDueñoDelPago, EsArrendadorYAdministraElRecibo, EsArrendatarioYEsDueñoDelRecibo
from pagos.tareas import actualizar_estado_recibo_si_pagado

from .models_recibos import Recibo, ReciboMensualidad, ReciboGastoExtra
from .serializers_recibos import (
    ReciboSerializer,
    GenerarReciboSerializer,
)

from usuarios.models import Usuario
from usuarios.permissions import EsArrendatario,EsArrendador

from contratos.models import Contrato
from contratos.models_mensualidades import Mensualidad

from gastos.models import GastoExtra

from tasas.models import TasaDia

from edificios.models import Apartamento

from log.models import LogAccion

#======================================================================================================================== 
#Vistas pagos
class ListaPagosAPIView(generics.ListAPIView): #Muestra los pagos asociados al arrendador (sus apartamentos) o arrendatario
    
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

class RegistrarPagoView(GenericAPIView): #Permite que el arrendatario registre un pago de un recibo(mensualidad o gasto extra)
    
    permission_classes = [IsAuthenticated]
    serializer_class = PagoRegistroSerializer

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        data = serializer.validated_data
        usuario = request.user
        tipo_usuario = usuario.tipo_usuario

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

        monto_bs = monto * tasa.valor_usd_bs

        # Crear el pago principal
        pago = Pago.objects.create(
            usuario=usuario,
            monto_total=monto,
            monto_bs=monto_bs,
            tasa_usd=tasa.valor_usd_bs,
            tasa_dia=tasa, 
            fecha_pago=fecha_pago,
            tipo_pago=tipo_pago,
            estado_validacion="validado" if tipo_usuario == 'arrendador' else "pendiente",
            validado_por=usuario if tipo_usuario == 'arrendador' else None,
            fecha_validacion=timezone.now() if tipo_usuario == 'arrendador' else None
        )

        # 💬 Agregar log del registro de pago
        LogAccion.objects.create(
            usuario=usuario,
            accion="registró un nuevo pago",
            tabla_afectada="pagos",
            registro_id=pago.id,
            descripcion=f"Tipo: {tipo_pago}, Monto: {monto}, Fecha: {fecha_pago}"
        )

        # Procesar mensualidades
        for item in mensualidades_data:
            mensualidad = get_object_or_404(Mensualidad, id=item["id"], estado__in=["pendiente", "atrasado"])

            if tipo_usuario == "arrendatario" and mensualidad.contrato.arrendatario_id != usuario.id:
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

            # 💬 Agregar log del registro de pago de una mensualidad
            LogAccion.objects.create(
                usuario=usuario,
                accion="asoció una mensualidad al pago",
                tabla_afectada="pagos_mensualidades",
                registro_id=mensualidad.id,
                descripcion=f"Pago #{pago.id}, Mensualidad #{mensualidad.id}, Monto pagado: {monto_item}"
            )

            monto_acumulado += monto_item

        # Procesar gastos extra
        for item in gastos_extra_data:
            gasto = get_object_or_404(GastoExtra, id=item["id"], estado__in=["pendiente", "atrasado"])

            if tipo_usuario == "arrendatario":
                contrato = Contrato.objects.filter(apartamento=gasto.apartamento, arrendatario=usuario, activo=True).first()
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

            # 💬 Agregar log del registro de pago de un gasto extra
            LogAccion.objects.create(
                usuario=usuario,
                accion="asoció un gasto extra al pago",
                tabla_afectada="pagos_gastos_extra",
                registro_id=gasto.id,
                descripcion=f"Pago #{pago.id}, GastoExtra #{gasto.id}, Monto pagado: {monto_item}"
            )

            monto_acumulado += monto_item

        # Verificación final del total
        if monto_acumulado != monto:

            LogAccion.objects.create(
                usuario=usuario,
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
                usuario=usuario,
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
                usuario=usuario,
                accion="registró pago por transferencia",
                tabla_afectada="pagos_transferencias",
                registro_id=pago.id,
                descripcion=f"Pago #{pago.id} registrado por transferencia. Referencia: {transferencia_data.get('referencia')}, Monto Bs: {monto_bs_transferido}"
            )

        if tipo_usuario == 'arrendador':
            # Actualizar mensualidades
            for pago_m in pago.mensualidades_pagadas.all():
                mensualidad = pago_m.mensualidad
                mensualidad.saldo_pendiente -= pago_m.monto_pagado
                mensualidad.saldo_pendiente = max(Decimal('0.00'), mensualidad.saldo_pendiente)
                if mensualidad.saldo_pendiente == 0:
                    mensualidad.estado = 'pagado'
                mensualidad.save()

            # Actualizar gastos
            for pago_g in pago.gastos_pagados.all():
                gasto = pago_g.gasto_extra
                gasto.saldo_pendiente -= pago_g.monto_pagado
                gasto.saldo_pendiente = max(Decimal('0.00'), gasto.saldo_pendiente)
                if gasto.saldo_pendiente == 0:
                    gasto.estado = 'pagado'
                gasto.save()

            # Revisar recibos relacionados
            for pago_m in pago.mensualidades_pagadas.all():
                recibos_m = ReciboMensualidad.objects.filter(mensualidad=pago_m.mensualidad)
                for rm in recibos_m:
                    actualizar_estado_recibo_si_pagado(rm.recibo, pago=pago)

            for pago_g in pago.gastos_pagados.all():
                recibos_g = ReciboGastoExtra.objects.filter(gasto_extra=pago_g.gasto_extra)
                for rg in recibos_g:
                    actualizar_estado_recibo_si_pagado(rg.recibo, pago=pago)
    
        return Response({
            "mensaje": "Pago registrado correctamente",
            "pago_id": pago.id
        })
     
class ValidarPagoView(APIView): #Permite que el arrendador valide un pago registrado por un arrendatario
    
    permission_classes = [IsAuthenticated, EsArrendador, EsArrendadorYAdministraElPago]

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
        
        if accion == "validar":
            # Validar el pago
            pago.estado_validacion = 'validado'
            pago.validado_por = request.user
            pago.fecha_validacion = timezone.now()
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

            # Revisar recibos asociados a mensualidades
            for pago_m in pago.mensualidades_pagadas.all():
                recibos_m = ReciboMensualidad.objects.filter(mensualidad=pago_m.mensualidad)
                for rm in recibos_m:
                    actualizar_estado_recibo_si_pagado(rm.recibo, pago=pago)

            # Revisar recibos asociados a gastos
            for pago_g in pago.gastos_pagados.all():
                recibos_g = ReciboGastoExtra.objects.filter(gasto_extra=pago_g.gasto_extra)
                for rg in recibos_g:
                    actualizar_estado_recibo_si_pagado(rg.recibo, pago=pago)

            return Response({'mensaje': 'Pago validado correctamente'}, status=status.HTTP_200_OK)
        
        elif accion == "rechazar":
            # ❌ Rechazar pago
            pago.estado_validacion = 'rechazado'
            pago.validado_por = request.user
            pago.fecha_validacion = timezone.now()
            pago.observaciones = observacion  # (agrega este campo al modelo si no existe)
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
    
class HistorialPagosView(APIView): #Permite que el arrendatario vea su historial de pagos (solo los ya validados)
    
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
    
class DetallePagoView(RetrieveAPIView): #Permite que el arrendador vea los detalles de un pago específico
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
        recibo_ids = request.data.get('recibos_id', [])

        if not isinstance(recibo_ids, list) or not recibo_ids:
            return Response({"error": "Debes enviar una lista de IDs de recibos."}, status=400)

        recibos = Recibo.objects.filter(id__in=recibo_ids)

        # Seguridad: validar acceso a esos recibos
        if usuario.tipo_usuario == 'arrendatario':
            recibos = recibos.filter(usuario=usuario)
        elif usuario.tipo_usuario == 'arrendador':
            edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)
            recibos = recibos.filter(
                Q(mensualidades__mensualidad__contrato__apartamento__edificio_id__in=edificios_ids) |
                Q(gastos__gasto_extra__apartamento__edificio_id__in=edificios_ids)
            ).distinct()
        else:
            return Response({"error": "No tienes permiso para esta acción."}, status=403)

        total_usd = Decimal('0.00')
        detalle = {"mensualidades": [], "gastos_extra": []}

        for r in recibos:
            for rm in r.mensualidades.all():
                mensualidad = rm.mensualidad
                if mensualidad.estado in ['pendiente', 'atrasado'] and mensualidad.saldo_pendiente > 0:
                    monto = mensualidad.saldo_pendiente
                    total_usd += monto
                    detalle["mensualidades"].append({
                        "id": mensualidad.id,
                        "recibo_id": r.id,
                        "monto_usd": float(monto),
                        "fecha_vencimiento": mensualidad.fecha_vencimiento,
                        "estado": mensualidad.estado
                    })

            for rg in r.gastos.all():
                gasto = rg.gasto_extra
                if gasto.estado in ['pendiente', 'atrasado'] and gasto.saldo_pendiente > 0:
                    monto = gasto.saldo_pendiente
                    total_usd += monto
                    detalle["gastos_extra"].append({
                        "id": gasto.id,
                        "recibo_id": r.id,
                        "monto_usd": float(monto),
                        "descripcion": gasto.descripcion,
                        "estado": gasto.estado
                    })

        if total_usd == 0:
            return Response({"error": "No hay deuda activa en los recibos seleccionados."}, status=400)

        tasa = TasaDia.objects.order_by('-fecha').first()
        if not tasa:
            return Response({"error": "No hay tasa registrada."}, status=400)

        total_bs = total_usd * tasa.valor_usd_bs

        return Response({
            "total_usd": float(total_usd),
            "tasa_usd_bs": float(tasa.valor_usd_bs),
            "total_bs_estimado": float(round(total_bs, 2)),
            "detalle": detalle
        })

#========================================================================================================================    
#Vistas recibos
class RecibosDelUsuarioView(APIView): #Permite que el arrendatario vea sus recibos (pendientes, atrasados o pagados)
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        estado = request.query_params.get('estado')

        if usuario.tipo_usuario == 'arrendatario':
            filtros = {'usuario': usuario}
            if estado in ['pendiente', 'atrasado', 'pagado']:
                filtros['estado'] = estado
            recibos = Recibo.objects.filter(**filtros).order_by('-fecha_emision')

        elif usuario.tipo_usuario == 'arrendador':
            # Arrendador ve recibos asociados a edificios que administra
            edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)

            # Recibos asociados a mensualidades o gastos extra de apartamentos en esos edificios
            recibos = Recibo.objects.filter(
                Q(mensualidades__mensualidad__contrato__apartamento__edificio_id__in=edificios_ids) |
                Q(gastos__gasto_extra__apartamento__edificio_id__in=edificios_ids)
            ).distinct()

            if estado in ['pendiente', 'atrasado', 'pagado']:
                recibos = recibos.filter(estado=estado)
            recibos = recibos.order_by('-fecha_emision')

        else:
            return Response({"error": "No tienes permiso para esta acción."}, status=403)

        data = ReciboSerializer(recibos, many=True).data
        return Response(data)

class PermisoArrendadorOSuperuser(IsAuthenticated):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.tipo_usuario == 'arrendador')
        )
    
class ListaRecibosAPIView(generics.ListAPIView):
    permission_classes = [PermisoArrendadorOSuperuser]
    serializer_class = ReciboSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['estado', 'usuario', 'fecha_emision', 'fecha_vencimiento']
    ordering_fields = ['fecha_emision', 'fecha_vencimiento']

    def get_queryset(self):
        usuario = self.request.user

        if usuario.is_superuser:
            return Recibo.objects.all()

        if usuario.tipo_usuario == 'arrendador':
            edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)
            return Recibo.objects.filter(
                Q(mensualidades__mensualidad__contrato__apartamento__edificio_id__in=edificios_ids) |
                Q(gastos__gasto_extra__apartamento__edificio_id__in=edificios_ids)
            ).distinct()

        return Recibo.objects.none()

class GenerarReciboAPIView(APIView): # Superuser genera recibos manuales o se generan automáticamente por mensualidades y gastos extra
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = GenerarReciboSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            usuario = Usuario.objects.get(id=data['usuario_id'])

            # IDs ya asociados a recibos (no pagados aún)
            mensualidades_con_recibo = ReciboMensualidad.objects.filter(
            recibo__estado__in=['pendiente', 'atrasado']
            ).values_list('mensualidad_id', flat=True)

            gastos_con_recibo = ReciboGastoExtra.objects.filter(
            recibo__estado__in=['pendiente', 'atrasado']
            ).values_list('gasto_extra_id', flat=True)

            # Solo tomar los que no estén en un recibo activo
            mensualidades = Mensualidad.objects.filter(
            id__in=data.get('mensualidades_id', []),
            estado__in=['pendiente', 'atrasado'],
            saldo_pendiente__gt=0
            ).exclude(id__in=mensualidades_con_recibo)

            gastos = GastoExtra.objects.filter(
            id__in=data.get('gastos_extra_id', []),
            estado__in=['pendiente', 'atrasado'],
            saldo_pendiente__gt=0
            ).exclude(id__in=gastos_con_recibo)

            if not mensualidades and not gastos:
                return Response({"error": "No hay deudas válidas para generar el recibo."}, status=status.HTTP_400_BAD_REQUEST)

            # Superusuario puede agrupar todo en un único recibo
            if request.user.is_superuser:
                total_usd = sum([m.monto_usd for m in mensualidades]) + sum([g.monto_usd for g in gastos])
                tasa = TasaDia.objects.order_by('-fecha').first()
                if not tasa:
                    return Response({"error": "No hay tasa registrada."}, status=status.HTTP_400_BAD_REQUEST)

                total_bs = total_usd * tasa.valor_usd_bs

                recibo = Recibo.objects.create(
                    usuario=usuario,
                    total_usd=total_usd,
                    total_bs=total_bs,
                    observaciones=data.get('observaciones', ''),
                    creado_por=request.user
                )

                for m in mensualidades:
                    ReciboMensualidad.objects.create(recibo=recibo, mensualidad=m, monto_usd=m.monto_usd)

                for g in gastos:
                    ReciboGastoExtra.objects.create(recibo=recibo, gasto_extra=g, monto_usd=g.monto_usd)

                return Response(ReciboSerializer(recibo).data, status=status.HTTP_201_CREATED)

            # Usuarios normales: un recibo por cada ítem
            recibos_creados = []

            tasa = TasaDia.objects.order_by('-fecha').first()
            if not tasa:
                return Response({"error": "No hay tasa registrada."}, status=status.HTTP_400_BAD_REQUEST)

            for m in mensualidades:
                total_usd = m.monto_usd
                total_bs = total_usd * tasa.valor_usd_bs
                recibo = Recibo.objects.create(
                    usuario=usuario,
                    total_usd=total_usd,
                    total_bs=total_bs,
                    observaciones=data.get('observaciones', ''),
                    creado_por=request.user
                )
                ReciboMensualidad.objects.create(recibo=recibo, mensualidad=m, monto_usd=total_usd)
                recibos_creados.append(recibo)

            for g in gastos:
                total_usd = g.monto_usd
                total_bs = total_usd * tasa.valor_usd_bs
                recibo = Recibo.objects.create(
                    usuario=usuario,
                    total_usd=total_usd,
                    total_bs=total_bs,
                    observaciones=data.get('observaciones', ''),
                    creado_por=request.user
                )
                ReciboGastoExtra.objects.create(recibo=recibo, gasto_extra=g, monto_usd=total_usd)
                recibos_creados.append(recibo)

            return Response(ReciboSerializer(recibos_creados, many=True).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
#Lista de recibos seleccionables (pendientes o atrasados) para pagar
class RecibosSeleccionablesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        if usuario.tipo_usuario == 'arrendatario':
            recibos = Recibo.objects.filter(
                usuario=usuario,
                estado__in=['pendiente', 'atrasado']
            )

        elif usuario.tipo_usuario == 'arrendador':
            edificios_ids = usuario.edificios_asignados.values_list('edificio_id', flat=True)
            recibos = Recibo.objects.filter(
                Q(mensualidades__mensualidad__contrato__apartamento__edificio_id__in=edificios_ids) |
                Q(gastos__gasto_extra__apartamento__edificio_id__in=edificios_ids),
                estado__in=['pendiente', 'atrasado']
            ).distinct()

        else:
            return Response({"error": "No tienes permiso para esta acción."}, status=403)

        # Filtrar solo los que tienen saldo pendiente > 0
        seleccionables = []
        tasa = TasaDia.objects.order_by('-fecha').first()
        for r in recibos:
            saldo_usd = Decimal('0.00')
            for rm in r.mensualidades.all():
                saldo_usd += rm.mensualidad.saldo_pendiente
            for rg in r.gastos.all():
                saldo_usd += rg.gasto_extra.saldo_pendiente

            if saldo_usd > 0:
                estimado_bs = round(saldo_usd * tasa.valor_usd_bs, 2) if tasa else None
                seleccionables.append({
                    "id": r.id,
                    "estado": r.estado,
                    "fecha_emision": r.fecha_emision,
                    "fecha_vencimiento": r.fecha_vencimiento,
                    "total_usd": float(r.total_usd),
                    "saldo_usd": float(saldo_usd),
                    "monto_estimado_bs": float(estimado_bs) if estimado_bs is not None else None,
                })

        return Response(seleccionables)

#Vista detalle de un recibo específico
class ReciboDetalleAPIView(RetrieveAPIView):
    queryset = Recibo.objects.all()
    serializer_class = ReciboSerializer
    permission_classes = [IsAuthenticated, 
                          # Custom permissions para que solo arrendatarios vean sus recibos y arrendadores los suyos
                          permissions.OR(EsArrendatarioYEsDueñoDelRecibo, EsArrendadorYAdministraElRecibo)]
    lookup_field = 'id'


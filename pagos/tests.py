from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from datetime import date

from .models import Pago, PagoMensualidad, PagoGastoExtra
from .models_recibos import Recibo
from .tareas import generar_recibo_para_pago
from usuarios.models import Usuario,UsuarioEdificio
from contratos.models import Mensualidad, Contrato
from gastos.models import GastoExtra
from edificios.models import Apartamento, Edificio

User = get_user_model()

class AnularPagoTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Crear usuario arrendador y arrendatario
        self.arrendatario = Usuario.objects.create_user(
            username='arrendatario1', password='test123', tipo_usuario='arrendatario',correo='arrendatario1@example.com'
        )
        self.arrendador = Usuario.objects.create_user(
            username='arrendador1', password='test123', tipo_usuario='arrendador', is_staff=True,correo='arrendador1@example.com'
        )

        # 🔐 Obtener token JWT para arrendador
        refresh = RefreshToken.for_user(self.arrendador)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        # Crear edificio primero
        self.edificio = Edificio.objects.create(
            nombre="Edificio Central",
            direccion="Calle Falsa 123"
        )

        # Asociar arrendador al edificio
        UsuarioEdificio.objects.create(
            usuario=self.arrendador,
            edificio=self.edificio,
            rol='administrador'  # o 'colaborador' si aplica
        )

        # Crear apartamento vinculado al edificio
        self.apartamento = Apartamento.objects.create(
            edificio=self.edificio,
            numero_apartamento="101",
            habitaciones=2,
            banos=1,
            descripcion="Apartamento 101"
        )

        # Crear contrato que vincule usuario + apartamento
        self.contrato = Contrato.objects.create(
            arrendatario=self.arrendatario,
            apartamento=self.apartamento,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date().replace(year=timezone.now().year + 1),
            fecha_pago_mensual=timezone.now().date().day,
            monto_usd_mensual=100.00,
            activo=True
        )

        # Crear mensualidad con el contrato
        self.mensualidad = Mensualidad.objects.create(
            contrato=self.contrato,
            fecha_generacion=timezone.now().date(),
            fecha_vencimiento=timezone.now().date(),
            monto_usd=100.00,
            estado='pendiente'
        )
        
        # Crear gasto
        self.gasto = GastoExtra.objects.create(
            apartamento=self.apartamento,
            descripcion="Reparación",
            monto_usd=50,
            estado='pendiente',
            fecha_vencimiento=timezone.now().date()
        )

        # Crear el pago validado
        self.pago = Pago.objects.create(
            usuario=self.arrendatario,
            monto_total=150,
            monto_bs=5250,
            tasa_usd=35,
            fecha_pago=timezone.now().date(),
            validado_por=self.arrendador,
            estado_validacion='validado'
        )

         # Asociar mensualidad y gasto
        PagoMensualidad.objects.create(pago=self.pago, mensualidad=self.mensualidad, monto_pagado=100)
        PagoGastoExtra.objects.create(pago=self.pago, gasto_extra=self.gasto, monto_pagado=50)

        # Generar recibo
        generar_recibo_para_pago(self.pago, self.arrendador)

    def test_anular_pago_anula_recibo(self):
        # Asegurar que el recibo fue creado
        recibo = Recibo.objects.get(pago=self.pago)
        self.assertEqual(recibo.estado, 'pagado')

        # Anular el pago
        response = self.client.post(
            f'/api/pagos/anular/{self.pago.id}/',
            {'comentario': 'Error en el monto'},
            format='json'
        )

        # Recargar el recibo
        recibo.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(recibo.estado, 'anulado')
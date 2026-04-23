from django.shortcuts import render
from django.utils import timezone

from rest_framework import generics,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .models import Notificacion
from .serializers import NotificacionListSerializer
from .filters import NotificacionFilter

from django_filters.rest_framework import DjangoFilterBackend

class ListaNotificacionesAPIView(generics.ListAPIView):
    """
    Lista las notificaciones del usuario autenticado.
    """

    serializer_class = NotificacionListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificacionFilter
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        user = self.request.user
        return Notificacion.objects.filter(
            receptor=self.request.user
        ).order_by('-created_at')
    
class DetalleNotificacionAPIView(generics.RetrieveAPIView):
    """
    Ver el detalle de una notificación propia.
    """
    serializer_class = NotificacionListSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        return Notificacion.objects.filter(
            receptor=self.request.user
        )
    
class MarcarNotificacionLeidaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notificacion = Notificacion.objects.get(
                pk=pk,
                receptor=request.user
            )
        except Notificacion.DoesNotExist:
            return Response(
                {"error": "Notificación no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not notificacion.leido:
            notificacion.leido = True
            notificacion.estado = 'leida'
            notificacion.save(update_fields=['leido', 'estado'])

        return Response({
            "mensaje": "Notificación marcada como leída."
        })    

class ArchivarNotificacionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notificacion = Notificacion.objects.get(
                pk=pk,
                receptor=request.user
            )
        except Notificacion.DoesNotExist:
            return Response(
                {"error": "Notificación no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        notificacion.estado = 'archivada'
        notificacion.save(update_fields=['estado'])

        return Response({
            "mensaje": "Notificación archivada."
        })

# Create your views here.

from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import TasaDia
from .serializers import TasaDiaSerializer,TasaDiaDetalleSerializer,TasaDiaCrearSerializer
from .filters import TasasDiaFilter

from usuarios.permissions import EsArrendador

#Lista de tasas del día
class ListaTasasDiaAPIView(generics.ListAPIView):
    queryset = TasaDia.objects.all()
    serializer_class = TasaDiaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TasasDiaFilter
    renderer_classes = [JSONRenderer]

#Vista para detalle de tasa del día
class DetalleTasaDiaAPIView(generics.RetrieveAPIView):
    queryset = TasaDia.objects.all()
    serializer_class = TasaDiaDetalleSerializer
    permission_classes = [IsAuthenticated, EsArrendador | IsAdminUser]

# Vista para crear una nueva tasa del día
class CrearTasaDiaAPIView(generics.CreateAPIView):
    queryset = TasaDia.objects.all()
    serializer_class = TasaDiaCrearSerializer
    permission_classes = [IsAuthenticated, EsArrendador | IsAdminUser]
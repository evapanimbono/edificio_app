from django.shortcuts import render
from rest_framework.renderers import JSONRenderer
from rest_framework import generics,filters
from rest_framework.permissions import IsAdminUser

from .models import LogAccion
from .serializers import LogAccionesSerializer
from .filters import LogAccionesFilter

from django_filters.rest_framework import DjangoFilterBackend

class ListaLogAccionesAPIView(generics.ListAPIView):
    queryset = LogAccion.objects.all()
    serializer_class = LogAccionesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = LogAccionesFilter
    renderer_classes = [JSONRenderer]

class ListaLogsAPIView(generics.ListAPIView):
    queryset = LogAccion.objects.all()
    serializer_class = LogAccionesSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['usuario__username', 'accion', 'tabla_afectada', 'fecha']
    ordering_fields = ['fecha']    
# Create your views here.

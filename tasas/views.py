from django.shortcuts import render

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .models import TasaDia
from .serializers import TasaDiaSerializer
from .filters import TasasDiaFilter
from django_filters.rest_framework import DjangoFilterBackend

class ListaTasasDiaAPIView(generics.ListAPIView):
    queryset = TasaDia.objects.all()
    serializer_class = TasaDiaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TasasDiaFilter
    renderer_classes = [JSONRenderer]
# Create your views here.

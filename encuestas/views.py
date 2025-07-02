from django.shortcuts import render

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .models import Encuesta
from .serializers_encuestas import EncuestaSerializer
from .filters import EncuestasFilter

from .models_respuestas import RespuestaEncuestas
from .serializers_respuestas import RespuestaEncuestaSerializer
from .filters import RespuestasEncuestasFilter

from django_filters.rest_framework import DjangoFilterBackend

class ListaEncuestasAPIView(generics.ListAPIView):
    queryset = Encuesta.objects.all()
    serializer_class = EncuestaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = EncuestasFilter
    renderer_classes = [JSONRenderer]
    

class ListaRespuestasEncuestasAPIView(generics.ListAPIView):
    queryset = RespuestaEncuestas.objects.all()
    serializer_class = RespuestaEncuestaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RespuestasEncuestasFilter
    renderer_classes = [JSONRenderer]
# Create your views here.

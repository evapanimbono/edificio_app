from django.shortcuts import render

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .models import Notificacion
from .serializers import NotificacionSerializer
from .filters import NotificacionFilter

from django_filters.rest_framework import DjangoFilterBackend

class ListaNotificacionesAPIView(generics.ListAPIView):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = NotificacionFilter
    renderer_classes = [JSONRenderer]
# Create your views here.

from django.urls import path
from .views import ListaEncuestasAPIView, ListaRespuestasEncuestasAPIView


urlpatterns = [
    path('', ListaEncuestasAPIView.as_view(), name='encuestas-lista'),
    path('respuestas/', ListaRespuestasEncuestasAPIView.as_view(), name='respuestas-lista'),
]
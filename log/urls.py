from django.urls import path
from .views import (
    ListaLogAccionesAPIView,
    ListaLogsAPIView
)

urlpatterns = [
    path('', ListaLogAccionesAPIView.as_view()),

    path('lista/', ListaLogsAPIView.as_view(), name='logs-lista'),
]
from django.urls import path
from .views import ListaTasasDiaAPIView

urlpatterns = [
    path('', ListaTasasDiaAPIView.as_view(), name='tasas-dia-lista'),
]
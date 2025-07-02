from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models_apartamentos import Apartamento
from .serializers_apartamentos import ApartamentoSerializer

class ListaApartamentosAPIView(APIView):
    def get(self, request):
        apartamentos = Apartamento.objects.all()
        serializer = ApartamentoSerializer(apartamentos, many=True)
        return Response(serializer.data)
# Create your views here.

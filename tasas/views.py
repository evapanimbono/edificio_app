from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from rest_framework import generics, serializers,status
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

    def validate_fecha(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("No se puede registrar una tasa con fecha futura.")
        if TasaDia.objects.filter(fecha=value).exists():
            raise serializers.ValidationError("Ya existe una tasa registrada para esta fecha.")
        return value

# Vista para anular una tasa del día (solo si no tiene pagos o los pagos asociados están anulados o rechazados)  
class AnularTasaDiaAPIView(APIView):
    permission_classes = [IsAuthenticated, EsArrendador | IsAdminUser]

    def post(self, request, pk):
        try:
            tasa = TasaDia.objects.get(pk=pk)
        except TasaDia.DoesNotExist:
            return Response({"detail": "Tasa no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        try:
            tasa.anular()
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Tasa anulada correctamente."}, status=status.HTTP_200_OK)
    
# Vista para eliminar una tasa del día (solo si está en estado 'anulada')
class EliminarTasaDiaAPIView(generics.DestroyAPIView):
    queryset = TasaDia.objects.all()
    permission_classes = [IsAuthenticated, EsArrendador | IsAdminUser]

    def delete(self, request, *args, **kwargs):
        tasa = self.get_object()
        if tasa.estado != 'anulada':
            return Response(
                {"detail": "Solo se pueden eliminar tasas en estado 'anulada'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().delete(request, *args, **kwargs)

# Vista para obtener la tasa activa del día
class TasaDiaActivaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasa = TasaDia.objects.filter(estado='activa').order_by('-fecha').first()
        if not tasa:
            return Response({"detail": "No hay una tasa activa registrada."}, status=status.HTTP_404_NOT_FOUND)
        data = TasaDiaSerializer(tasa).data
        return Response(data, status=status.HTTP_200_OK)
    

from rest_framework import serializers
from .models_apartamentos import Apartamento

class ApartamentoListSerializer(serializers.ModelSerializer):
    edificio_nombre = serializers.CharField(source='edificio.nombre', read_only=True)

    class Meta:
        model = Apartamento
        fields = ['id', 'edificio', 'edificio_nombre', 'numero_apartamento', 'piso', 'estado']

class ApartamentoDetailSerializer(serializers.ModelSerializer):
    edificio_nombre = serializers.CharField(source='edificio.nombre', read_only=True)

    class Meta:
        model = Apartamento
        fields = '__all__'

class ApartamentoCrearEditarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartamento
        fields = ['edificio', 'numero_apartamento', 'piso', 'habitaciones', 'banos', 'descripcion', 'estado']
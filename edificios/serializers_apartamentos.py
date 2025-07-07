
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

    def validate(self, data):
        edificio = data.get('edificio')
        numero = data.get('numero_apartamento')

        if edificio and numero:
            if Apartamento.objects.filter(edificio=edificio, numero_apartamento=numero).exists():
                raise serializers.ValidationError("Ya existe un apartamento con ese número en este edificio.")

        if data.get('habitaciones', 0) < 0:
            raise serializers.ValidationError("El número de habitaciones no puede ser negativo.")

        if data.get('banos', 0) < 0:
            raise serializers.ValidationError("El número de baños no puede ser negativo.")

        return data
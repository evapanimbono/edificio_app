from rest_framework import serializers
from .models import TasaDia

class TasaDiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TasaDia
        fields = '__all__'

class TasaDiaDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TasaDia
        fields = ['fecha', 'valor_usd_bs', 'fuente', 'registrada_por']

class TasaDiaCrearSerializer(serializers.ModelSerializer):
    class Meta:
        model = TasaDia
        fields = ['fecha', 'valor_usd_bs', 'fuente']

    def validate_fecha(self, value):
        if TasaDia.objects.filter(fecha=value).exists():
            raise serializers.ValidationError("Ya existe una tasa registrada para esta fecha.")
        return value

    def create(self, validated_data):
        usuario = self.context['request'].user
        return TasaDia.objects.create(
            registrada_por=usuario,
            **validated_data
        )
    

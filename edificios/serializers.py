from rest_framework import serializers
from .models import Edificio

#Para vistas de lista (muestra info breve) (SuperUser/Arrendador)
class EdificioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edificio
        fields = ['id', 'nombre', 'direccion', 'latitud', 'longitud']

#Para mostrar todo en el detalle del edificio (Todos)
class EdificioDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edificio
        fields = '__all__'

#Para que el superuser pueda crear/modificar edificios (SuperUser)
class EdificioCrearEditarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edificio
        exclude = ['created_at', 'updated_at']

    def validate_nombre(self, value):
        if Edificio.objects.filter(nombre__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un edificio con este nombre.")
        return value
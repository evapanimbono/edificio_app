from rest_framework import serializers
from .models_mensualidades import Mensualidad

class MensualidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensualidad
        fields = '__all__'
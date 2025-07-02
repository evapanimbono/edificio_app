from rest_framework import serializers
from .models import TasaDia

class TasaDiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TasaDia
        fields = '__all__'
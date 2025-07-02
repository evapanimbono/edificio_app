from rest_framework import serializers
from .models import Encuesta

class EncuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encuesta
        fields = '__all__'
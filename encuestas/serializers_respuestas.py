from rest_framework import serializers
from .models_respuestas import RespuestaEncuestas

class RespuestaEncuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RespuestaEncuestas
        fields = '__all__'
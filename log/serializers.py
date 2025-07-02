from rest_framework import serializers
from .models import LogAccion

class LogAccionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAccion
        fields = '__all__'
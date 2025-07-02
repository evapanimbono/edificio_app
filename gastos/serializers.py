from rest_framework import serializers
from .models import GastoExtra

class GastoExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = GastoExtra
        fields = '__all__'
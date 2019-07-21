from rest_framework import serializers
from .models import PredictionModel


class PredictionModelGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionModel
        fields = ['pk', 'model_type', 'model_name', 'used_for_prediction_count', 'recent_running_time', 'creation_time']


class PredictionModelPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionModel
        fields = ['model_type', 'model_name', 'consent_for_file', 'is_public']

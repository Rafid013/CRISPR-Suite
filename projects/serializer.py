from rest_framework import serializers
from .models import Project, PredictionModel


class ProjectGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['pk', 'project_name']


class ProjectPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['project_name']


class PredictionModelGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionModel
        fields = ['pk', 'model_type', 'model_name']


class PredictionModelPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionModel
        fields = ['model_type', 'model_name', 'consent_for_file', 'is_public']

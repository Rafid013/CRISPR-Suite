from django import forms
from .models import Project, PredictionModel


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ['project_name']


class PredictionModelForm(forms.ModelForm):

    class Meta:
        model = PredictionModel
        fields = ['model_type', 'model_name', 'training_file', 'consent_for_file']



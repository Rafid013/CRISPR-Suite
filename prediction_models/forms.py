from django import forms
from .models import PredictionModel


class PredictionModelForm(forms.ModelForm):

    class Meta:
        model = PredictionModel
        fields = ['model_type', 'model_name', 'training_file', 'consent_for_file', 'is_public']

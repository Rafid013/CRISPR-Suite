from django.contrib import admin
from .models import Project, PredictionModel

admin.site.register(Project)
admin.site.register(PredictionModel)
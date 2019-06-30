from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


# Create your models here.
class Project(models.Model):
    project_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('projects:show', kwargs={'pk': self.pk})

    def __str__(self):
        return self.project_name


class PredictionModel(models.Model):
    model_type = models.PositiveSmallIntegerField(choices=((1, "CRISPRpred"),
                                                           (2, "CRISPRpred++"),
                                                           (3, "CRISPRpred(SEQ)")))
    model_name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.model_name + ' ' + str(self.model_type)

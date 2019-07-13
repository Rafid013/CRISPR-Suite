from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
# from django.core.validators import FileExtensionValidator


# Create your models here.
class Project(models.Model):
    project_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('projects:show_project', kwargs={'project_id': self.pk})

    def __str__(self):
        return self.project_name


def get_upload_path(instance, filename):
    return 'project_{0}/{1}'.format(instance.project.pk, filename)


class PredictionModel(models.Model):
    model_type = models.PositiveSmallIntegerField(choices=((1, "CRISPRpred"),
                                                           (2, "CRISPRpred++"),
                                                           (3, "CRISPRpred(SEQ)")))
    model_name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    training_file = models.FileField(upload_to=get_upload_path)
    consent_for_file = models.BooleanField(verbose_name="Can we use the file for research purposes?")

    def __str__(self):
        return self.model_name + ' ' + str(self.get_model_type_display())

    def get_absolute_url(self):
        return reverse('projects:show_model', kwargs={'project_id': self.project.pk, 'model_id': self.pk})

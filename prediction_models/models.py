from django.db import models
from django.contrib.auth.models import User
# from django.core.validators import FileExtensionValidator


def get_upload_path(instance, filename):
    return 'model_{0}/{1}'.format(instance.pk, filename)


class PredictionModel(models.Model):
    model_type = models.PositiveSmallIntegerField(choices=((1, "CRISPRpred"),
                                                           (2, "CRISPRpred++"),
                                                           (3, "CRISPRpred(SEQ)")))
    model_name = models.CharField(max_length=100)
    training_file = models.FileField(upload_to=get_upload_path)
    consent_for_file = models.BooleanField(verbose_name="Can we use the data for research purposes?")
    is_public = models.BooleanField(verbose_name="Make the model public?", default=False)
    used_for_prediction_count = models.IntegerField(default=0, editable=True)
    recent_running_time = models.DateTimeField(auto_now_add=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.model_name + ' ' + str(self.get_model_type_display())

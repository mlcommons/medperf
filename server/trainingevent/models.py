from django.db import models
from training.models import TrainingExperiment
from django.contrib.auth import get_user_model

User = get_user_model()


# Create your models here.
class TrainingEvent(models.Model):
    name = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    is_valid = models.BooleanField(default=True)
    finished = models.BooleanField(default=False)
    training_exp = models.ForeignKey(
        TrainingExperiment, on_delete=models.PROTECT, related_name="events"
    )
    participants = models.JSONField()
    report = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

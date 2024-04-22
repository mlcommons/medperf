from django.db import models
from training.models import TrainingExperiment


# Create your models here.
class TrainingEvent(models.Model):
    finished = models.BooleanField(default=False)
    training_exp = models.ForeignKey(
        TrainingExperiment, on_delete=models.PROTECT, related_name="events"
    )
    participants = models.JSONField()
    report = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

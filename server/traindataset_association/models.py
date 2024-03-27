from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ExperimentDataset(models.Model):
    MODEL_STATUS = (
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
    )
    certificate = models.TextField(blank=True)
    signing_request = models.TextField()
    dataset = models.ForeignKey("dataset.Dataset", on_delete=models.PROTECT)
    training_exp = models.ForeignKey(
        "training.TrainingExperiment", on_delete=models.CASCADE
    )
    initiated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    metadata = models.JSONField(default=dict)
    approval_status = models.CharField(
        choices=MODEL_STATUS, max_length=100, default="PENDING"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

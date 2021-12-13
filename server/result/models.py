from django.db import models
from django.contrib.auth.models import User


class ModelResult(models.Model):
    MODEL_RESULT_STATUS = (
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
    )

    name = models.CharField(max_length=20, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    benchmark = models.ForeignKey(
        "benchmark.Benchmark", on_delete=models.CASCADE
    )
    model = models.ForeignKey("mlcube.MlCube", on_delete=models.PROTECT)
    dataset = models.ForeignKey("dataset.Dataset", on_delete=models.PROTECT)
    results = models.JSONField()
    metadata = models.JSONField(default=dict)
    approval_status = models.CharField(
        choices=MODEL_RESULT_STATUS, max_length=100, default="PENDING"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (("benchmark", "model", "dataset"),)
        ordering = ["modified_at"]

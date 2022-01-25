from django.db import models
from django.contrib.auth.models import User


class BenchmarkDataset(models.Model):
    DATASET_STATUS = (
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
    )
    dataset = models.ForeignKey("dataset.Dataset", on_delete=models.PROTECT)
    benchmark = models.ForeignKey(
        "benchmark.Benchmark", on_delete=models.CASCADE
    )
    initiated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    approval_status = models.CharField(
        choices=DATASET_STATUS, max_length=100, default="PENDING"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["modified_at"]

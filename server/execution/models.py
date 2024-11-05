from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Execution(models.Model):
    MODEL_RESULT_STATUS = (
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
    )

    name = models.CharField(max_length=20, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    benchmark = models.ForeignKey("benchmark.Benchmark", on_delete=models.CASCADE)
    model = models.ForeignKey("mlcube.MlCube", on_delete=models.PROTECT)
    dataset = models.ForeignKey("dataset.Dataset", on_delete=models.PROTECT)
    results = models.JSONField()
    metadata = models.JSONField(default=dict)
    user_metadata = models.JSONField(default=dict)
    approval_status = models.CharField(
        choices=MODEL_RESULT_STATUS, max_length=100, default="PENDING"
    )
    is_valid = models.BooleanField(default=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["modified_at"]

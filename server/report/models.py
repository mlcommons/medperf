from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Report(models.Model):
    dataset_name = models.CharField(max_length=20)
    description = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    input_data_hash = models.CharField(max_length=128)
    data_preparation_mlcube = models.ForeignKey(
        "mlcube.MlCube", on_delete=models.PROTECT
    )
    benchmark = models.ForeignKey(
        "benchmark.Benchmark", on_delete=models.CASCADE, blank=True, null=True
    )
    is_valid = models.BooleanField(default=True)

    contents = models.JSONField(default=dict, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    user_metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.dataset_name

    class Meta:
        ordering = ["modified_at"]

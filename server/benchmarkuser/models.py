from django.contrib.auth.models import User
from django.db import models


class BenchmarkUser(models.Model):

    USER_ROLES = (
        ("BenchmarkOwner", "BenchmarkOwner"),
        ("DataOwner", "DataOwner"),
        ("ModelOwner", "ModelOwner"),
    )

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    benchmark = models.ForeignKey(
        "benchmark.Benchmark", on_delete=models.CASCADE
    )
    role = models.CharField(choices=USER_ROLES, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("user", "benchmark", "role"),)
        ordering = ["modified_at"]

from django.db import models
from django.contrib.auth import get_user_model
from mlcube.models import MlCube

User = get_user_model()


class DataPrepWorkflow(models.Model):
    name = models.CharField(max_length=20, unique=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    prep_tarball_url = models.CharField(max_length=256)
    prep_tarball_hash = models.CharField(max_length=100)
    containers = models.ManyToManyField(MlCube)
    is_valid = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    user_metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.constraints.UniqueConstraint(
                fields=["prep_tarball_hash"],
                name="unique_tarball_hash_for_workflow",
            )
        ]
        verbose_name_plural = "DataPrepWorkflows"
        ordering = ["modified_at"]

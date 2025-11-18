from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MlCube(models.Model):
    MLCUBE_STATE = (
        ("DEVELOPMENT", "DEVELOPMENT"),
        ("OPERATION", "OPERATION"),
    )

    name = models.CharField(max_length=128, unique=True)
    container_config = models.JSONField()
    parameters_config = models.JSONField(blank=True, null=True)
    image_tarball_url = models.CharField(max_length=256, blank=True)
    image_tarball_hash = models.CharField(max_length=100, blank=True)
    image_hash = models.CharField(max_length=100, blank=True)
    additional_files_tarball_url = models.CharField(max_length=256, blank=True)
    additional_files_tarball_hash = models.CharField(max_length=100, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    state = models.CharField(
        choices=MLCUBE_STATE, max_length=100, default="DEVELOPMENT"
    )
    is_valid = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    user_metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (
            (
                "image_tarball_hash",
                "image_hash",
                "additional_files_tarball_hash",
                "container_config",
                "parameters_config",
            ),
        )
        verbose_name_plural = "MlCubes"
        ordering = ["modified_at"]

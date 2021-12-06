from django.db import models
from django.contrib.auth.models import User


class MlCube(models.Model):

    name = models.CharField(max_length=20)
    git_mlcube_url = models.CharField(max_length=256)
    git_parameters_url = models.CharField(max_length=256)
    tarball_url = models.CharField(max_length=256, blank=True)
    tarball_hash = models.CharField(max_length=100, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "MlCubes"
        ordering = ["modified_at"]

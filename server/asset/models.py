from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

LOCAL_ASSET_URL = "local"


class Asset(models.Model):
    ASSET_STATE = (
        ("DEVELOPMENT", "DEVELOPMENT"),
        ("OPERATION", "OPERATION"),
    )

    name = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    asset_hash = models.CharField(max_length=100)
    asset_url = models.CharField(max_length=256)
    state = models.CharField(choices=ASSET_STATE, max_length=100, default="DEVELOPMENT")
    is_valid = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    user_metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_local(self):
        return self.asset_url == LOCAL_ASSET_URL

    class Meta:
        ordering = ["modified_at"]

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class Model(models.Model):
    MODEL_TYPE = (
        ("ASSET", "ASSET"),
        ("CONTAINER", "CONTAINER"),
    )
    MODEL_STATE = (
        ("DEVELOPMENT", "DEVELOPMENT"),
        ("OPERATION", "OPERATION"),
    )

    name = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    state = models.CharField(choices=MODEL_STATE, max_length=100, default="DEVELOPMENT")
    is_valid = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    user_metadata = models.JSONField(default=dict, blank=True, null=True)

    type = models.CharField(choices=MODEL_TYPE, max_length=100)
    container = models.ForeignKey(
        "mlcube.MlCube", null=True, blank=True, on_delete=models.PROTECT
    )
    asset = models.ForeignKey(
        "asset.Asset", null=True, blank=True, on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.type == "CONTAINER":
            if not self.container:
                raise ValidationError(
                    "Container must be set for CONTAINER type models."
                )
            if self.asset:
                raise ValidationError(
                    "Asset must not be set for CONTAINER type models."
                )
        elif self.type == "ASSET":
            if not self.asset:
                raise ValidationError("Asset must be set for FILE type models.")
            if self.container:
                raise ValidationError("Container must not be set for FILE type models.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["modified_at"]

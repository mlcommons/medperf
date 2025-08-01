from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ContainerCA(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    associated_ca = models.ForeignKey("ca.CA", on_delete=models.PROTECT)
    model_mlcube = models.ForeignKey(
        "mlcube.MlCube", on_delete=models.PROTECT, related_name="model_mlcube"
    )
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["associated_ca", "model_mlcube"], name="Unique_CA_and_Model"
            )
        ]

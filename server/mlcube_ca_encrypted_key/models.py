from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ModelCAEncryptedKey(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)  # Model owner
    name = models.CharField(max_length=20)
    ca_association = models.ForeignKey(
        "mlcube_ca_association.ContainerCA",
        on_delete=models.CASCADE,
        null=False,
    )
    data_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="data_owner", null=True
    )
    encrypted_key_base64 = models.TextField(null=False)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["ca_association", "data_owner"],
                name="One_Key_Per_Owner_And_Association",
            )
        ]

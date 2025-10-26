from django.db import models
from django.contrib.auth import get_user_model
from certificate.models import Certificate
from mlcube.models import MlCube
from django.core.exceptions import ValidationError

User = get_user_model()


class ModelCAEncryptedKey(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)  # Model owner
    name = models.CharField(max_length=20)
    certificate = models.ForeignKey(Certificate, on_delete=models.PROTECT)
    container = models.ForeignKey(MlCube, on_delete=models.CASCADE)
    encrypted_key_base64 = models.TextField(null=False)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.owner != self.container.owner:
            raise ValidationError(
                f"Owner of {self.__class__.__name__} instance must "
                "match the owner of the provided model container!"
            )
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["certificate", "container"],
                name="One_Key_Per_Certificate_And_Model",
            )
        ]

from django.db import models
from django.contrib.auth import get_user_model
from certificate.models import Certificate
from mlcube.models import MlCube

User = get_user_model()


class MlCubeKey(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True)
    certificate = models.ForeignKey(Certificate, on_delete=models.PROTECT)
    container = models.ForeignKey(MlCube, on_delete=models.CASCADE)
    is_valid = models.BooleanField(default=True)
    encrypted_key_base64 = models.TextField(null=False)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["certificate", "container"],
                condition=models.Q(is_valid=True),
                name="One_Key_Per_Certificate_And_Container",
            )
        ]

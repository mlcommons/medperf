from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CA(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True)
    config = models.JSONField()
    client_mlcube = models.ForeignKey(
        "mlcube.MlCube", on_delete=models.PROTECT, related_name="ca_client"
    )
    server_mlcube = models.ForeignKey(
        "mlcube.MlCube", on_delete=models.PROTECT, related_name="ca_server"
    )
    ca_mlcube = models.ForeignKey(
        "mlcube.MlCube", on_delete=models.PROTECT, related_name="ca"
    )
    is_valid = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.config

    class Meta:
        ordering = ["created_at"]

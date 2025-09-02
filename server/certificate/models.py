from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Certificate(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True)
    ca = models.ForeignKey("ca.CA", on_delete=models.PROTECT)
    certificate_content_base64 = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["certificate_content_base64", "ca_id", "owner"],
                name="Unique_Certificate_Per_CA_and_Owner",
            )
        ]

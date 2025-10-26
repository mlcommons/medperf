from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Certificate(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True)
    is_valid = models.BooleanField(default=True)
    ca = models.ForeignKey("ca.CA", on_delete=models.PROTECT)
    certificate_content_base64 = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.constraints.UniqueConstraint(
                fields=["owner", "ca"],
                condition=models.Q(is_valid=True),
                name="One_Certificate_Per_User_And_CA",
            )
        ]

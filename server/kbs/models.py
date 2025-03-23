from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class KBS(models.Model):
    TYPES = (
        ("kbs", "kbs"),  # config: url, port, cert
        ("as", "as"),  # config: url, port, cert, token verification cert
    )
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True)
    config = models.JSONField()
    kbs_type = models.CharField(choices=TYPES, max_length=100)
    is_valid = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.config)

    class Meta:
        ordering = ["created_at"]

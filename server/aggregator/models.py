from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Aggregator(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True)
    server_config = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.server_config

    class Meta:
        ordering = ["created_at"]

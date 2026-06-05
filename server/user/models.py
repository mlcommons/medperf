from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserExtension(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    metadata = models.JSONField(default=dict)

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Aggregator(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=300)
    port = models.IntegerField()
    aggregation_mlcube = models.ForeignKey(
        "mlcube.MlCube",
        on_delete=models.PROTECT,
        related_name="aggregators",
    )
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.address

    class Meta:
        ordering = ["created_at"]

from django.db import models
from django.contrib.auth import get_user_model
from django.http import Http404

User = get_user_model()


class ContainerCA(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    associated_ca = models.ForeignKey("ca.CA", on_delete=models.PROTECT)
    model_mlcube = models.ForeignKey(
        "mlcube.MlCube", on_delete=models.PROTECT, related_name="model_mlcube"
    )
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ModelCAAssociation(Model={self.model_mlcube.id}, CA={self.associated_ca.id})"

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["associated_ca", "model_mlcube"], name="Unique_CA_and_Model"
            )
        ]

    @classmethod
    def get_by_model_id(cls, model_id):
        ca_association = (
            ContainerCA.objects.filter(model_mlcube__id=model_id)
            .order_by("created_at")
            .last()
        )

        if ca_association is None:
            raise Http404(
                f"No CA association was found for the given Container ID ({model_id}). Please verify the Container ID."
            )

        return ca_association

    @classmethod
    def get_by_model_id_and_ca_id(cls, model_id, ca_id):
        try:
            ca_association = ContainerCA.objects.get(
                model_mlcube__id=model_id, associated_ca__id=ca_id
            )
        except ContainerCA.DoesNotExist:
            raise Http404(
                f"No CA association was found for the Model ID {model_id} and CA ID {ca_id}. Please verify the inputs."
            )

        return ca_association

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TrainingExperiment(models.Model):
    EXP_STATUS = (
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
    )
    STATES = (
        ("DEVELOPMENT", "DEVELOPMENT"),
        ("OPERATION", "OPERATION"),
    )

    name = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=100, blank=True)
    docs_url = models.CharField(max_length=100, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    demo_dataset_tarball_url = models.CharField(max_length=256)
    demo_dataset_tarball_hash = models.CharField(max_length=100)
    demo_dataset_generated_uid = models.CharField(max_length=128)
    data_preparation_mlcube = models.ForeignKey(
        "mlcube.MlCube",
        on_delete=models.PROTECT,
        related_name="training_exp",
    )
    fl_mlcube = models.ForeignKey(
        "mlcube.MlCube",
        on_delete=models.PROTECT,
        related_name="fl_mlcube",
    )

    metadata = models.JSONField(default=dict, blank=True, null=True)
    # TODO: consider if we want to enable restarts and epochs/"fresh restarts"
    state = models.CharField(choices=STATES, max_length=100, default="DEVELOPMENT")
    is_valid = models.BooleanField(default=True)
    approval_status = models.CharField(
        choices=EXP_STATUS, max_length=100, default="PENDING"
    )
    plan = models.JSONField(blank=True, null=True)

    user_metadata = models.JSONField(default=dict, blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def event(self):
        return self.events.all().order_by("created_at").last()

    @property
    def aggregator(self):
        aggregator_assoc = (
            self.experimentaggregator_set.all().order_by("created_at").last()
        )
        if aggregator_assoc and aggregator_assoc.approval_status == "APPROVED":
            return aggregator_assoc.aggregator

    @property
    def ca(self):
        ca_assoc = self.experimentca_set.all().order_by("created_at").last()
        if ca_assoc and ca_assoc.approval_status == "APPROVED":
            return ca_assoc.ca

    class Meta:
        ordering = ["modified_at"]

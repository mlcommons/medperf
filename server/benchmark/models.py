from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# The topology whose script computes the metrics inside the confidential VM, so
# nothing but the encrypted results ever leaves it.
END_TO_END_TOPOLOGY = "end_to_end_script"


class Benchmark(models.Model):
    BENCHMARK_STATUS = (
        ("PENDING", "PENDING"),
        ("APPROVED", "APPROVED"),
        ("REJECTED", "REJECTED"),
    )

    BENCHMARK_STATE = (
        ("DEVELOPMENT", "DEVELOPMENT"),
        ("OPERATION", "OPERATION"),
    )

    AUTO_APPROVAL_MODE = (
        ("NEVER", "NEVER"),
        ("ALWAYS", "ALWAYS"),
        ("ALLOWLIST", "ALLOWLIST"),
    )

    # How the benchmark's parts fit together. Each topology fixes the kind of
    # model it accepts and which containers it needs; see `validate_topology`.
    BENCHMARK_TOPOLOGY = (
        ("byo_inference_script", "byo_inference_script"),
        (END_TO_END_TOPOLOGY, END_TO_END_TOPOLOGY),
        ("inference_script", "inference_script"),
    )
    name = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=256, blank=True)
    docs_url = models.CharField(max_length=100, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    demo_dataset_tarball_url = models.CharField(max_length=256)
    demo_dataset_tarball_hash = models.CharField(max_length=100)
    demo_dataset_generated_uid = models.CharField(max_length=128)
    data_preparation_mlcube = models.ForeignKey(
        "mlcube.MlCube",
        on_delete=models.PROTECT,
        related_name="data_preprocessor_mlcube",
    )
    reference_model = models.ForeignKey(
        "model.Model",
        on_delete=models.PROTECT,
        related_name="reference_model_benchmark",
    )
    topology = models.CharField(choices=BENCHMARK_TOPOLOGY, max_length=100)
    data_evaluator_mlcube = models.ForeignKey(
        "mlcube.MlCube",
        on_delete=models.PROTECT,
        related_name="data_evaluator_mlcube",
        null=True,
        blank=True,
    )
    benchmark_script = models.ForeignKey(
        "mlcube.MlCube",
        on_delete=models.PROTECT,
        related_name="benchmark_script",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True, null=True)
    state = models.CharField(
        choices=BENCHMARK_STATE, max_length=100, default="DEVELOPMENT"
    )
    is_valid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    approval_status = models.CharField(
        choices=BENCHMARK_STATUS, max_length=100, default="PENDING"
    )
    dataset_auto_approval_allow_list = models.JSONField(default=list, blank=True)
    dataset_auto_approval_mode = models.CharField(
        choices=AUTO_APPROVAL_MODE, max_length=100, default="NEVER"
    )
    model_auto_approval_allow_list = models.JSONField(default=list, blank=True)
    model_auto_approval_mode = models.CharField(
        choices=AUTO_APPROVAL_MODE, max_length=100, default="NEVER"
    )
    user_metadata = models.JSONField(default=dict, blank=True, null=True)
    committee_members = models.ManyToManyField(
        User, blank=True, related_name="committee_benchmarks"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["modified_at"]

    @property
    def committee_member_emails(self):
        return list(self.committee_members.values_list("email", flat=True))

    @property
    def is_end_to_end_topology(self):
        return self.topology == END_TO_END_TOPOLOGY

    def user_can_manage_benchmark(self, user):
        if self.owner.id == user.id:
            return True
        return self.committee_members.filter(id=user.id).exists()

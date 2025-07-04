from django.contrib import admin

from .models import Benchmark


class BenchmarkAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "docs_url",
        "owner",
        "is_valid",
        "is_active",
        "metadata",
        "user_metadata",
        "demo_dataset_tarball_url",
        "demo_dataset_tarball_hash",
        "demo_dataset_generated_uid",
        "data_preparation_mlcube",
        "reference_model_mlcube",
        "data_evaluator_mlcube",
        "dataset_list",
        "model_list",
        "approved_at",
        "approval_status",
        "created_at",
        "modified_at",
        "dataset_auto_approval_allow_list",
        "dataset_auto_approval_mode",
        "model_auto_approval_allow_list",
        "model_auto_approval_mode",
    )

    def dataset_list(self, obj):
        return ",".join([gp.dataset.name for gp in obj.benchmarkdataset_set.all()])

    dataset_list.short_description = "Registered Datasets"

    def model_list(self, obj):
        return ",".join([gp.model_mlcube.name for gp in obj.benchmarkmodel_set.all()])

    model_list.short_description = "Registered Models"


admin.site.register(Benchmark, BenchmarkAdmin)

from django.contrib import admin

from .models import Benchmark


class BenchmarkAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "docs_url",
        "owner",
        "data_preparation_mlcube",
        "reference_model_mlcube",
        "data_evaluator_mlcube",
        "dataset_list",
        "model_list",
        "approved_at",
        "approval_status",
        "created_at",
        "modified_at",
    )

    def dataset_list(self, obj):
        return ",".join(
            [gp.dataset.name for gp in obj.benchmarkdataset_set.all()]
        )

    dataset_list.short_description = "Registered Datasets"

    def model_list(self, obj):
        return ",".join(
            [gp.model_mlcube.name for gp in obj.benchmarkmodel_set.all()]
        )

    model_list.short_description = "Registered Models"


admin.site.register(Benchmark, BenchmarkAdmin)

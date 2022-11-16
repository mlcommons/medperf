from django.contrib import admin
from .models import BenchmarkDataset


class BenchmarkDatasetAdmin(admin.ModelAdmin):
    list_display = (
        "dataset",
        "benchmark",
        "initiated_by",
        "metadata",
        "approval_status",
        "approved_at",
        "created_at",
        "modified_at",
    )


admin.site.register(BenchmarkDataset, BenchmarkDatasetAdmin)

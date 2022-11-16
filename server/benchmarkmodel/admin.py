from django.contrib import admin
from .models import BenchmarkModel


class BenchmarkModelAdmin(admin.ModelAdmin):
    list_display = (
        "model_mlcube",
        "benchmark",
        "initiated_by",
        "metadata",
        "approval_status",
        "approved_at",
        "created_at",
        "modified_at",
    )


admin.site.register(BenchmarkModel, BenchmarkModelAdmin)

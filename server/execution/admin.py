from django.contrib import admin
from .models import Execution


class ExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "benchmark",
        "model",
        "dataset",
        "results",
        "metadata",
        "approval_status",
        "approved_at",
        "created_at",
        "modified_at",
        "model_report",
        "evaluation_report",
        "finalized",
        "finalized_at",
    )


admin.site.register(Execution, ExecutionAdmin)

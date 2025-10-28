from django.contrib import admin
from .models import DataPrepWorkflow


class DataPrepWorkflowAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "prep_tarball_url",
        "prep_tarball_hash",
    )


admin.site.register(DataPrepWorkflow, DataPrepWorkflowAdmin)

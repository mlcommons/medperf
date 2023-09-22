from django.contrib import admin
from .models import Report


class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "dataset_name",
        "description",
        "location",
        "owner",
        "input_data_hash",
        "data_preparation_mlcube",
        "is_valid",
        "contents",
        "metadata",
        "user_metadata",
        "created_at",
        "modified_at",
    )


admin.site.register(Report, ReportAdmin)

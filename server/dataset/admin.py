from django.contrib import admin
from .models import Dataset


class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "location",
        "owner",
        "input_data_hash",
        "generated_uid",
        "split_seed",
        "data_preparation_mlcube",
        "state",
        "is_valid",
        "generated_metadata",
        "user_metadata",
        "report",
        "created_at",
        "modified_at",
    )


admin.site.register(Dataset, DatasetAdmin)

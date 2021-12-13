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
        "is_valid",
        "split_seed",
        "data_preparation_mlcube",
        "metadata",
        "created_at",
        "modified_at",
    )


admin.site.register(Dataset, DatasetAdmin)

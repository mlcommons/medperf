from django.contrib import admin
from .models import Dataset


class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
        "location",
        "owner",
        "generated_uid",
        "split_seed",
        "data_preparation_mlcube",
        "metadata",
        "created_at",
        "modified_at",
    )


admin.site.register(Dataset, DatasetAdmin)

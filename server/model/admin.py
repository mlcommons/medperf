from django.contrib import admin
from .models import Model


class ModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "container",
        "asset",
        "created_at",
        "modified_at",
        "name",
        "owner",
        "state",
        "is_valid",
        "metadata",
        "user_metadata",
    )


admin.site.register(Model, ModelAdmin)

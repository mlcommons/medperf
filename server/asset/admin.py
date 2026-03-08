from django.contrib import admin
from .models import Asset


class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "asset_hash",
        "asset_url",
        "state",
        "is_valid",
        "metadata",
        "user_metadata",
        "created_at",
        "modified_at",
    )


admin.site.register(Asset, AssetAdmin)

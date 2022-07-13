from django.contrib import admin
from .models import MlCube


class MlCubeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "git_mlcube_url",
        "git_parameters_url",
        "image_tarball_url",
        "image_tarball_hash",
        "additional_files_tarball_url",
        "additional_files_tarball_hash",
        "owner",
        "state",
        "is_valid",
        "metadata",
        "user_metadata",
        "created_at",
        "modified_at",
    )


admin.site.register(MlCube, MlCubeAdmin)

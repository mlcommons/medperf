from django.contrib import admin
from .models import MlCubeKey


@admin.register(MlCubeKey)
class MlCubeKeyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in MlCubeKey._meta.fields]

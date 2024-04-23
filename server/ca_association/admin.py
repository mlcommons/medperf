from django.contrib import admin
from .models import ExperimentCA


@admin.register(ExperimentCA)
class ExperimentCAAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ExperimentCA._meta.fields]

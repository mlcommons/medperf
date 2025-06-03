from django.contrib import admin
from .models import ExperimentDataset


@admin.register(ExperimentDataset)
class ExperimentDatasetAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ExperimentDataset._meta.fields]

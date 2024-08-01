from django.contrib import admin
from .models import ExperimentAggregator


@admin.register(ExperimentAggregator)
class ExperimentAggregatorAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ExperimentAggregator._meta.fields]

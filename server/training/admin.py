from django.contrib import admin

from .models import TrainingExperiment, DatasetTrainingKit, AggregatorTrainingKit


class TrainingExperimentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TrainingExperiment._meta.fields]


class DatasetTrainingKitAdmin(admin.ModelAdmin):
    list_display = [field.name for field in DatasetTrainingKit._meta.fields]


class AggregatorTrainingKitAdmin(admin.ModelAdmin):
    list_display = [field.name for field in AggregatorTrainingKit._meta.fields]


admin.site.register(TrainingExperiment, TrainingExperimentAdmin)


admin.site.register(DatasetTrainingKit, DatasetTrainingKitAdmin)


admin.site.register(AggregatorTrainingKit, AggregatorTrainingKitAdmin)

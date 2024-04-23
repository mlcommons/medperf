from django.contrib import admin

from .models import TrainingExperiment


class TrainingExperimentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TrainingExperiment._meta.fields]


admin.site.register(TrainingExperiment, TrainingExperimentAdmin)

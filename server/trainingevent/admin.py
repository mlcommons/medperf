from django.contrib import admin
from .models import TrainingEvent


@admin.register(TrainingEvent)
class TrainingEventAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TrainingEvent._meta.fields]

from django.contrib import admin
from .models import Aggregator


@admin.register(Aggregator)
class AggregatorAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Aggregator._meta.fields]

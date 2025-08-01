from django.contrib import admin
from .models import ContainerCA


@admin.register(ContainerCA)
class ContainerCAAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ContainerCA._meta.fields]

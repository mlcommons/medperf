from django.contrib import admin
from .models import KBS


@admin.register(KBS)
class KbsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in KBS._meta.fields]

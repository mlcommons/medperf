from django.contrib import admin
from .models import CA


@admin.register(CA)
class CAAdmin(admin.ModelAdmin):
    list_display = [field.name for field in CA._meta.fields]

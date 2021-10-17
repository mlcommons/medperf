from django.contrib import admin
from .models import BenchmarkUser


class BenchmarkUserAdmin(admin.ModelAdmin):
    list_display = ("user", "benchmark", "role", "created_at", "modified_at")


admin.site.register(BenchmarkUser, BenchmarkUserAdmin)

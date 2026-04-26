from django.contrib import admin
from .models import UserExtension


class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "first_name", "last_name")


@admin.register(UserExtension)
class UserExtensionAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserExtension._meta.fields]

from django.contrib import admin
from .models import ModelCAEncryptedKey


@admin.register(ModelCAEncryptedKey)
class ModelCAEncryptedKeyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in ModelCAEncryptedKey._meta.fields]

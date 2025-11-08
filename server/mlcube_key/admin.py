from django.contrib import admin
from .models import EncryptedKey


@admin.register(EncryptedKey)
class EncryptedKeyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in EncryptedKey._meta.fields]

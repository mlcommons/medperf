from django.contrib import admin


class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "first_name", "last_name")

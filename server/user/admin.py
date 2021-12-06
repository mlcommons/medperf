from django.contrib import admin


class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "password", "first_name", "last_name")

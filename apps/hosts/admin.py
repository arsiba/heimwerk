# apps/hosts/admin.py
from django.contrib import admin
from .models import DockerHost


@admin.register(DockerHost)
class DockerHostAdmin(admin.ModelAdmin):
    list_display = ("name", "base_url", "active")
    list_filter = ("active",)

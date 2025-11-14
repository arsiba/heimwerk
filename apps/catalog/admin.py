from django.contrib import admin

from apps.catalog.models import Instance, Module

# Register your models here.
admin.site.register(Module)
admin.site.register(Instance)

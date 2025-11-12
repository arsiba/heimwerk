from django.contrib import admin
from django.contrib.auth.models import User

from serviceCatalog.models import Instance, Module

# Register your models here.
admin.site.register(Module)
admin.site.register(Instance)

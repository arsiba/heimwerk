from django.contrib import admin
from django.contrib.auth.models import User

from serviceCatalog.models import TF_Module, Instance

# Register your models here.
admin.site.register(TF_Module)
admin.site.register(Instance)
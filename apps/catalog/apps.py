from django.apps import AppConfig

from core.docker.client import init_docker


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"

    def ready(self):
        client = init_docker()

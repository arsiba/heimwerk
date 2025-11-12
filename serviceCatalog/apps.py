from django.apps import AppConfig

from deployDocker.docker_tools import init_docker


class ServicecatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "serviceCatalog"

    def ready(self):
        import serviceCatalog.signals

        client = init_docker()

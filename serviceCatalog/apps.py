from django.apps import AppConfig


class ServicecatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "serviceCatalog"

    def ready(self):
        import serviceCatalog.signals

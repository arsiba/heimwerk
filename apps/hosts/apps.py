from django.apps import AppConfig


class HostsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.hosts"

    def ready(self):
        from django.db.utils import OperationalError, ProgrammingError
        from django.apps import apps as django_apps

        docker_host = django_apps.get_model("hosts", "DockerHost")

        try:
            docker_host.objects.update(active=False)

            if not docker_host.objects.exists():
                docker_host.objects.create(
                    name="Default Docker host",
                    base_url="",
                    active=False,
                    pangolin_features=False,
                )

        except (OperationalError, ProgrammingError):
            pass

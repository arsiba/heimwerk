import uuid

from django.db import models

from core.docker.client import test_client_config


class DockerHost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Name, e.g. 'local Docker host'")
    base_url = models.CharField(
        max_length=255,
        help_text="z.B. tcp://127.0.0.1:2375 or unix:///var/run/docker.sock",
    )
    active = models.BooleanField(default=False)
    pangolin_features = models.BooleanField(default=False)
    default_domain = models.URLField(max_length=200, null=True)

    class Meta:
        verbose_name = "Docker Host"
        verbose_name_plural = "Docker Hosts"

    def __str__(self):
        return self.name

    def test_config(self):
        return test_client_config(self.base_url)

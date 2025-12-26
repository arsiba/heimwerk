import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify

from core.utils.common import restart_choices


class Module(models.Model):
    """
    Represents a reusable module, e.g., a Docker container template.
    All necessary parameters for container instantiation are stored separately.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Name of the module")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(
        blank=True, help_text="Short description of the module"
    )

    image_name = models.CharField(
        max_length=200,
        help_text="Docker image name, e.g., nginx:latest",
        default="willFail:fail",
    )
    container_port = models.PositiveIntegerField(
        blank=True, null=True, help_text="Default port mapping, e.g. 80"
    )
    default_env = models.JSONField(
        blank=True,
        null=True,
        help_text="Default environment variables, e.g., {'ENV_VAR': 'value'}",
    )
    default_restart_policy = models.CharField(
        blank=True,
        null=True,
        choices=restart_choices,
        help_text="Default restart policy, e.g., {'Name': 'always'}",
    )
    module_image = models.ImageField(upload_to="images/", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("module-detail", args=[self.slug])

    def __str__(self):
        return self.name

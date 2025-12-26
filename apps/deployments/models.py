import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils.text import slugify

from apps.catalog.models import Module
from core.utils.common import restart_choices, STATUS_CHOICES


class Instance(models.Model):
    """
    Represents an instance of a Module, e.g., a running Docker container.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=50, unique=True, help_text="Unique name for the instance"
    )
    slug = models.SlugField(max_length=120, blank=True)

    owner = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="instances")
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="instances"
    )
    image_name = models.CharField(
        max_length=200,
        help_text="Docker image name, e.g., nginx:latest",
        default="willFail:fail",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Store actual runtime parameters and output from Docker
    container_port = models.PositiveIntegerField(
        blank=True, null=True, help_text="Container Port used for this instance"
    )

    host_port = models.PositiveIntegerField(
        blank=True, null=True, help_text="Host Port used for this instance"
    )

    environment = models.JSONField(
        blank=True, null=True, help_text="Environment variables used"
    )
    default_restart_policy = models.CharField(
        blank=True,
        null=True,
        choices=restart_choices,
    )
    container_id = models.CharField(
        max_length=64, blank=True, null=True, help_text="Docker container ID"
    )
    docker_output = models.JSONField(
        blank=True, null=True, help_text="Docker API output or metadata"
    )

    pangolin_name = models.CharField(max_length=100, blank=True, null=True)
    pangolin_resource_domain = models.URLField(max_length=200, blank=True, null=True)
    pangolin_protocol = models.CharField(max_length=10, blank=True, null=True)
    pangolin_target_protocol = models.CharField(max_length=10, blank=True, null=True)
    pangolin_port = models.PositiveIntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            UniqueConstraint(
                Lower("name"),
                name="unique_instance_name",
                violation_error_message="This instance name is already in use.",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.module.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def is_active(self):
        return self.status == "running"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("deployments:instance-detail", args=[self.slug])

    def get_local_resource_url(self):
        return f"127.0.0.1:{self.host_port}"

    def get_external_resource_url(self):
        return self.pangolin_resource_domain

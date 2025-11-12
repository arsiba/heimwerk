import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils.text import slugify


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
    default_ports = models.JSONField(
        blank=True, null=True, help_text="Default port mapping, e.g., {'80/tcp': 8080}"
    )
    default_env = models.JSONField(
        blank=True,
        null=True,
        help_text="Default environment variables, e.g., {'ENV_VAR': 'value'}",
    )
    default_restart_policy = models.JSONField(
        blank=True,
        null=True,
        help_text="Default restart policy, e.g., {'Name': 'always'}",
    )

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


class Instance(models.Model):
    """
    Represents an instance of a Module, e.g., a running Docker container.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("failed", "Failed"),
        ("stopped", "Stopped"),
        ("destroyed", "Destroyed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=50, unique=True, help_text="Unique name for the instance"
    )
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
    ports = models.JSONField(
        blank=True, null=True, help_text="Port mapping used for this instance"
    )
    environment = models.JSONField(
        blank=True, null=True, help_text="Environment variables used"
    )
    restart_policy = models.JSONField(
        blank=True, null=True, help_text="Restart policy used"
    )
    container_id = models.CharField(
        max_length=64, blank=True, null=True, help_text="Docker container ID"
    )
    docker_output = models.JSONField(
        blank=True, null=True, help_text="Docker API output or metadata"
    )

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

    def is_active(self):
        return self.status == "running"


class UserProfile(models.Model):
    """
    Stores additional information for a user, e.g., quotas.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    quota = models.PositiveIntegerField(
        default=3, help_text="Maximum number of instances user can create"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        group_name = (
            self.user.groups.first().name if self.user.groups.exists() else "No Group"
        )
        return f"{self.user.username} ({group_name})"

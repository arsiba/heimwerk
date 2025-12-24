import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils.text import slugify

restart_choices = [
    ("no", "No"),
    ("on-failure", "On failure"),
    ("always", "Always"),
    ("unless-stopped", "Unless stopped"),
]


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


class Instance(models.Model):
    """
    Represents an instance of a Module, e.g., a running Docker container.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("paused", "Paused"),
        ("exited", "Exited"),
        ("stopped", "Stopped"),
        ("destroyed", "Destroyed"),
        ("failed", "Failed"),
    ]

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

        return reverse("instance-detail", args=[self.slug])

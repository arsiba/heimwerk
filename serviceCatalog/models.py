import uuid
from django.contrib.auth.models import User
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils.text import slugify


class TF_Module(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name des Terraform-Moduls"
    )

    slug = models.SlugField(max_length=120, unique=True, blank=True)

    description = models.TextField(
        blank=True,
        help_text="Kurzbeschreibung des Moduls"
    )
    module_code = models.TextField(
        help_text="Terraform-Code oder Pfad zum Modul"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('module-detail', args=[self.slug])

    def __str__(self):
        return self.name


class Instance(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Eindeutiger Name der Instanz"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.RESTRICT
    )
    module = models.ForeignKey(
        TF_Module,
        on_delete=models.CASCADE,
        related_name='instances',
        help_text="Das Terraform-Modul, das instanziiert wurde"
    )
    status = models.CharField(
        max_length=20,
        default="pending",
        help_text="Status der Instanz (pending, running, failed, destroyed, etc.)"
    )
    terraform_output = models.JSONField(
        blank=True,
        null=True,
        help_text="Terraform-Ausgabe oder Metadaten zur Instanz"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='unique_instance_name',
                violation_error_message='Dieser Instanzname wird bereits verwendet.'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.module.name})"


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    quota = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.user.groups.first() or 'ohne Gruppe'})"
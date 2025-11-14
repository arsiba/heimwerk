import uuid

from django.contrib.auth.models import User
from django.db import models


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

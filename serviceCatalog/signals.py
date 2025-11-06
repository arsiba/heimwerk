from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, User
from .models import UserProfile

# Diese Gruppen sollen immer existieren
DEFAULT_GROUPS = ["guest", "user", "editor"]


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """Wird nach jeder Migration ausgeführt und legt Standardgruppen an."""
    for group_name in DEFAULT_GROUPS:
        Group.objects.get_or_create(name=group_name)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Erstellt ein Profil und ordnet neue User automatisch einer Gruppe zu."""
    if created:
        # Standardgruppe bestimmen – z. B. immer "user"
        default_group = Group.objects.get(name="guest")
        instance.groups.add(default_group)

        # Profil anlegen
        UserProfile.objects.create(user=instance)

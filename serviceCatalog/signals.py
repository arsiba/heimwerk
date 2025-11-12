from django.contrib.auth.models import Group, User
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

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
    """Erstellt ein Profil und ordnet neue User automatisch Gruppen zu."""
    if created:
        # Stelle sicher, dass alle Default-Gruppen existieren
        create_default_groups(sender)

        if instance.is_superuser:
            # Superuser -> bekommt 'editor' + 'user'
            editor_group = Group.objects.get(name="editor")
            user_group = Group.objects.get(name="user")
            instance.groups.add(editor_group, user_group)
        else:
            # Normale User -> bekommen z. B. 'guest'
            guest_group = Group.objects.get(name="guest")
            instance.groups.add(guest_group)

        # UserProfile anlegen
        UserProfile.objects.create(user=instance)

# main/context_processors.py

from .models import Instance


def global_user_context(request):
    """Fügt benutzerbezogene Informationen zu jedem Template-Kontext hinzu."""
    user = request.user

    if not user.is_authenticated:
        return {
            "is_admin": False,
            "is_editor": False,
            "is_user": False,
            "user_instances_count": 0,
            "all_instances_count": 0,
            "can_deploy": False,
        }

    is_admin = user.is_superuser
    is_editor = user.groups.filter(name="editor").exists()
    is_user = user.groups.filter(name="user").exists()

    user_instances_count = Instance.objects.filter(owner=user).count()
    all_instances_count = Instance.objects.count()
    can_deploy = is_admin or is_editor or is_user

    return {
        "is_admin": is_admin,
        "is_editor": is_editor,
        "is_user": is_user,
        "user_instances_count": user_instances_count,
        "all_instances_count": all_instances_count,
        "can_deploy": can_deploy,
    }

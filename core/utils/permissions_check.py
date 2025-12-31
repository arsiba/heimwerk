def user_can_deploy(user):
    return user.is_superuser or user.groups.filter(name__in=["user", "editor"]).exists()


def user_can_edit(user):
    return user.is_superuser or user.groups.filter(name="editor").exists()


def user_can_administrate(user):
    return user.is_superuser or user.groups.filter(name="editor").exists()

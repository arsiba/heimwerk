import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, render
from django.views import generic, View

from apps.users.models import UserProfile
from core.utils.permissions_check import user_can_administrate


class UsersListView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "users/users_list.html"

    def test_func(self):
        return user_can_administrate(self.request.user)

    def get(self, request):
        userProfiles = (
            UserProfile.objects.select_related("user")
            .prefetch_related("user__groups")
            .all()
        )
        context = {"userProfiles": userProfiles}

        return render(request, self.template_name, context)

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from django.views import generic

from core.utils.permissions_check import user_can_edit
from .models import Module
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView


def index(request):
    """View function for home page of site."""
    modules = Module.objects.all()
    context = {
        "modules": modules,
    }
    return render(request, "index.html", context=context)


class ModuleDetailView(generic.DetailView):
    """Generic class-based detail view for a module."""

    model = Module
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["user_instances"] = self.object.instances.filter(
                owner=self.request.user
            )
        if self.request.user.is_superuser:
            context["user_instances"] = self.object.instances.all()
        else:
            context["user_instances"] = []
        context["can_deploy"] = (
            self.request.user.groups.filter(name="user").exists()
            or self.request.user.groups.filter(name="editor").exists()
        )
        return context


class ModuleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    def test_func(self):
        user = self.request.user
        return user_can_edit(user)

    model = Module
    fields = "__all__"


class ModuleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    def test_func(self):
        user = self.request.user
        return user_can_edit(user)

    model = Module
    slug_field = "slug"
    slug_url_kwarg = "slug"
    fields = "__all__"

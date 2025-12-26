from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from django.views import generic
from .models import Module
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView


def index(request):
    """View function for home page of site."""

    modules = Module.objects.all()[:5]

    num_visits = request.session.get("num_visits", 0)
    num_visits += 1
    user = request.user

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


def user_can_deploy(user):
    return user.is_superuser or user.groups.filter(name__in=["user", "editor"]).exists()


def user_can_edit(user):
    return user.is_superuser or user.groups.filter(name="editor").exists()


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

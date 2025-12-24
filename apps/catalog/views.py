from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View, generic
from django.views.decorators.http import require_POST

from core.docker.deploy import destroy_instance, pause_instance, unpause_instance

from .models import Instance, Module
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


class InstanceListView(generic.ListView):
    """Generic class-based view for a list of instances."""

    model = Instance
    paginate_by = 10

    def get_context_data(self, **kwargs):
        user = self.request.user
        owned_instances = Instance.objects.filter(owner=user)

        if user.is_superuser or user.groups.filter(name="editor").exists():
            owned_instances = Instance.objects.all()
        new_context = {
            "owned_Instances": owned_instances,
        }
        return new_context


def user_can_deploy(user):
    return user.is_superuser or user.groups.filter(name__in=["user", "editor"]).exists()


def user_can_edit(user):
    return user.is_superuser or user.groups.filter(name="editor").exists()


class InstanceDetailView(LoginRequiredMixin, UserPassesTestMixin, generic.DetailView):
    """Generic class-based detail view for a instance."""

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user == self.get_object().owner

    model = Instance
    slug_field = "slug"
    slug_url_kwarg = "slug"


@require_POST
def instance_action_view(request, instance_id):
    """
    Handle pause or destroy actions for an instance.
    The action type comes from a POST parameter: 'action' = 'pause' | 'destroy'
    """
    instance = get_object_or_404(Instance, id=instance_id)
    action = request.POST.get("action")

    try:
        if action == "pause":
            pause_instance(instance.id)
            messages.success(request, f"Instance '{instance.name}' paused.")
        elif action == "unpause":
            unpause_instance(instance.id)
            messages.success(request, f"Instance '{instance.name}' unpaused.")
        elif action == "destroy":
            destroy_instance(instance.id)
            messages.success(request, f"Instance '{instance.name}' destroyed.")
            return redirect("index")
        else:
            messages.error(request, "Unknown action.")
    except Exception as e:
        messages.error(request, f"Failed to perform action '{action}': {e}")

    return redirect("instance-detail", instance.slug)


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

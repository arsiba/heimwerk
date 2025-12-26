import json
import threading
from cProfile import label

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View, generic
from django.views.decorators.http import require_POST

from apps.catalog.models import Module
from apps.catalog.views import user_can_deploy
from apps.deployments.models import Instance
from core.docker.deploy import (
    deploy_instance,
    get_random_free_port,
    set_pangolin_labels,
    pause_instance,
    unpause_instance,
    destroy_instance,
)


class DeployView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "deployments/deploy_form.html"

    def test_func(self):
        return user_can_deploy(self.request.user)

    def get(self, request, slug):
        module = get_object_or_404(Module, slug=slug)
        context = {
            "module": module,
        }
        return render(request, self.template_name, context)

    def post(self, request, slug):
        module = get_object_or_404(Module, slug=slug)

        name = f"{request.POST.get('name')}_{request.user.username}"

        if Instance.objects.filter(name__iexact=name).exists():
            return render(
                request,
                self.template_name,
                {
                    "module": module,
                    "error": f"Name '{name}' is already taken",
                },
            )

        instance = Instance.objects.create(
            name=name,
            owner=request.user,
            module=module,
            status="pending",
            image_name=module.image_name,
            container_port=module.container_port,
            host_port=get_random_free_port(),
            environment=module.default_env,
            default_restart_policy=module.default_restart_policy,
        )
        set_pangolin_labels(instance.id, False)

        threading.Thread(
            target=deploy_instance, args=(instance.id,), daemon=True
        ).start()

        return redirect("deployments:instance-list")


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

    return redirect("deployments:instance-detail", instance.slug)

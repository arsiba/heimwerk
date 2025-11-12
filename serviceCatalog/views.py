import json
import threading

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View, generic
from django.views.decorators.http import require_POST

from deployDocker.deploy_logic import deploy_instance, destroy_instance, pause_instance

from .models import Instance, Module


def index(request):
    """View function for home page of site."""

    modules = Module.objects.all()[:5]

    num_visits = request.session.get("num_visits", 0)
    num_visits += 1
    user = request.user

    context = {
        "modules": modules,
    }

    # Render the HTML template index.html with the data in the context variable.
    return render(request, "index.html", context=context)


class ModuleListView(generic.ListView):
    """Generic class-based view for a list of modules."""

    model = Module
    paginate_by = 10


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


class DeployView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "deploy_form.html"

    def test_func(self):
        return user_can_deploy(self.request.user)

    def get(self, request, slug):
        module = get_object_or_404(Module, slug=slug)

        # Konvertiere alle Default-Felder in gültige JSON-Strings
        default_ports_json = json.dumps(
            module.default_ports or {}, separators=(",", ":")
        )
        default_env_json = json.dumps(module.default_env or {}, separators=(",", ":"))
        default_restart_policy_json = json.dumps(
            module.default_restart_policy or {}, separators=(",", ":")
        )

        context = {
            "module": module,
            "default_ports_json": default_ports_json,
            "default_env_json": default_env_json,
            "default_restart_policy_json": default_restart_policy_json,
        }
        return render(request, self.template_name, context)

    def post(self, request, slug):
        module = get_object_or_404(Module, slug=slug)

        name = f"{request.POST.get('name')}_{request.user.username}"
        image_name = request.POST.get("image_name")
        ports_raw = request.POST.get("ports", "{}").strip()
        env_raw = request.POST.get("environment", "{}").strip()
        restart_policy_raw = request.POST.get("restart_policy", "{}").strip()

        ports_raw = ports_raw.replace("'", '"')
        env_raw = env_raw.replace("'", '"')
        restart_policy_raw = restart_policy_raw.replace("'", '"')

        try:
            ports = json.loads(ports_raw) if ports_raw else {}
            environment = json.loads(env_raw) if env_raw else {}
            restart_policy = (
                json.loads(restart_policy_raw) if restart_policy_raw else {}
            )
        except json.JSONDecodeError as e:
            return render(
                request,
                self.template_name,
                {
                    "module": module,
                    "error": f"JSON parse error: {e}",
                    "old_data": request.POST,
                    "default_ports_json": ports_raw,
                    "default_env_json": env_raw,
                    "default_restart_policy_json": restart_policy_raw,
                },
            )

        if Instance.objects.filter(name__iexact=name).exists():
            return render(
                request,
                self.template_name,
                {
                    "module": module,
                    "error": f"Name '{name}' is already taken",
                    "old_data": request.POST,
                    "default_ports_json": ports_raw,
                    "default_env_json": env_raw,
                    "default_restart_policy_json": restart_policy_raw,
                },
            )

        instance = Instance.objects.create(
            name=name,
            owner=request.user,
            module=module,
            status="pending",
            image_name=image_name,
            ports=ports,
            environment=environment,
            restart_policy=restart_policy,
        )

        threading.Thread(
            target=deploy_instance, args=(instance.id,), daemon=True
        ).start()

        return redirect("instance-list")


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
    action = request.POST.get('action')

    try:
        if action == 'pause':
            pause_instance(instance.id)
            messages.success(request, f"Instance '{instance.name}' paused.")
        elif action == 'destroy':
            destroy_instance(instance.id)
            messages.success(request, f"Instance '{instance.name}' destroyed.")
            return redirect('index')  # Redirect to list after destroy
        else:
            messages.error(request, "Unknown action.")
    except Exception as e:
        messages.error(request, f"Failed to perform action '{action}': {e}")

    return redirect('instance-detail', instance.slug)

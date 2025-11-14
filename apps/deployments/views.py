import json
import threading

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.catalog.models import Instance, Module
from apps.catalog.views import user_can_deploy
from core.docker.deploy import deploy_instance


# Create your views here.
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

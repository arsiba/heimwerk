import json
import threading

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.catalog.models import Instance, Module
from apps.catalog.views import user_can_deploy
from core.docker.deploy import deploy_instance, get_random_free_port


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
            restart_policy=module.default_restart_policy,
        )

        threading.Thread(
            target=deploy_instance, args=(instance.id,), daemon=True
        ).start()

        return redirect("instance-list")

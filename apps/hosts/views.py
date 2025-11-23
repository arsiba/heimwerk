from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from django.views import View

from apps.catalog.views import user_can_edit
from apps.hosts.models import DockerHost
from core.docker.client import test_client_config, init_docker


class HostView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "hosts/host_form.html"

    def test_func(self):
        return user_can_edit(self.request.user)

    def get_object(self):
        host, _ = DockerHost.objects.get_or_create(
            defaults={
                "name": "Default Docker host",
                "base_url": "",
                "active": False,
                "pangolin_features": False,
            }
        )
        return host

    def get(self, request):
        docker_host = self.get_object()
        return render(request, self.template_name, {"docker_host": docker_host})

    def post(self, request):
        docker_host = self.get_object()
        action = request.POST.get("action")
        error = None

        if action == "test":
            connection = test_client_config(request.POST.get("base_url"))
            if not connection:
                return render(
                    request,
                    self.template_name,
                    {
                        "docker_host": docker_host,
                        "error": "Connection failed, please check your config",
                    },
                )
            return render(
                request,
                self.template_name,
                {"docker_host": docker_host, "connection": "Connection successful"},
            )

        elif action == "save":
            docker_host.base_url = request.POST.get("base_url", "")
            docker_host.pangolin_features = "pangolin_features" in request.POST
            docker_host.save()

            if docker_host.test_config():
                docker_host.active = True
                init_docker(docker_host.base_url)
                docker_host.save()
            else:
                error = "Connection failed, please check your config"

            return render(
                request,
                self.template_name,
                {
                    "docker_host": docker_host,
                    "success": "Settings saved",
                    "error": error,
                },
            )

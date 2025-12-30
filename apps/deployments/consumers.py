import asyncio
import json
import threading
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from apps.deployments.models import Instance
from core.docker.client import get_docker_client
from core.docker.deploy import get_instance_stats


class DockerLogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        self.instance_id = self.scope["url_route"]["kwargs"]["pk"]
        self.container_name = await get_container_id(self, self.instance_id)

        if not self.container_name:
            await self.close()
            return

        await self.accept()
        self.keep_running = True

        self.loop = asyncio.get_running_loop()
        self.thread = threading.Thread(target=self._stream_logs_thread)
        self.thread.start()

    async def disconnect(self, close_code):
        self.keep_running = False

    def _stream_logs_thread(self):
        """runs in background and streams logs"""
        client = get_docker_client()
        try:
            container = client.containers.get(self.container_name)
            log_stream = container.logs(
                stream=True, follow=True, stdout=True, stderr=True, tail=50
            )

            for line in log_stream:
                if not self.keep_running:
                    break

                decoded_line = line.decode("utf-8", errors="replace")

                asyncio.run_coroutine_threadsafe(
                    self.send(text_data=decoded_line), self.loop
                )
        except Exception as e:
            pass


class InstanceStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.instance_id = self.scope["url_route"]["kwargs"]["pk"]
        self.container_name = await get_container_id(self, self.instance_id)

        if not self.container_name:
            await self.close()
            return

        await self.accept()
        self.keep_running = True

        self.loop = asyncio.get_running_loop()
        self.thread = threading.Thread(target=self._stream_status_thread)
        self.thread.start()

    async def disconnect(self, close_code):
        self.keep_running = False

    def _stream_status_thread(self):
        """runs in background and streams the container status"""
        client = get_docker_client()
        status_cache = None
        try:
            container = client.containers.get(self.container_name)
            while self.keep_running:
                status = container.status
                if status_cache != status:
                    asyncio.run_coroutine_threadsafe(
                        self.send(text_data=status), self.loop
                    )
                    status_cache = status
        except Exception as e:
            pass


class InstanceStatsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.instance_id = self.scope["url_route"]["kwargs"]["pk"]
        self.container_name = await get_container_id(self, self.instance_id)

        if not self.container_name:
            await self.close()
            return

        await self.accept()
        self.keep_running = True

        self.loop = asyncio.get_running_loop()
        self.thread = threading.Thread(target=self._stream_stats_thread)
        self.thread.start()

    async def disconnect(self, close_code):
        self.keep_running = False

    def _stream_stats_thread(self):
        client = get_docker_client()
        try:
            container = client.containers.get(self.container_name)
            stats_stream = container.stats(stream=True, decode=True)

            for stats in stats_stream:
                if not self.keep_running:
                    break

                if "cpu_stats" not in stats or "precpu_stats" not in stats:
                    continue

                cpu_percent = 0.0
                cpu_delta = (
                    stats["cpu_stats"]["cpu_usage"]["total_usage"]
                    - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                )
                system_delta = stats["cpu_stats"].get("system_cpu_usage", 0) - stats[
                    "precpu_stats"
                ].get("system_cpu_usage", 0)

                if system_delta > 0.0 and cpu_delta > 0.0:
                    online_cpus = stats["cpu_stats"].get("online_cpus", 1)
                    cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0

                mem_stats = stats.get("memory_stats", {})
                usage = mem_stats.get("usage", 0)
                inactive_file = mem_stats.get("stats", {}).get("inactive_file", 0)
                memory_mib = round((usage - inactive_file) / (1024 * 1024), 2)

                data = {
                    "memory_mib": memory_mib,
                    "cpu_percent": round(cpu_percent, 2),
                }

                if self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.send(text_data=json.dumps(data)), self.loop
                    )

        except Exception as e:
            pass


@database_sync_to_async
def get_container_id(self, pk):
    try:

        if self.scope["user"].is_superuser:
            instance = Instance.objects.get(pk=pk)
        else:
            instance = Instance.objects.get(pk=pk, owner=self.scope["user"])

        return instance.container_id or instance.name
    except Instance.DoesNotExist:
        return None

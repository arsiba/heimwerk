import asyncio
import threading
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from apps.deployments.models import Instance
from core.docker.client import get_docker_client


class DockerLogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        self.instance_id = self.scope["url_route"]["kwargs"]["pk"]
        self.container_name = await self.get_container_id(self.instance_id)

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

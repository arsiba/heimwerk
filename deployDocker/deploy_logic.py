import time

from deployDocker.docker_tools import get_docker_client, pull_image, start_container
from serviceCatalog.models import Instance

DOCKER_TO_INSTANCE_STATUS = {
    "created": "pending",
    "restarting": "pending",
    "running": "running",
    "paused": "paused",
    "exited": "stopped",
    "dead": "failed",
    "removing": "destroyed",
}


def get_image(image_name):
    client = get_docker_client()
    pull_image(client, image_name)


def deploy_instance(instance_id):
    instance = Instance.objects.get(id=instance_id)
    client = get_docker_client()
    get_image(instance.image_name)
    container = start_container(
        client,
        instance.image_name,
        instance.name,
        instance.ports,
        instance.environment,
        instance.restart_policy,
    )

    instance.container_id = container.id
    instance.status = container.status
    instance.save()

    while True:
        container.reload()
        docker_status = container.status

        instance.status = DOCKER_TO_INSTANCE_STATUS.get(docker_status, "pending")
        instance.save()

        if docker_status in ["running", "exited", "dead"]:
            break

        time.sleep(2)

    container.reload()
    docker_status = container.status
    instance.status = DOCKER_TO_INSTANCE_STATUS.get(docker_status, "pending")
    instance.save()

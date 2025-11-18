import logging
import random
import time

from apps.catalog.models import Instance
from core.docker.client import (
    destroy_container,
    get_docker_client,
    pull_image,
    start_container,
    stop_container,
    unstop_container,
)

# Logging konfigurieren (kann an Django-Logging angepasst werden)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        client = get_docker_client()
        logger.info(f"Pulling image '{image_name}'")
        pull_image(client, image_name)
    except Exception as e:
        logger.exception(f"Failed to pull image '{image_name}': {e}")
        raise


def deploy_instance(instance_id):
    logger.info(f"Fetching instance with id {instance_id}")
    instance = Instance.objects.get(id=instance_id)
    try:
        logger.info("Getting Docker client...")

        client = get_docker_client()
        get_image(instance.image_name)
        logger.info(f"Starting container for instance '{instance.name}'")
        ports = {f"{instance.container_port}/tcp": instance.host_port}
        restart_policy = {"Name": instance.default_restart_policy}
        container = start_container(
            client,
            instance.image_name,
            instance.name,
            ports,
            instance.environment,
            True,
            restart_policy,
        )

    except Exception as e:
        instance.docker_output = {"error": str(e)}
        instance.save()
        instance.status = "failed"
        logger.exception(
            f"Failed to start container for instance '{instance.name}': {e}"
        )
        return

    try:
        container.reload()
        instance.container_id = container.id
        instance.status = DOCKER_TO_INSTANCE_STATUS.get(container.status, "pending")
        instance.save()
        logger.info(
            f"Container '{container.id}' started with initial status: {container.status}"
        )
    except Exception as e:
        logger.exception(
            f"Failed to save container info for instance '{instance.name}': {e}"
        )
        instance.docker_output = {"error": str(e)}
        instance.save()
        return

    exit_codes = ["running", "exited", "dead", "failed"]

    try:
        while True:
            container.reload()
            docker_status = container.status
            instance.status = DOCKER_TO_INSTANCE_STATUS.get(docker_status, "pending")
            instance.save()
            logger.info(f"[{instance.name}] Docker Status: {docker_status}")

            if docker_status in exit_codes:
                logger.info(f"Container reached terminal status: {docker_status}")
                break

            time.sleep(1)
    except Exception as e:
        logger.exception(f"Error while monitoring container '{instance.name}': {e}")
        return

    logger.info(f"Deployment of instance '{instance.name}' finished successfully.")


def pause_instance(instance_id):
    logger.info(f"Fetching instance with id {instance_id}")
    instance = Instance.objects.get(id=instance_id)
    logger.info("Getting Docker client...")
    client = get_docker_client()
    stop_container(client, instance.name)
    logger.info(f"Container '{instance.name}' paused.")
    instance.status = "paused"
    instance.save()


def unpause_instance(instance_id):
    logger.info(f"Fetching instance with id {instance_id}")
    instance = Instance.objects.get(id=instance_id)
    logger.info("Getting Docker client...")
    client = get_docker_client()
    unstop_container(client, instance.name)
    logger.info(f"Container '{instance.name}' unpaused.")
    instance.status = "running"
    instance.save()


def destroy_instance(instance_id):
    logger.info(f"Fetching instance with id {instance_id}")
    instance = Instance.objects.get(id=instance_id)
    logger.info("Getting Docker client...")
    client = get_docker_client()
    try:
        destroy_container(client, instance.name)
    except Exception as e:
        logger.exception(f"Failed to destroy container '{instance.name}': {e}")
        return
    else:
        Instance.objects.filter(id=instance_id).delete()
        logger.info(f"Container '{instance.name}' destroyed.")


def get_allocated_ports():
    client = get_docker_client()
    containers = client.containers.list()
    used_ports = set()
    for container in containers:
        container.reload()
        ports = container.attrs["NetworkSettings"]["Ports"] or {}
        for container_port, host_bindings in ports.items():
            if host_bindings:
                for binding in host_bindings:
                    host_port = binding.get("HostPort")
                    if host_port:
                        used_ports.add(int(host_port))

    return used_ports


def get_random_free_port():
    range_lower = 49152
    range_upper = 65535
    while True:
        port = random.randint(range_lower, range_upper)
        if port not in get_allocated_ports():
            return port

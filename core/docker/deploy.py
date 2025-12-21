import logging
import random
import time

from apps.catalog.models import Instance
from apps.hosts.models import DockerHost
from core.docker.client import (
    destroy_container,
    get_docker_client,
    pull_image,
    start_container,
    stop_container,
    unstop_container,
    build_labels,
)

# Logging konfigurieren (kann an Django-Logging angepasst werden)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCKER_TO_INSTANCE_STATUS = {
    "created": "pending",
    "restarting": "pending",
    "running": "running",
    "paused": "paused",
    "exited": "exited",
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


def update_instance_status(instance, container):
    """Reload container, update instance status and save."""
    container.reload()
    docker_status = container.status.lower().split()[0]
    logger.info(f"Docker Status: {docker_status}")
    instance.status = DOCKER_TO_INSTANCE_STATUS.get(docker_status, "pending")
    instance.save()
    return docker_status


def monitor_container(
    instance, container, max_checks=None, interval=10, ignore_exit_codes=False
):
    """Monitor container until it reaches a terminal status or max_checks is reached."""
    exit_codes = ["running", "exited", "dead", "failed"]
    count = 0

    while True:
        try:
            status = update_instance_status(instance, container)
        except Exception:
            logger.exception(f"Failed to update instance status")
            break

        logger.info(f"[{instance.name}] Docker Status: {status}")

        if status in exit_codes and not ignore_exit_codes:
            logger.info(f"Container reached terminal status: {status}")
            break

        count += 1
        if max_checks and count >= max_checks:
            break

        time.sleep(interval)


def deploy_instance(instance_id):
    logger.info(f"Fetching instance with id {instance_id}")
    instance = Instance.objects.get(id=instance_id)
    host = DockerHost.objects.get(active=True)

    try:
        client = get_docker_client()
        get_image(instance.image_name)

        ports = {f"{instance.container_port}/tcp": instance.host_port}
        restart_policy = {"Name": instance.default_restart_policy}
        labels = (
            build_labels(
                instance.pangolin_name,
                instance.pangolin_resource_domain,
                instance.pangolin_protocol,
                instance.pangolin_target_protocol,
                instance.pangolin_port,
            )
            if host.pangolin_features
            else None
        )
        logger.info(labels)

        container = start_container(
            client,
            instance.image_name,
            instance.name,
            ports,
            instance.environment,
            True,
            restart_policy,
            labels,
        )
        logger.info(f"Container '{instance.name}' started.")
    except Exception as e:
        logger.exception(f"Failed to start container '{instance.name}': {e}")
        instance.status = "failed"
        instance.docker_output = {"error": str(e)}
        instance.save()
        return

    monitor_container(instance, container)
    logger.info("Double checking instance status")

    monitor_container(instance, container, max_checks=10, ignore_exit_codes=True)

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


def set_pangolin_labels(instance_id, container_secured_backend):
    instance = Instance.objects.get(id=instance_id)
    host = DockerHost.objects.get(active=True)
    pangolin_name = instance.name.replace(" ", "_")
    pangolin_resource_domain = f"{instance.owner.username.replace(' ', '_')}-{instance.module.name.replace(' ', '_')}-{random.randint(1000, 9999)}.{host.default_domain}"
    pangolin_protocol = "https"
    pangolin_target_protocol = "https" if container_secured_backend else "http"
    pangolin_port = instance.host_port

    instance.pangolin_name = pangolin_name
    instance.pangolin_resource_domain = pangolin_resource_domain
    instance.pangolin_protocol = pangolin_protocol
    instance.pangolin_target_protocol = pangolin_target_protocol
    instance.pangolin_port = pangolin_port
    instance.save()

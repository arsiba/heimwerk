import logging
import random
import time

from django.db import connection, close_old_connections
from apps.deployments.models import Instance
from apps.hosts.models import DockerHost
from core.docker.client import (
    destroy_container,
    get_docker_client,
    pull_image,
    start_container,
    stop_container,
    unstop_container,
    build_labels,
    container_stats,
)

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
        logger.info(f"Pulling {image_name}...")
        pull_image(client, image_name)
        logger.info(f"Image {image_name} ready.")
    except Exception as e:
        logger.exception(f"Pull failed: {image_name} | {e}")
        raise


def update_instance_status(instance, container):
    container.reload()
    docker_status = container.status.lower().split()[0]
    instance.status = DOCKER_TO_INSTANCE_STATUS.get(docker_status, "pending")
    instance.save()
    return docker_status


def monitor_container(
    instance, container, max_checks=None, interval=10, ignore_exit_codes=False
):
    exit_codes = ["running", "exited", "dead", "failed"]
    count = 0

    while True:
        try:
            status = update_instance_status(instance, container)
            logger.info(f"[{instance.name}] Status: {status}")
        except Exception:
            logger.exception(f"[{instance.name}] Status update failed")
            break

        if status in exit_codes and not ignore_exit_codes:
            break

        count += 1
        if max_checks and count >= max_checks:
            break

        time.sleep(interval)


def deploy_instance(instance_id):
    close_old_connections()
    try:
        instance = Instance.objects.get(id=instance_id)
        host = DockerHost.objects.get(active=True)
        logger.info(f"Starting deployment: {instance.name}")

        client = get_docker_client()
        get_image(instance.image_name)

        ports = (
            {f"{instance.container_port}/tcp": instance.host_port}
            if instance.container_port
            else None
        )
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
        logger.info(f"Container started: {instance.name}")

        monitor_container(instance, container)
        monitor_container(instance, container, max_checks=10, ignore_exit_codes=True)
        logger.info(f"Deployment successful: {instance.name}")

    except Exception as e:
        logger.exception(f"Deployment failed for ID {instance_id}")
        close_old_connections()
        instance = Instance.objects.get(id=instance_id)
        instance.status = "failed"
        instance.docker_output = {"error": str(e)}
        instance.save()
    finally:
        close_old_connections()


def pause_instance(instance_id):
    instance = Instance.objects.get(id=instance_id)
    client = get_docker_client()
    stop_container(client, instance.name)
    instance.status = "paused"
    instance.save()
    logger.info(f"Paused: {instance.name}")


def unpause_instance(instance_id):
    instance = Instance.objects.get(id=instance_id)
    client = get_docker_client()
    unstop_container(client, instance.name)
    instance.status = "running"
    instance.save()
    logger.info(f"Unpaused: {instance.name}")


def destroy_instance(instance_id):
    instance = Instance.objects.get(id=instance_id)
    client = get_docker_client()
    try:
        destroy_container(client, instance.name)
        Instance.objects.filter(id=instance_id).delete()
        logger.info(f"Destroyed: {instance.name}")
    except Exception:
        logger.exception(f"Destroy failed: {instance.name}")


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
    rand_id = random.randint(1000, 9999)
    domain = f"{instance.owner.username}-{instance.module.name}-{rand_id}.{host.default_domain}".replace(
        " ", "_"
    )

    instance.pangolin_name = pangolin_name
    instance.pangolin_resource_domain = domain
    instance.pangolin_protocol = "http"
    instance.pangolin_target_protocol = "https" if container_secured_backend else "http"
    instance.pangolin_port = instance.host_port
    instance.save()


def get_instance_stats(instance_id):
    instance = Instance.objects.get(id=instance_id)
    client = get_docker_client()
    return container_stats(client, instance.name)

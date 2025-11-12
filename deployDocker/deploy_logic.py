import logging
import time

from dulwich.porcelain import remove

from deployDocker.docker_tools import get_docker_client, pull_image, start_container
from serviceCatalog.models import Instance

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
    try:
        logger.info(f"Fetching instance with id {instance_id}")
        instance = Instance.objects.get(id=instance_id)
    except Instance.DoesNotExist:
        logger.error(f"Instance with id {instance_id} does not exist.")
        return
    except Exception as e:
        logger.exception(f"Error fetching instance {instance_id}: {e}")
        return

    try:
        logger.info("Getting Docker client...")
        client = get_docker_client()
    except Exception as e:
        logger.exception(f"Failed to get Docker client: {e}")
        return

    try:
        get_image(instance.image_name)
    except Exception as e:
        logger.exception(
            f"Failed to ensure image '{instance.image_name}' is available: {e}"
        )
        return

    try:
        logger.info(f"Starting container for instance '{instance.name}'")
        container = start_container(
            client,
            instance.image_name,
            instance.name,
            instance.ports,
            instance.environment,
            True,
            instance.restart_policy,
        )
    except Exception as e:
        logger.exception(
            f"Failed to start container for instance '{instance.name}': {e}"
        )
        return

    # Container-ID speichern
    try:
        container.reload()  # sicherstellen, dass status geladen ist
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

    exit_codes = ["running", "exited", "dead"]
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

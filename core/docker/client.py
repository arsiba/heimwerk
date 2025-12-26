import docker
from docker import DockerClient
from docker.models.containers import Container

_client = None


def init_docker(host_url: str = "tcp://127.0.0.1:2375", local: bool = False):
    """
    Initialize and return a Docker client connected to a specified Docker host.

    This function creates a Docker client using the provided IP address and port,
    allowing Python code to interact with the Docker daemon over TCP.

    Parameters:
    -----------
    docker_ip : str, optional
        The IP address of the Docker host. Default is "127.0.0.1".
    docker_port : int, optional
        The port number on which the Docker daemon is listening. Default is 2375.

    Returns:
    --------
    docker.DockerClient
        An instance of DockerClient connected to the specified Docker host.
    """
    global _client
    if _client is None:
        if local:
            base_url = "unix://var/run/docker.sock"
            _client = docker.DockerClient(base_url=base_url)
        else:
            _client = docker.DockerClient(base_url=host_url)
    return _client


def test_client_config(host_url: str = "tcp://127.0.0.1:2375"):
    try:
        test_client = docker.DockerClient(base_url=host_url)
        test_client.ping()
        test_client.close()
        return True
    except Exception:
        return False


def test_connection():
    try:
        result = get_docker_client().ping()
        return result == "OK"
    except Exception:
        return False


def get_docker_client():
    global _client
    if _client is None:
        _client = init_docker()
    return _client


def pull_image(client: DockerClient, image_name: str):
    """Pull an image from Docker Hub."""
    client.images.pull(image_name)


def build_labels(
    pangolin_name: str,
    pangolin_resource_domain: str,
    pangolin_protocol: str,
    pangolin_target_protocol: str,
    pangolin_port: int,
) -> dict[str, str]:

    resource_key = pangolin_name

    return {
        f"pangolin.public-resources.{resource_key}.name": pangolin_name,
        f"pangolin.public-resources.{resource_key}.protocol": pangolin_protocol,
        f"pangolin.public-resources.{resource_key}.full-domain": pangolin_resource_domain,
        f"pangolin.public-resources.{resource_key}.targets[0].method": pangolin_target_protocol,
        f"pangolin.public-resources.{resource_key}.targets[0].port": str(pangolin_port),
    }


def start_container(
    client: DockerClient,
    image_name: str,
    container_name: str,
    ports: dict[str, int] | None = None,
    environment: dict[str, str] | None = None,
    detach: bool = True,
    restart_policy: dict | None = None,
    labels: dict[str, str] | None = None,
) -> Container:
    """
    Start a Docker container.

    Parameters:
        client: DockerClient instance
        image_name: Name of the Docker image
        container_name: Desired container name
        ports: Port mappings (container_port: host_port)
        environment: Environment variables
        detach: Run container in background
        restart_policy: Restart policy dict, e.g. {"Name": "always"}

    Returns:
        Container instance
    """
    container = client.containers.run(
        image=image_name,
        name=container_name,
        ports=ports,
        environment=environment,
        detach=detach,
        restart_policy=restart_policy,
        labels=labels,
    )
    return container


def stop_container(client: DockerClient, container_name: str):
    client.containers.get(container_name).stop()


def unstop_container(client: DockerClient, container_name: str):
    client.containers.get(container_name).start()


def destroy_container(client: DockerClient, container_name: str):
    client.containers.get(container_name).remove(force=True)


def container_stats(client: DockerClient, container_name: str):
    return client.api.stats(container_name, decode=True, stream=False)


def container_logs(client: DockerClient, container_name: str):
    return client.api.logs(container_name, stdout=True, stderr=True, stream=False)

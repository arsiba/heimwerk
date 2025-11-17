import docker
from docker import DockerClient

_client = None


def init_docker(
    docker_ip: str = "127.0.0.1", docker_port: int = 2375, local: bool = False
):
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
            base_url = f"tcp://{docker_ip}:{docker_port}"
            _client = docker.DockerClient(base_url=base_url)
    return _client


def get_docker_client():
    global _client
    if _client is None:
        _client = init_docker()
    return _client


def pull_image(client: DockerClient, image_name: str):
    """Pull an image from Docker Hub."""
    client.images.pull(image_name)


# falls du es importierst
from docker.models.containers import Container


def start_container(
    client: DockerClient,
    image_name: str,
    container_name: str,
    ports: dict[str, int] | None = None,
    environment: dict[str, str] | None = None,
    detach: bool = True,
    restart_policy: dict | None = None,
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
    )
    return container


def stop_container(client: DockerClient, container_name: str):
    client.containers.get(container_name).stop()


def destroy_container(client: DockerClient, container_name: str):
    client.containers.get(container_name).remove(force=True)


def container_stats(client: DockerClient, container_name: str):
    return client.api.stats(container_name, decode=True, stream=False)

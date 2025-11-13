[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-highlight.svg)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)

# Heimwerk

[![Under Development](https://img.shields.io/badge/status-under%20development-orange)](docs/TODO.md)
[![TODOs](https://img.shields.io/badge/TODO-docs%2FTODO.md-lightgrey)](docs/TODO.md)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)

**Heimwerk** is a Platform for deploying Docker containers. Users can select from a catalog of prebuilt modules, view them, and deploy them with a single click. The system simplifies service deployment in a homelab and enables standardized deployments.

The recommended use case is in combination with **Pangolin**, to automatically make deployed services accessible to the user, including subdomain, network rules, and access control.

## Features

* Catalog management for modules
* Display modules with description and metadata
* Self-service deployment with one click
* Recommended integration with Pangolin for automatic deployment and network configuration
* Easily extendable with new modules

## Target Audience

* Homelab users who want to deploy services quickly and easily
* Users who want to test self-service deployments with standardized modules

## Development TODOs

The current development tasks are documented in [`docs/TODO.md`](docs/TODO.md).  

Excerpt:

* **Deployment Views** – Add views for managing `Instance` deployments with proper permission checks  
* **Deployment Forms** – Build forms to deploy instances based on modules (machine/host selection, domain/subdomain)  
* **Backend** – Implement basic deploy functionality, capture outputs and status, support destroying instances  
* **Settings & Secure Storage** – Store hosts, credentials, configs, and state securely  
* **Tests** – Unit and integration tests for views, forms, backend, and settings

[See full TODO list](docs/TODO.md) for details.

## Code Formatting

* To indent and beautify HTML templates:
```bash
djhtml template.html
```

## Development

To run **Heimwerk** locally, you need a development Docker server with its API exposed over TCP. Follow these steps:

### 1. Stop the running Docker service
Before exposing the Docker API, stop the default Docker daemon:
```bash
sudo systemctl stop docker
````

### 2. Start Docker with TCP API enabled

Start the Docker daemon manually, exposing both the TCP port (for Heimwerk) and the default Unix socket:

```bash
sudo dockerd -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock
```

* `tcp://0.0.0.0:2375` — allows connections over TCP on all interfaces.
* `unix:///var/run/docker.sock` — keeps local Docker CLI commands functional.

### 3. Verify Docker TCP access

You can test the TCP API with:

```bash
curl http://localhost:2375/version
```

You should see JSON output containing Docker version information.

### Security Notice

Exposing Docker over TCP **without TLS** is insecure and allows full control of your system. For local development, it's recommended to either:

* Restrict the TCP endpoint to `127.0.0.1`:

```bash
sudo dockerd -H tcp://127.0.0.1:2375 -H unix:///var/run/docker.sock
```

* Or configure TLS for remote access in production environments.

### 4. Restart Docker after development

When finished, restart the standard Docker service:

```bash
sudo systemctl start docker
```

This setup allows Heimwerk to communicate with Docker for deploying and managing containers in your local dev environment.



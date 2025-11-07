[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-highlight.svg)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
# Heimwerk

[![Under Development](https://img.shields.io/badge/status-under%20development-orange)](docs/TODO.md)
[![TODOs](https://img.shields.io/badge/TODO-docs%2FTODO.md-lightgrey)](docs/TODO.md)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)

**Heimwerk** is a self-service catalog for Terraform modules. Users can select from a catalog of prebuilt modules, view them, and deploy them with a single click. The system simplifies service deployment in a homelab and enables standardized deployments.

The recommended use case is in combination with **Pangolin**, to automatically make deployed services accessible to the user, including subdomain, network rules, and access control.

## Features

* Catalog management for Terraform modules
* Display modules with description and metadata
* Self-service deployment with one click
* Recommended integration with Pangolin for automatic deployment and network configuration
* Easily extendable with new Terraform modules

## Target Audience

* Homelab users who want to deploy services quickly and easily
* Users who want to test self-service deployments with standardized Terraform modules


## Development TODOs

The current development tasks are documented in [`docs/TODO.md`](docs/TODO.md).  

Excerpt:

* **Deployment Views** – Add views for managing `Instance` deployments with proper permission checks.  
* **Deployment Forms** – Build forms to deploy instances based on Terraform modules (machine/host selection, domain/subdomain).  
* **Terraform Backend** – Implement basic deploy functionality, capture outputs and status, support destroying instances.  
* **Settings & Secure Storage** – Store hosts, credentials, configs, and state securely.  
* **Tests** – Unit and integration tests for views, forms, backend, and settings.

[See full TODO list](docs/TODO.md) for details.

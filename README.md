[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-highlight.svg)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
---
# Heimwerk
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)

**Heimwerk** ist ein Self-Service-Katalog für Terraform-Module. Nutzer können aus einem Katalog vorgefertigter Module wählen, diese anzeigen und auf Klick deployen. Das System dient dazu, die Bereitstellung von Diensten im Homelab zu vereinfachen und standardisierte Deployments zu ermöglichen.

Der empfohlene Use Case ist die Kombination mit **Pangolin**, um die bereitgestellten Dienste automatisch für den Nutzer zugänglich zu machen, inklusive Subdomain, Netzwerkregeln und Zugriffsschutz.


## Funktionen

* Katalogverwaltung für Terraform-Module
* Anzeigen von Modulen mit Beschreibung und Metadaten
* Self-Service Deployment auf Klick
* Integrationsempfehlung mit Pangolin zur automatischen Bereitstellung und Netzwerkverwaltung
* Einfach erweiterbar durch neue Terraform-Module


## Zielgruppe

* Homelab-Nutzer, die Dienste schnell und einfach bereitstellen wollen
* Nutzer, die Self-Service Deployments mit standardisierten Terraform-Modulen testen möchten

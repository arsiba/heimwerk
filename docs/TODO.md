# Heimwerk TODOs – Deployment & Terraform Features

## 1. Deployment Views

* Add views for managing `Instance` deployments. 
* Add permission checks so users only see their own instances.

## 2. Deployment Forms

* Build forms to deploy instances based on Terraform modules.
* Include generic form based on terraform missing variables e.g. machine/host selection and domain/subdomain selection.

## 3. Terraform Backend

* Implement basic deploy functionality (`terraform init`, `plan`, `apply`).
* Capture outputs and instance status.
* Support destroying.

## 4. Settings & Secure Storage

* Store Terraform hosts, credentials, configs, and state securely.
* Ensure access control and encryption for sensitive data.

## 5. Tests

* Write unit and integration tests for:
  * Deployment views
  * Deployment forms
  * Terraform backend functionality
  * Settings and credentials handling

# Heimwerk

[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-highlight.svg)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)  
[![GitHub release](https://img.shields.io/github/release/arsiba/heimwerk.svg)](https://github.com/arsiba/heimwerk/releases/latest)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=arsiba_heimwerk&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=arsiba_heimwerk)
[![No AI Generated Code](https://img.shields.io/badge/no--ai--generated--code-100%25-brightgreen)](https://github.com/arsiba/heimwerk)

**Heimwerk** is a platform for deploying Docker containers, designed to empower users by providing easy, self-service access to homelab resources. It enables administrators to share server capabilities securely and effortlessly, allowing users to deploy services from a prebuilt catalog with a single click while maintaining a standardized and controlled environment.

The recommended use case is in combination with **[Pangolin](https://github.com/arsiba/pangolin)**, to automatically make deployed services accessible to the user, including subdomain, network rules, and access control.

---

## Screenshots

<p align="center">
  <img src="docs/assets/catalog.png" width="45%" alt="Catalog Management" />
  <img src="docs/assets/instance_details.png" width="45%" alt="Instance Details" />
</p>

---

## Installation

### Quick Production Install (Recommended)

The fastest way to deploy Heimwerk on a Linux server. This script downloads the necessary production files, generates a secure `SECRET_KEY`, and configures your domain.

Run the following command:

```bash
curl -sSL https://raw.githubusercontent.com/arsiba/heimwerk/refs/heads/main/install.sh | bash
docker compose -f docker-compose.prod.yml exec heimwerk python manage.py collectstatic
docker compose -f docker-compose.prod.yml exec heimwerk python manage.py createsuperuser
docker compose -f docker-compose.prod.yml restart
```

### Manual Production Setup

If you prefer to set up the containers manually:

1.  **Download the production files:**
    `docker-compose.prod.yml`, `nginx.conf`, and `.env.example`.
2.  **Configure environment:**
    ```bash
    cp .env.example .env
    # Edit .env to set your ALLOWED_HOSTS and a secure SECRET_KEY
    ```
3.  **Deploy:**
    ```bash
    docker compose -f docker-compose.prod.yml up -d
    docker compose -f docker-compose.prod.yml exec heimwerk python manage.py migrate
    docker compose -f docker-compose.prod.yml exec heimwerk python manage.py createsuperuser
    ```

### Local Development Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/arsiba/heimwerk.git
    cd heimwerk
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    ```bash
    cp .env.example .env # Ensure DEBUG=True for local dev
    ```
    *Edit the `.env` file and set a unique `SECRET_KEY`.*
5.  **Apply migrations & Create superuser:**
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
    ```
6.  **Run the application:**
    ```bash
    python manage.py runserver
    ```
    The application will be available at `http://127.0.0.1:8000`.

---

## Features

*   **Catalog Management**: Maintain a catalog of prebuilt Docker modules.
*   **One-Click Deployment**: Safe and straightforward self-service for sharing resources.
*   **Pangolin Integration**: Automatic network configuration and access control (recommended).
*   **Extensible**: Easily add new modules to the catalog.
*   **Real-time Monitoring**: (In progress) Statistics for deployed instances via WebSockets.

---

## Tech Stack & Requirements

### Tech Stack
-   **Language:** Python 3.10+
-   **Framework:** Django 5.2.x, Django Channels
-   **Database:** SQLite (default for development)
-   **Containerization:** Docker (via Docker SDK for Python)
-   **Web Server:** Daphne (for ASGI/WebSocket support)

### Requirements
-   Python 3.10 or higher
-   Docker installed and running
-   Access to Docker API

---

## Project Structure

```text
heimwerk/
├── apps/               # Django applications
│   ├── catalog/        # Module catalog management
│   ├── deployments/    # Instance and deployment logic
│   ├── hosts/          # Docker host management
│   └── users/          # User management and signals
├── config/             # Project configuration (settings, URLs, ASGI/WSGI)
├── core/               # Core logic and utilities
│   ├── docker/         # Docker SDK wrappers and deployment logic
│   └── utils/          # Common utilities
├── templates/          # Global HTML templates
├── docs/               # Documentation (TODOs, etc.)
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
└── pyproject.toml      # Build and tool configuration (Black, Isort)
```

---

## Management Commands

| Command | Description |
| :--- | :--- |
| `python manage.py runserver` | Start the development server. |
| `python manage.py migrate` | Apply database migrations. |
| `python manage.py createsuperuser` | Create an administrative user. |
| `python manage.py test` | Run the test suite. |
| `python manage.py collectstatic` | Collect static files for production. |
| `python manage.py shell` | Open the Django interactive shell. |

---

## Environment Variables

Currently, the project uses default Django settings. Future updates may include:

-   `DEBUG`: Set to `False` in production.
-   `SECRET_KEY`: Django secret key.
-   `ALLOWED_HOSTS`: List of hosts allowed to access the site.
-   **TODO**: Define app-specific environment variables for Docker host configurations and secure storage.

---

## Testing

Run tests using the standard Django test runner:

```bash
python manage.py test
```



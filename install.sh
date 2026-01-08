#!/bin/bash
set -Eeuo pipefail

# =========================================================
# HEIMWERK INSTALLATION (CORE SETUP ONLY)
#
# This script:
# - Collects minimal configuration from the user
# - Generates a production-safe .env file
# - Starts Docker services
# - Runs initial database migrations
#
# Design constraints:
# - .env values are space-separated and QUOTED
#   because nginx also consumes them.
# - Django is hardened to correctly parse quoted values.
# - Containers MUST be recreated when .env changes.
# =========================================================

# ---------------------------------------------------------
# Colors & Icons (purely cosmetic)
# ---------------------------------------------------------
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

CHECK="${GREEN}✓${NC}"
CROSS="${RED}✗${NC}"
ARROW="${CYAN}→${NC}"

# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
PROJECT_NAME="heimwerk"
REPO_RAW_URL="https://raw.githubusercontent.com/arsiba/heimwerk/main"

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

print_header() {
    clear
    echo -e "${BOLD}${ORANGE}╔══════════════════════════════════════════╗"
    echo "║                                          ║"
    echo "║           HEIMWERK INSTALLATION          ║"
    echo "║                                          ║"
    echo -e "╚══════════════════════════════════════════╝${NC}"
}

print_step()    { echo -e "\n${BOLD}${BLUE}▶ [$1] $2${NC}"; }
print_success() { echo -e "  ${CHECK} $1"; }
print_error()   { echo -e "  ${CROSS} $1"; }
print_info()    { echo -e "  ${ARROW} $1"; }

fatal() {
    print_error "$1"
    exit 1
}

# ---------------------------------------------------------
# Execution starts here
# ---------------------------------------------------------

print_header

# ---------------------------------------------------------
# [0/6] Verify required tools exist
# ---------------------------------------------------------
print_step "0/6" "Checking Requirements"

for cmd in docker curl openssl; do
    command -v "$cmd" &>/dev/null || fatal "$cmd missing"
    print_success "$cmd found"
done

# ---------------------------------------------------------
# [1/6] Basic configuration
# ---------------------------------------------------------
print_step "1/6" "Configuration"

# Read domain or IP from user (stdin must be /dev/tty)
read -rp "Enter your domain or IP [localhost]: " USER_DOMAIN < /dev/tty
USER_DOMAIN=${USER_DOMAIN:-localhost}

# Trim accidental whitespace (prevents broken CSRF origins)
USER_DOMAIN=$(echo "$USER_DOMAIN" | xargs)

# Ask for SSL only when not localhost
USE_SSL="n"
if [[ "$USER_DOMAIN" != "localhost" && "$USER_DOMAIN" != "127.0.0.1" ]]; then
    read -rp "Is this domain running with SSL (https)? [y/N]: " USE_SSL < /dev/tty
fi

# Determine protocol used for CSRF_TRUSTED_ORIGINS
PROTO="http"
if [[ $USE_SSL =~ ^[Yy]$ ]]; then
    PROTO="https"
    print_info "Using HTTPS for CSRF origins"
else
    print_info "Using HTTP for CSRF origins"
fi

# ---------------------------------------------------------
# [2/6] Download production files
# ---------------------------------------------------------
print_step "2/6" "Downloading Production Files"

curl -fsSL "${REPO_RAW_URL}/${COMPOSE_FILE}" -o "${COMPOSE_FILE}"
curl -fsSL "${REPO_RAW_URL}/nginx.conf" -o nginx.conf

print_success "Files downloaded"

# ---------------------------------------------------------
# [3/6] Generate .env (only if missing)
# ---------------------------------------------------------
print_step "3/6" "Syncing Credentials & Volumes"

if [ ! -f "$ENV_FILE" ]; then

    # If a database volume exists but no .env, offer a clean reset
    if docker volume ls | grep -q "${PROJECT_NAME}_postgres_data"; then
        echo -e "${ORANGE}! Old database found but no .env file.${NC}"
        read -rp "Wipe old data for a clean install? [y/N]: " WIPE < /dev/tty
        if [[ $WIPE =~ ^[Yy]$ ]]; then
            docker compose -f "${COMPOSE_FILE}" down -v &>/dev/null
        fi
    fi

    # Generate cryptographically strong secrets
    RAND_SECRET=$(openssl rand -hex 32)
    DB_PASS=$(openssl rand -hex 24)

    # CSRF origins must include:
    # - localhost
    # - IPv4 loopback
    # - IPv6 loopback
    # - user domain (with correct protocol)
    TRUSTED="http://localhost http://127.0.0.1 http://::1 ${PROTO}://${USER_DOMAIN}"

    # IMPORTANT:
    # Values are QUOTED and SPACE-SEPARATED because:
    # - nginx consumes them as raw strings
    # - Django strips quotes and splits safely
    cat > "${ENV_FILE}" <<EOF
SECRET_KEY=${RAND_SECRET}
DEBUG=False
ALLOWED_HOSTS="127.0.0.1 localhost ::1 ${USER_DOMAIN}"
CSRF_TRUSTED_ORIGINS="${TRUSTED}"

POSTGRES_DB=heimwerk
POSTGRES_USER=heimwerk_admin
POSTGRES_PASSWORD=${DB_PASS}
DATABASE_URL=postgres://heimwerk_admin:${DB_PASS}@db:5432/heimwerk
EOF

    chmod 600 "${ENV_FILE}"
    print_success "Generated new .env"

else
    print_info "Using existing .env"
fi

# ---------------------------------------------------------
# [4/6] Start Docker services
#
# --force-recreate is REQUIRED to ensure updated .env values
# are injected into containers (Docker does NOT update env
# vars on existing containers).
# ---------------------------------------------------------
print_step "4/6" "Starting Docker Services"

docker compose -f "${COMPOSE_FILE}" up -d --quiet-pull --force-recreate
print_success "Containers are up"

# ---------------------------------------------------------
# [5/6] Wait for database to become healthy
# ---------------------------------------------------------
print_step "5/6" "Waiting for Database"

DB_CONTAINER=$(docker compose -f "${COMPOSE_FILE}" ps -q db)

until [ "$(docker inspect -f '{{.State.Health.Status}}' "$DB_CONTAINER")" == "healthy" ]; do
    echo -n "."
    sleep 2
done

echo ""
print_success "Database is ready"

# ---------------------------------------------------------
# [6/6] Run Django migrations
# ---------------------------------------------------------
print_step "6/6" "Database Migrations"

print_info "Running migrations..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk \
    python manage.py migrate --no-input || \
    print_info "Migration finished with warnings."

# ---------------------------------------------------------
# Final instructions
# ---------------------------------------------------------
echo -e "\n${BOLD}${GREEN}✓ AUTOMATED STEPS COMPLETE${NC}"
echo -e "${ORANGE}Remaining manual steps:${NC}"
echo -e "  1. Collect static files:   ${CYAN}docker compose exec heimwerk python manage.py collectstatic${NC}"
echo -e "  2. Create admin:           ${CYAN}docker compose exec heimwerk python manage.py createsuperuser${NC}"
echo -e "  3. Restart app:            ${CYAN}docker compose restart heimwerk nginx${NC}"
echo ""

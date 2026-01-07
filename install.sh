#!/bin/bash
set -Eeuo pipefail

# =========================================================
# HEIMWERK INSTALLATION (ROBUST PRODUCTION VERSION)
# =========================================================

# Colors & Icons
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

# Constants
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
PROJECT_NAME="heimwerk"
REPO_RAW_URL="https://raw.githubusercontent.com/arsiba/heimwerk/main"

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

print_header() {
    clear
    echo -e "${BOLD}${ORANGE}╔══════════════════════════════════════════╗"
    echo "║                                          ║"
    echo "║           HEIMWERK INSTALLATION          ║"
    echo "║                                          ║"
    echo -e "╚══════════════════════════════════════════╝${NC}"
}

print_step() { echo -e "\n${BOLD}${BLUE}▶ [$1] $2${NC}"; }
print_success() { echo -e "  ${CHECK} $1"; }
print_error()   { echo -e "  ${CROSS} $1"; }
print_info()    { echo -e "  ${ARROW} $1"; }

fatal() {
    print_error "$1"
    exit 1
}

# ---------------------------------------------------------
# Execution
# ---------------------------------------------------------

print_header

# [0/7] Requirements
print_step "0/7" "Checking Requirements"
for cmd in docker curl openssl; do
    command -v "$cmd" &>/dev/null || fatal "$cmd missing"
    print_success "$cmd found"
done

# [1/7] Configuration
print_step "1/7" "Configuration"
read -rp "Enter your domain or IP [localhost]: " USER_DOMAIN < /dev/tty
USER_DOMAIN=${USER_DOMAIN:-localhost}

# [2/7] Download
print_step "2/7" "Downloading Production Files"
curl -fsSL "${REPO_RAW_URL}/${COMPOSE_FILE}" -o "${COMPOSE_FILE}"
curl -fsSL "${REPO_RAW_URL}/nginx.conf" -o nginx.conf
print_success "Files downloaded"

# [3/7] Sync Credentials & Volumes
print_step "3/7" "Syncing Credentials & Volumes"
if [ ! -f "$ENV_FILE" ]; then
    if docker volume ls | grep -q "${PROJECT_NAME}_postgres_data"; then
        echo -e "${ORANGE}! Old database found but no .env file.${NC}"
        read -rp "Wipe old data for a clean install? [y/N]: " WIPE < /dev/tty
        if [[ $WIPE =~ ^[Yy]$ ]]; then
            docker compose -f "${COMPOSE_FILE}" down -v &>/dev/null
        fi
    fi
    RAND_SECRET=$(openssl rand -hex 32)
    DB_PASS=$(openssl rand -hex 24)
    cat > "${ENV_FILE}" <<EOF
SECRET_KEY=${RAND_SECRET}
DEBUG=False
ALLOWED_HOSTS="127.0.0.1 localhost ::1 ${USER_DOMAIN}"
POSTGRES_DB=heimwerk
POSTGRES_USER=heimwerk_admin
POSTGRES_PASSWORD=${DB_PASS}
DATABASE_URL=postgres://heimwerk_admin:${DB_PASS}@db:5432/heimwerk
EOF
    print_success "Generated new .env"
else
    print_info "Using existing .env"
fi

# [4/7] Start Services
print_step "4/7" "Starting Docker Services"
docker compose -f "${COMPOSE_FILE}" up -d --quiet-pull
print_success "Containers are up"

# [5/7] Healthcheck
print_step "5/7" "Waiting for Database"
until [ "$(docker inspect -f '{{.State.Health.Status}}' $(docker compose -f ${COMPOSE_FILE} ps -q db))" == "healthy" ]; do
    echo -n "."
    sleep 2
done
echo ""
print_success "Database is ready"

# [6/7] Backend Initialization
print_step "6/7" "Backend Initialization"
print_info "Running migrations..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py migrate --no-input

print_info "Collecting static files..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py collectstatic --no-input --clear

# IMPORTANT: Restart the app to load the new static manifest
print_info "Refreshing application state..."
docker compose -f "${COMPOSE_FILE}" restart heimwerk
print_success "Backend is fully synced"

# [7/7] Admin
print_step "7/7" "Creating Admin User"
# We check if we are in an interactive terminal to allow superuser creation
if [ -t 0 ]; then
    docker compose -f "${COMPOSE_FILE}" exec heimwerk python manage.py createsuperuser || print_info "Superuser creation skipped."
fi

print_info "Restarting Nginx..."
docker compose -f "${COMPOSE_FILE}" restart nginx

echo -e "\n${BOLD}${GREEN}✓ INSTALLATION COMPLETE${NC}"
echo -e "Access: http://${USER_DOMAIN}"
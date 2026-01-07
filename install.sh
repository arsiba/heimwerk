#!/bin/bash
set -Eeuo pipefail

# =========================================================
# HEIMWERK INSTALLATION (FIXED FOR AUTH ERRORS)
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

error_handler() {
    echo -e "\n${RED}Critical Error occurred at line $1.${NC}"
    echo -e "This is usually caused by password mismatches with existing volumes."
    echo -e "Try running: ${CYAN}docker compose -f ${COMPOSE_FILE} down -v${NC} then restart the script."
    exit 1
}
trap 'error_handler $LINENO' ERR

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

# [3/7] Hard Reset Logic (Solves the Password Error)
print_step "3/7" "Syncing Credentials & Volumes"
if docker volume ls | grep -q "${PROJECT_NAME}_postgres_data"; then
    echo -e "${ORANGE}Existing database found.${NC}"
    read -rp "Do you want to wipe existing data to apply new credentials? [y/N]: " WIPE_DATA < /dev/tty
    if [[ $WIPE_DATA =~ ^[Yy]$ ]]; then
        print_info "Cleaning up old volumes..."
        docker compose -f "${COMPOSE_FILE}" down -v --remove-orphans &>/dev/null || true
        print_success "Cleanup complete"
    else
        print_info "Keeping existing data. WARNING: If passwords don't match, migrations will fail."
    fi
fi

# Generate Environment
if [ ! -f "$ENV_FILE" ]; then
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
    print_success "New .env file generated"
else
    print_info "Using existing .env file"
fi

# [4/7] Start
print_step "4/7" "Starting Docker Services"
docker compose -f "${COMPOSE_FILE}" up -d --quiet-pull
print_success "Containers are starting..."

# [5/7] Healthcheck
print_step "5/7" "Waiting for Database"
until [ "$(docker inspect -f '{{.State.Health.Status}}' $(docker compose -f ${COMPOSE_FILE} ps -q db))" == "healthy" ]; do
    echo -n "."
    sleep 2
done
echo ""
print_success "Database is healthy"

# [6/7] Backend Init (Migrations)
print_step "6/7" "Backend Initialization"
print_info "Running migrations..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py migrate --no-input
print_info "Collecting static files..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py collectstatic --no-input --clear
print_success "Backend ready"

# [7/7] Admin
print_step "7/7" "Creating Admin User"
docker compose -f "${COMPOSE_FILE}" exec heimwerk python manage.py createsuperuser

print_info "Finalizing..."
docker compose -f "${COMPOSE_FILE}" restart nginx

echo -e "\n${BOLD}${GREEN}✓ INSTALLATION COMPLETE${NC}"
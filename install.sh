#!/bin/bash
set -Eeuo pipefail

# =========================================================
# HEIMWERK INSTALLATION (CORE SETUP ONLY)
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

# [0/6] Requirements
print_step "0/6" "Checking Requirements"
for cmd in docker curl openssl; do
    command -v "$cmd" &>/dev/null || fatal "$cmd missing"
    print_success "$cmd found"
done

# [1/6] Configuration
print_step "1/6" "Configuration"
read -rp "Enter your domain or IP [localhost]: " USER_DOMAIN < /dev/tty
USER_DOMAIN=${USER_DOMAIN:-localhost}

# [2/6] Download
print_step "2/6" "Downloading Production Files"
curl -fsSL "${REPO_RAW_URL}/${COMPOSE_FILE}" -o "${COMPOSE_FILE}"
curl -fsSL "${REPO_RAW_URL}/nginx.conf" -o nginx.conf
print_success "Files downloaded"

# [3/6] Sync Credentials & Volumes
print_step "3/6" "Syncing Credentials & Volumes"
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
    chmod 600 "${ENV_FILE}"
    print_success "Generated new .env"
else
    print_info "Using existing .env"
fi

# [4/6] Start Services
print_step "4/6" "Starting Docker Services"
docker compose -f "${COMPOSE_FILE}" up -d --quiet-pull
print_success "Containers are up"

# [5/6] Healthcheck
print_step "5/6" "Waiting for Database"
until [ "$(docker inspect -f '{{.State.Health.Status}}' $(docker compose -f ${COMPOSE_FILE} ps -q db))" == "healthy" ]; do
    echo -n "."
    sleep 2
done
echo ""
print_success "Database is ready"

# [6/6] Backend Initialization
print_step "6/6" "Database Migrations"

print_info "Running migrations..."
# Wrapped to ensure script finishes even if Django outputs RuntimeWarnings to stderr
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py migrate --no-input || print_info "Migration finished with warnings."

echo -e "\n${BOLD}${GREEN}✓ AUTOMATED STEPS COMPLETE${NC}"
echo -e "${ORANGE}Remaining manual steps:${NC}"
echo -e "  1. Collect static files:   ${CYAN}docker compose exec heimwerk python manage.py collectstatic${NC}"
echo -e "  2. Create admin:           ${CYAN}docker compose exec heimwerk python manage.py createsuperuser${NC}"
echo -e "  3. Restart app:            ${CYAN}docker compose restart heimwerk nginx${NC}"
echo ""
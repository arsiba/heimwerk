#!/bin/bash
set -Eeuo pipefail

# =========================================================
# HEIMWERK INSTALLATION
# =========================================================

# Colors
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Icons
CHECK="${GREEN}✓${NC}"
CROSS="${RED}✗${NC}"
ARROW="${CYAN}→${NC}"

# Constants
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
PROJECT_NAME="heimwerk"
DB_VOLUME="${PROJECT_NAME}_postgres_data"
REPO_RAW_URL="https://raw.githubusercontent.com/arsiba/heimwerk/main"

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

print_header() {
    clear
    echo -e "${BOLD}${ORANGE}"
    echo "╔══════════════════════════════════════════╗"
    echo "║                                          ║"
    echo "║           HEIMWERK INSTALLATION          ║"
    echo "║                                          ║"
    echo "╚══════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BOLD}${BLUE}▶ [$1] $2${NC}"
}

print_success() { echo -e "  ${CHECK} $1"; }
print_error()   { echo -e "  ${CROSS} $1"; }
print_info()    { echo -e "  ${ARROW} $1"; }

fatal() {
    print_error "$1"
    exit 1
}

# Trap to catch errors and provide context
error_handler() {
    echo -e "\n${RED}Critical Error occurred at line $1.${NC}"
    echo -e "Check logs: ${CYAN}docker compose -f ${COMPOSE_FILE} logs --tail=20${NC}"
    exit 1
}
trap 'error_handler $LINENO' ERR

# ---------------------------------------------------------
# 0/7 Requirements
# ---------------------------------------------------------

print_header
print_step "0/7" "Checking Requirements"

for cmd in docker curl openssl; do
    command -v "$cmd" &>/dev/null || fatal "$cmd is not installed."
    print_success "$cmd found"
done

docker compose version &>/dev/null || fatal "Docker Compose V2 is required."
print_success "Docker Compose found"

# ---------------------------------------------------------
# 1/7 Configuration
# ---------------------------------------------------------

print_step "1/7" "Configuration"

read -rp "Enter your domain or IP [localhost]: " USER_DOMAIN < /dev/tty
USER_DOMAIN=${USER_DOMAIN:-localhost}
print_info "Domain set to: $USER_DOMAIN"

# ---------------------------------------------------------
# 2/7 Download
# ---------------------------------------------------------

print_step "2/7" "Downloading Production Files"
curl -fsSL "${REPO_RAW_URL}/${COMPOSE_FILE}" -o "${COMPOSE_FILE}"
curl -fsSL "${REPO_RAW_URL}/nginx.conf" -o nginx.conf
print_success "Files downloaded"

# ---------------------------------------------------------
# 3/7 Environment (Auto-Generation)
# ---------------------------------------------------------

print_step "3/7" "Setting Up Environment"

if [ -f "$ENV_FILE" ]; then
    print_info ".env already exists. Skipping generation."
else
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
    print_success ".env file generated with secure secrets"
fi

# ---------------------------------------------------------
# 4/7 Starting Services
# ---------------------------------------------------------

print_step "4/7" "Starting Docker Services"
docker compose -f "${COMPOSE_FILE}" pull --quiet
docker compose -f "${COMPOSE_FILE}" up -d
print_success "Containers are starting..."

# ---------------------------------------------------------
# 5/7 Wait for Database (The "Better" Method)
# ---------------------------------------------------------

print_step "5/7" "Waiting for Database Healthcheck"

# Since your YAML has a healthcheck, we just wait for the status to change.
# This avoids the 'exec' crash problem entirely.
until [ "$(docker inspect -f '{{.State.Health.Status}}' $(docker compose -f ${COMPOSE_FILE} ps -q db))" == "healthy" ]; do
    echo -n "."
    sleep 2
done

echo ""
print_success "Database is ready and healthy"

# ---------------------------------------------------------
# 6/7 Database and Static Files
# ---------------------------------------------------------

print_step "6/7" "Backend Initialization"

print_info "Running database migrations..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py migrate --no-input

print_info "Collecting static files..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py collectstatic --no-input --clear

print_success "Database migrations and assets complete"

# ---------------------------------------------------------
# 7/7 Admin User
# ---------------------------------------------------------

print_step "7/7" "Creating Admin User"
echo -e "${ORANGE}Attention: You will now create the Django superuser.${NC}"
# Use exec without -T here because we WANT the interactive terminal
docker compose -f "${COMPOSE_FILE}" exec heimwerk python manage.py createsuperuser

# ---------------------------------------------------------
# Finalize
# ---------------------------------------------------------

print_info "Finalizing and restarting Nginx..."
docker compose -f "${COMPOSE_FILE}" restart nginx

echo -e "\n${BOLD}${GREEN}╔══════════════════════════════════════════╗"
echo -e "║        ✓ INSTALLATION COMPLETE ✓         ║"
echo -e "╚══════════════════════════════════════════╝${NC}\n"
echo -e "${ORANGE}URL:${NC} http://${USER_DOMAIN}"
echo -e "${ORANGE}Management:${NC}"
echo -e "  Stop:    docker compose -f ${COMPOSE_FILE} stop"
echo -e "  Logs:    docker compose -f ${COMPOSE_FILE} logs -f"
echo ""
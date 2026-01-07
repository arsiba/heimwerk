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
STAR="${ORANGE}★${NC}"

# Constants
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
PROJECT_NAME="heimwerk"
DB_VOLUME="${PROJECT_NAME}_db_data"
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
    echo ""
    echo -e "${BOLD}${BLUE}▶ [$1] $2${NC}"
}

print_success() { echo -e "  ${CHECK} $1"; }
print_error()   { echo -e "  ${CROSS} $1"; }
print_info()    { echo -e "  ${ARROW} $1"; }

fatal() {
    print_error "$1"
    exit 1
}

trap 'fatal "Installation failed. See error above."' ERR

# ---------------------------------------------------------
# Checks
# ---------------------------------------------------------

check_requirements() {
    print_step "0/7" "Checking Requirements"

    for cmd in docker curl openssl; do
        command -v "$cmd" &>/dev/null || fatal "$cmd is not installed"
        print_success "$cmd found"
    done

    docker compose version &>/dev/null || fatal "Docker Compose plugin missing"
    print_success "Docker Compose found"
}

# ---------------------------------------------------------
# Start
# ---------------------------------------------------------

print_header
check_requirements

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

print_step "1/7" "Configuration"

read -rp "Enter your domain or IP [localhost]: " USER_DOMAIN < /dev/tty
USER_DOMAIN=${USER_DOMAIN:-localhost}

print_info "Domain set to: $USER_DOMAIN"

# ---------------------------------------------------------
# Safety check
# ---------------------------------------------------------

if docker volume ls --format '{{.Name}}' | grep -q "^${DB_VOLUME}$"; then
    fatal "Existing database volume detected (${DB_VOLUME}).
To reset safely run:
  docker compose -f ${COMPOSE_FILE} down -v
  rm -f ${ENV_FILE}
Then re-run the installer."
fi

# ---------------------------------------------------------
# Download files
# ---------------------------------------------------------

print_step "2/7" "Downloading Production Files"

curl -fsSL "${REPO_RAW_URL}/${COMPOSE_FILE}" -o "${COMPOSE_FILE}"
curl -fsSL "${REPO_RAW_URL}/nginx.conf" -o nginx.conf

print_success "Production files downloaded"

# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

print_step "3/7" "Setting Up Environment"

RAND_SECRET=$(openssl rand -hex 32)
DB_PASS=$(openssl rand -hex 24)

cat > "${ENV_FILE}" <<EOF
SECRET_KEY=${RAND_SECRET}
DEBUG=False
ALLOWED_HOSTS=localhost 127.0.0.1 ::1 ${USER_DOMAIN}

POSTGRES_DB=heimwerk
POSTGRES_USER=heimwerk_admin
POSTGRES_PASSWORD=${DB_PASS}

DATABASE_URL=postgres://heimwerk_admin:${DB_PASS}@db:5432/heimwerk
EOF

print_success "Environment file created"

# ---------------------------------------------------------
# Docker
# ---------------------------------------------------------

print_step "4/7" "Starting Docker Services"

docker compose -f "${COMPOSE_FILE}" pull
docker compose -f "${COMPOSE_FILE}" up -d

print_success "Docker containers started"

# ---------------------------------------------------------
# Wait for database (Docker healthcheck)
# ---------------------------------------------------------

print_step "5/7" "Waiting for Database"

until [ "$(docker inspect -f '{{.State.Health.Status}}' heimwerk-db-1)" = "healthy" ]; do
    sleep 2
done

print_success "Database is healthy"

# ---------------------------------------------------------
# Database and static files
# ---------------------------------------------------------

print_step "6/7" "Database and Static Files"

print_info "Running database migrations"
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk \
    python manage.py migrate --no-input

print_success "Database migrations completed"

print_info "Collecting static files"
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk \
    python manage.py collectstatic --no-input --clear

print_success "Static files collected"

# ---------------------------------------------------------
# Admin user (interactive)
# ---------------------------------------------------------

print_step "7/7" "Creating Admin User"

echo ""
echo -e "${BOLD}${ORANGE}You will now create the Django superuser.${NC}"
echo -e "${ORANGE}This step is interactive and required.${NC}"
echo ""

docker compose -f "${COMPOSE_FILE}" exec heimwerk \
    python manage.py createsuperuser

# ---------------------------------------------------------
# Final restart
# ---------------------------------------------------------

print_info "Restarting services"
docker compose -f "${COMPOSE_FILE}" restart

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║        ✓ INSTALLATION COMPLETE ✓         ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${ORANGE}Access:${NC}"
echo -e "  ${ARROW} URL: http://${USER_DOMAIN}"
echo ""
echo -e "${ORANGE}Useful commands:${NC}"
echo -e "  ${ARROW} Logs:    docker compose -f ${COMPOSE_FILE} logs -f"
echo -e "  ${ARROW} Stop:    docker compose -f ${COMPOSE_FILE} down"
echo -e "  ${ARROW} Reset DB: docker compose -f ${COMPOSE_FILE} down -v"
echo ""

#!/bin/bash
set -Eeuo pipefail

# =========================================================
# HEIMWERK INSTALLATION SCRIPT
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

# Improved trap to show where it failed
error_handler() {
    echo ""
    fatal "Installation failed at line $1. Check logs with 'docker compose logs'."
}
trap 'error_handler $LINENO' ERR

# ---------------------------------------------------------
# Step 0: Checks
# ---------------------------------------------------------

check_requirements() {
    print_step "0/7" "Checking Requirements"

    for cmd in docker curl openssl; do
        if ! command -v "$cmd" &>/dev/null; then
            fatal "$cmd is not installed. Please install it first."
        fi
        print_success "$cmd found"
    done

    if ! docker compose version &>/dev/null; then
        fatal "Docker Compose V2 plugin is missing (run 'docker compose' to verify)."
    fi
    print_success "Docker Compose found"
}

# ---------------------------------------------------------
# Execution
# ---------------------------------------------------------

print_header
check_requirements

# Step 1: Configuration
print_step "1/7" "Configuration"
read -rp "Enter your domain or IP [localhost]: " USER_DOMAIN < /dev/tty
USER_DOMAIN=${USER_DOMAIN:-localhost}
print_info "Domain set to: $USER_DOMAIN"

# Safety check for existing data
if docker volume ls --format '{{.Name}}' | grep -q "^${DB_VOLUME}$"; then
    echo -e "${ORANGE}! Existing database volume detected.${NC}"
    read -rp "Keep existing data? [Y/n]: " KEEP_DATA < /dev/tty
    if [[ ! $KEEP_DATA =~ ^[Yy]$ ]] && [[ ! -z $KEEP_DATA ]]; then
        fatal "Installation aborted to protect existing data."
    fi
fi

# Step 2: Download files
print_step "2/7" "Downloading Production Files"
curl -fsSL "${REPO_RAW_URL}/${COMPOSE_FILE}" -o "${COMPOSE_FILE}"
curl -fsSL "${REPO_RAW_URL}/nginx.conf" -o nginx.conf
print_success "Production files downloaded"

# Step 3: Environment Setup
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
chmod 600 "${ENV_FILE}"
print_success "Environment file created (.env)"

# Step 4: Docker Start
print_step "4/7" "Starting Docker Services"
docker compose -f "${COMPOSE_FILE}" pull --quiet
docker compose -f "${COMPOSE_FILE}" up -d
print_success "Docker containers started"

# Step 5: Wait for Database (Robust Logic)
print_step "5/7" "Waiting for Database"
MAX_RETRIES=30
RETRY_COUNT=0

until [ $RETRY_COUNT -ge $MAX_RETRIES ]; do
    # Check if DB is ready using pg_isready
    if docker compose -f "${COMPOSE_FILE}" exec -T db pg_isready -U heimwerk_admin > /dev/null 2>&1; then
        break
    fi
    echo -n "."
    ((RETRY_COUNT++))
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo ""
    fatal "Database failed to become ready in time. Check 'docker compose logs db'."
fi

echo ""
print_success "Database is healthy"

# Step 6: Database and Static Files
print_step "6/7" "Database and Static Files"
print_info "Running database migrations..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py migrate --no-input

print_info "Collecting static files..."
docker compose -f "${COMPOSE_FILE}" exec -T heimwerk python manage.py collectstatic --no-input --clear
print_success "Database and assets ready"

# Step 7: Admin User
print_step "7/7" "Creating Admin User"
echo -e "${ORANGE}Interactive: Please set up your admin account now.${NC}"
docker compose -f "${COMPOSE_FILE}" exec heimwerk python manage.py createsuperuser || print_info "Superuser creation skipped or failed (perhaps it already exists?)"

# Finalize
print_info "Finalizing services..."
docker compose -f "${COMPOSE_FILE}" restart heimwerk nginx

echo -e "\n${BOLD}${GREEN}╔══════════════════════════════════════════╗"
echo -e "║        ✓ INSTALLATION COMPLETE ✓         ║"
echo -e "╚══════════════════════════════════════════╝${NC}\n"
echo -e "${ORANGE}Access:${NC} http://${USER_DOMAIN}"
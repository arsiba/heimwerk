#!/bin/bash

set -e  # Exit on any error

# Color Definitions
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

# Helper Functions
print_header() {
    echo ""
    echo -e "${BOLD}${ORANGE}╔══════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${ORANGE}║                                          ║${NC}"
    echo -e "${BOLD}${ORANGE}║      ${STAR} HEIMWERK INSTALLATION ${STAR}       ║${NC}"
    echo -e "${BOLD}${ORANGE}║                                          ║${NC}"
    echo -e "${BOLD}${ORANGE}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${BOLD}${BLUE}▶ [$1] $2${NC}"
    echo -e "${CYAN}────────────────────────────────────────${NC}"
}

print_success() {
    echo -e "  ${CHECK} ${GREEN}$1${NC}"
}

print_error() {
    echo -e "  ${CROSS} ${RED}$1${NC}"
}

print_info() {
    echo -e "  ${ARROW} ${CYAN}$1${NC}"
}

check_requirements() {
    print_step "0/7" "Checking Requirements"

    local missing_deps=0

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        missing_deps=1
    else
        print_success "Docker found"
    fi

    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        missing_deps=1
    else
        print_success "Docker Compose found"
    fi

    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed"
        missing_deps=1
    else
        print_success "curl found"
    fi

    if ! command -v openssl &> /dev/null; then
        print_error "openssl is not installed"
        missing_deps=1
    else
        print_success "openssl found"
    fi

    if [ $missing_deps -eq 1 ]; then
        echo ""
        print_error "Missing required dependencies. Please install them and try again."
        exit 1
    fi
}

validate_password() {
    if [ ${#1} -lt 8 ]; then
        return 1
    fi
    return 0
}

# Trap errors
trap 'print_error "Installation failed! Check the error above."; exit 1' ERR

# Main Installation
clear
print_header

check_requirements

# 1. Configuration
print_step "1/7" "Configuration"

echo -n -e "${ORANGE}Enter your domain or IP ${BOLD}[localhost]${NC}${ORANGE}: ${NC}"
read -r USER_DOMAIN < /dev/tty
USER_DOMAIN=${USER_DOMAIN:-localhost}
print_info "Domain set to: ${BOLD}${USER_DOMAIN}${NC}"

echo -n -e "${ORANGE}Enter Admin Username ${BOLD}[admin]${NC}${ORANGE}: ${NC}"
read -r ADMIN_USER < /dev/tty
ADMIN_USER=${ADMIN_USER:-admin}
print_info "Username set to: ${BOLD}${ADMIN_USER}${NC}"

echo -n -e "${ORANGE}Enter Admin Email ${BOLD}[admin@example.com]${NC}${ORANGE}: ${NC}"
read -r ADMIN_EMAIL < /dev/tty
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
print_info "Email set to: ${BOLD}${ADMIN_EMAIL}${NC}"

while true; do
    echo -n -e "${ORANGE}Enter Admin Password (min. 8 chars): ${NC}"
    read -rs ADMIN_PASS < /dev/tty
    echo ""

    if validate_password "$ADMIN_PASS"; then
        print_success "Password accepted"
        break
    else
        print_error "Password must be at least 8 characters long. Please try again."
    fi
done

# 2. Download files
print_step "2/7" "Downloading Production Files"
REPO_RAW_URL="https://raw.githubusercontent.com/arsiba/heimwerk/main"

print_info "Fetching docker-compose.prod.yml..."
if curl -fsSL "${REPO_RAW_URL}/docker-compose.prod.yml" -o docker-compose.prod.yml; then
    print_success "docker-compose.prod.yml downloaded"
else
    print_error "Failed to download docker-compose.prod.yml"
    exit 1
fi

print_info "Fetching nginx.conf..."
if curl -fsSL "${REPO_RAW_URL}/nginx.conf" -o nginx.conf; then
    print_success "nginx.conf downloaded"
else
    print_error "Failed to download nginx.conf"
    exit 1
fi

# 3. Environment Setup
print_step "3/7" "Setting Up Environment"

if [ ! -f .env ]; then
    print_info "Generating secure credentials..."
    RAND_SECRET=$(openssl rand -base64 32 | tr -d '=/+')
    DB_PASS=$(openssl rand -base64 12 | tr -d '=/+')

    cat <<EOF > .env
SECRET_KEY='$RAND_SECRET'
DEBUG=False
ALLOWED_HOSTS='127.0.0.1 localhost ::1 $USER_DOMAIN'
POSTGRES_DB=heimwerk
POSTGRES_USER=heimwerk_admin
POSTGRES_PASSWORD=$DB_PASS
DATABASE_URL=postgres://heimwerk_admin:$DB_PASS@db:5432/heimwerk
EOF
    print_success "Environment file created"
else
    print_info "Using existing .env file"
fi

# 4. Start Docker
print_step "4/7" "Starting Docker Services"

print_info "Pulling Docker images..."
docker compose -f docker-compose.prod.yml pull

print_info "Starting containers..."
docker compose -f docker-compose.prod.yml up -d

print_success "Docker services started"

# 5. Wait for services
print_step "5/7" "Waiting for Services"

print_info "Waiting for database to be ready..."
sleep 10

# Check if services are actually running
if ! docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_error "Services failed to start properly"
    docker compose -f docker-compose.prod.yml logs
    exit 1
fi

print_success "Services are ready"

# 6. Database and Static Files
print_step "6/7" "Setting Up Database and Static Files"

print_info "Running database migrations..."
if docker compose -f docker-compose.prod.yml exec -T heimwerk python manage.py migrate --no-input; then
    print_success "Database migrations completed"
else
    print_error "Database migration failed"
    docker compose -f docker-compose.prod.yml logs heimwerk
    exit 1
fi

print_info "Collecting static files (this is critical!)..."
if docker compose -f docker-compose.prod.yml exec -T heimwerk python manage.py collectstatic --no-input --clear; then
    print_success "Static files collected successfully"
else
    print_error "Static file collection failed"
    docker compose -f docker-compose.prod.yml logs heimwerk
    exit 1
fi

# 7. Create Admin User
print_step "7/7" "Creating Admin Account"

print_info "Creating superuser account..."

# First, try to delete any existing admin user with the same username
docker compose -f docker-compose.prod.yml exec -T heimwerk python manage.py shell <<EOF 2>/dev/null || true
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    user = User.objects.get(username='$ADMIN_USER')
    user.delete()
    print('Removed existing user')
except User.DoesNotExist:
    pass
EOF

# Now create the new admin user
if docker compose -f docker-compose.prod.yml exec -T \
    -e DJANGO_SUPERUSER_PASSWORD="$ADMIN_PASS" \
    -e DJANGO_SUPERUSER_USERNAME="$ADMIN_USER" \
    -e DJANGO_SUPERUSER_EMAIL="$ADMIN_EMAIL" \
    heimwerk python manage.py createsuperuser --no-input; then
    print_success "Admin account created successfully"
else
    print_error "Failed to create admin account"
    print_info "Trying alternative method..."

    # Alternative: Use Django shell to create user
    docker compose -f docker-compose.prod.yml exec -T heimwerk python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USER').exists():
    User.objects.create_superuser('$ADMIN_USER', '$ADMIN_EMAIL', '$ADMIN_PASS')
    print('Admin user created via shell')
else:
    user = User.objects.get(username='$ADMIN_USER')
    user.set_password('$ADMIN_PASS')
    user.email = '$ADMIN_EMAIL'
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print('Admin user updated')
EOF
    print_success "Admin account configured"
fi

# Final restart to ensure everything is running smoothly
print_info "Restarting services for clean state..."
docker compose -f docker-compose.prod.yml restart

print_info "Waiting for services to stabilize..."
sleep 5

# Success Message
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║                                          ║${NC}"
echo -e "${BOLD}${GREEN}║         ${CHECK} INSTALLATION COMPLETE! ${CHECK}       ║${NC}"
echo -e "${BOLD}${GREEN}║                                          ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}${ORANGE}Access Information:${NC}"
echo -e "  ${ARROW} URL:      ${BOLD}${CYAN}http://$USER_DOMAIN${NC}"
echo -e "  ${ARROW} Username: ${BOLD}${CYAN}$ADMIN_USER${NC}"
echo -e "  ${ARROW} Password: ${BOLD}${CYAN}(the password you entered)${NC}"
echo ""
echo -e "${ORANGE}Quick Commands:${NC}"
echo -e "  ${ARROW} View logs:    ${CYAN}docker compose -f docker-compose.prod.yml logs -f${NC}"
echo -e "  ${ARROW} Stop:         ${CYAN}docker compose -f docker-compose.prod.yml down${NC}"
echo -e "  ${ARROW} Restart:      ${CYAN}docker compose -f docker-compose.prod.yml restart${NC}"
echo ""
echo -e "${ORANGE}Troubleshooting:${NC}"
echo -e "  ${ARROW} If you can't login, reset password with:${NC}"
echo -e "      ${CYAN}docker compose -f docker-compose.prod.yml exec heimwerk python manage.py changepassword $ADMIN_USER${NC}"
echo ""
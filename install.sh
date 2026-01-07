#!/bin/bash

# Styling
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${ORANGE}==========================================${NC}"
echo -e "${ORANGE}   Heimwerk - Automated Installation      ${NC}"
echo -e "${ORANGE}==========================================${NC}"

# 1. Ask for all inputs at the beginning
echo -e "${BLUE}[1/5] Configuration...${NC}"

# Using /dev/tty ensures input works even when running via curl | bash
echo -n -e "${ORANGE}Enter your domain or IP [localhost]: ${NC}"
read -r USER_DOMAIN < /dev/tty
USER_DOMAIN=${USER_DOMAIN:-localhost}

echo -n -e "${ORANGE}Enter Admin Username [admin]: ${NC}"
read -r ADMIN_USER < /dev/tty
ADMIN_USER=${ADMIN_USER:-admin}

echo -n -e "${ORANGE}Enter Admin Email [admin@example.com]: ${NC}"
read -r ADMIN_EMAIL < /dev/tty
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}

echo -n -e "${ORANGE}Enter Admin Password (min. 8 chars): ${NC}"
# -s hides the password input
read -rs ADMIN_PASS < /dev/tty
echo "" # New line after hidden password

# 2. Download files
echo -e "\n${BLUE}[2/5] Downloading production files...${NC}"
REPO_RAW_URL="https://raw.githubusercontent.com/arsiba/heimwerk/main"
curl -sO "${REPO_RAW_URL}/docker-compose.prod.yml"
curl -sO "${REPO_RAW_URL}/nginx.conf"

# 3. Environment Setup
if [ ! -f .env ]; then
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
fi

# 4. Start Docker
echo -e "\n${BLUE}[3/5] Starting Docker services...${NC}"
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# 5. Finalize (Migrations & Superuser)
echo -e "\n${BLUE}[4/5] Finalizing Database (this takes a moment)...${NC}"
sleep 10
docker compose -f docker-compose.prod.yml exec -T heimwerk python manage.py migrate --no-input

echo -e "${BLUE}[5/5] Creating Admin Account...${NC}"
# Passing variables to the container for non-interactive creation
docker compose -f docker-compose.prod.yml exec -T \
    -e DJANGO_SUPERUSER_PASSWORD="$ADMIN_PASS" \
    -e DJANGO_SUPERUSER_USERNAME="$ADMIN_USER" \
    -e DJANGO_SUPERUSER_EMAIL="$ADMIN_EMAIL" \
    heimwerk python manage.py createsuperuser --no-input

echo -e "\n${ORANGE}==========================================${NC}"
echo -e "${GREEN}   SUCCESS! Heimwerk is installed.${NC}"
echo -e "${ORANGE}   URL: http://$USER_DOMAIN${NC}"
echo -e "${ORANGE}   Admin: $ADMIN_USER / (your password)${NC}"
echo -e "${ORANGE}==========================================${NC}"
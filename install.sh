#!/bin/bash

# Styling
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${ORANGE}==========================================${NC}"
echo -e "${ORANGE}   Heimwerk - Automated Installation      ${NC}"
echo -e "${ORANGE}==========================================${NC}"

# 1. Download necessary files
echo -e "\n${BLUE}[1/4] Downloading production files...${NC}"
REPO_RAW_URL="https://raw.githubusercontent.com/arsiba/heimwerk/main"

curl -sO "${REPO_RAW_URL}/docker-compose.prod.yml"
curl -sO "${REPO_RAW_URL}/nginx.conf"

# 2. Interactive Configuration
echo -e "\n${BLUE}[2/4] Configuration...${NC}"

# Ask for Domain (Redirection from /dev/tty is needed for curl | bash pipes)
echo -n -e "${ORANGE}Enter your domain or IP (e.g. heimwerk.com): ${NC}"
read -r USER_DOMAIN < /dev/tty

# If empty, default to localhost
USER_DOMAIN=${USER_DOMAIN:-localhost}

# Generate secure credentials automatically
RAND_SECRET=$(openssl rand -base64 32 | tr -d '=/+')
DB_PASS=$(openssl rand -base64 12 | tr -d '=/+')

# Create .env from scratch using the inputs
cat <<EOF > .env
SECRET_KEY='$RAND_SECRET'
DEBUG=False
ALLOWED_HOSTS='127.0.0.1 localhost ::1 $USER_DOMAIN'

POSTGRES_DB=heimwerk
POSTGRES_USER=heimwerk_admin
POSTGRES_PASSWORD=$DB_PASS

DATABASE_URL=postgres://heimwerk_admin:$DB_PASS@db:5432/heimwerk
EOF

echo -e "${GREEN}✔ Configuration created for: $USER_DOMAIN${NC}"

# 3. Start Docker Containers
echo -e "\n${BLUE}[3/4] Starting Docker services...${NC}"
docker compose -f docker-compose.prod.yml up -d

# 4. Database & Superuser
echo -e "\n${BLUE}[4/4] Finalizing setup...${NC}"
echo "Waiting for Database (10s)..."
sleep 10
docker compose -f docker-compose.prod.yml exec heimwerk python manage.py migrate

# Now start the interactive Superuser creation
echo -e "\n${ORANGE}>>> Please create your Administrator account now:${NC}"
docker compose -f docker-compose.prod.yml exec heimwerk python manage.py createsuperuser

echo -e "\n${ORANGE}==========================================${NC}"
echo -e "${GREEN}   SUCCESS! Heimwerk is ready.${NC}"
echo -e "${ORANGE}   URL: http://$USER_DOMAIN${NC}"
echo -e "${ORANGE}==========================================${NC}"
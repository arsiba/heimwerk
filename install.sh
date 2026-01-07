#!/bin/bash

# Styling
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}   Heimwerk - Automated Installation      ${NC}"
echo -e "${BLUE}==========================================${NC}"

# 1. Download necessary files
echo -e "\n${BLUE}[1/5] Downloading configuration files...${NC}"
REPO_RAW_URL="https://raw.githubusercontent.com/arsiba/heimwerk/main"

curl -sO $REPO_RAW_URL/docker-compose.prod.yml
curl -sO $REPO_RAW_URL/nginx.conf
curl -sO $REPO_RAW_URL/.env.example

# 2. Domain and Environment Setup
echo -e "\n${BLUE}[2/5] Setting up environment...${NC}"

# Ask for Domain
read -p "Enter your domain or IP (e.g., heimwerk.example.com or 1.2.3.4): " USER_DOMAIN
if [ -z "$USER_DOMAIN" ]; then
    USER_DOMAIN="localhost"
fi

if [ ! -f .env ]; then
    cp .env.example .env

    # 2a. Generate a secure random Django Secret Key
    RAND_KEY=$(openssl rand -base64 32)
    # Replace the hardcoded secret key
    sed -i "s|SECRET_KEY=.*|SECRET_KEY='$RAND_KEY'|g" .env

    # 2b. Set the ALLOWED_HOSTS with the user's domain
    # We keep localhost/127.0.0.1 for internal health checks
    NEW_HOSTS="127.0.0.1 localhost ::1 $USER_DOMAIN"
    sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=\"$NEW_HOSTS\"|g" .env

    echo -e "${GREEN}✔ .env created with a fresh SECRET_KEY and Domain: $USER_DOMAIN${NC}"
else
    echo -e "${GREEN}✔ .env already exists. Skipping configuration to prevent overwriting.${NC}"
fi

# 3. Start Containers
echo -e "\n${BLUE}[3/5] Starting Docker containers...${NC}"
docker compose -f docker-compose.prod.yml up -d

# 4. Database Migrations
echo -e "\n${BLUE}[4/5] Running database migrations...${NC}"
# Wait for Postgres to be ready
echo "Waiting for database to initialize..."
sleep 10
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 5. Create Superuser
echo -e "\n${BLUE}[5/5] Creating Administrator account...${NC}"
echo -e "${BLUE}Please enter your details for the admin panel:${NC}"
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}   Installation Successful!               ${NC}"
echo -e "${GREEN}   Heimwerk is running on $USER_DOMAIN    ${NC}"
echo -e "${GREEN}==========================================${NC}"
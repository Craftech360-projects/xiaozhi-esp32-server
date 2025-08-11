#!/bin/bash

# Azure PostgreSQL Setup Script for xiaozhi-esp32-server
# This script creates and configures Azure PostgreSQL Flexible Server

set -e

# Configuration variables
RESOURCE_GROUP=${AZURE_RESOURCE_GROUP:-"xiaozhi-rg"}
LOCATION=${AZURE_LOCATION:-"East Asia"}
SERVER_NAME=${AZURE_POSTGRES_SERVER:-"xiaozhi-postgres-server"}
DATABASE_NAME=${AZURE_POSTGRES_DATABASE:-"xiaozhi_esp32_server"}
ADMIN_USERNAME=${AZURE_POSTGRES_USERNAME:-"xiaozhi_admin"}
ADMIN_PASSWORD=${AZURE_POSTGRES_PASSWORD:-""}
SKU_NAME=${AZURE_POSTGRES_SKU:-"Standard_B1ms"}
TIER=${AZURE_POSTGRES_TIER:-"Burstable"}
STORAGE_SIZE=${AZURE_POSTGRES_STORAGE:-"32"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Azure PostgreSQL Setup for xiaozhi-esp32-server ===${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Please log in to Azure CLI first:${NC}"
    echo "az login"
    exit 1
fi

# Prompt for password if not set
if [ -z "$ADMIN_PASSWORD" ]; then
    echo -e "${YELLOW}Enter password for PostgreSQL admin user (minimum 8 characters):${NC}"
    read -s ADMIN_PASSWORD
    echo
    
    if [ ${#ADMIN_PASSWORD} -lt 8 ]; then
        echo -e "${RED}Error: Password must be at least 8 characters long${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}Configuration:${NC}"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Server Name: $SERVER_NAME"
echo "Database Name: $DATABASE_NAME"
echo "Admin Username: $ADMIN_USERNAME"
echo "SKU: $SKU_NAME"
echo "Tier: $TIER"
echo "Storage: ${STORAGE_SIZE}GB"
echo

read -p "Continue with this configuration? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 1
fi

echo -e "${BLUE}Step 1: Creating resource group...${NC}"
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output table

echo -e "${BLUE}Step 2: Creating PostgreSQL Flexible Server...${NC}"
az postgres flexible-server create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$SERVER_NAME" \
    --location "$LOCATION" \
    --admin-user "$ADMIN_USERNAME" \
    --admin-password "$ADMIN_PASSWORD" \
    --sku-name "$SKU_NAME" \
    --tier "$TIER" \
    --storage-size "$STORAGE_SIZE" \
    --version 15 \
    --public-access 0.0.0.0 \
    --output table

echo -e "${BLUE}Step 3: Creating database...${NC}"
az postgres flexible-server db create \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$SERVER_NAME" \
    --database-name "$DATABASE_NAME" \
    --output table

echo -e "${BLUE}Step 4: Configuring firewall rules...${NC}"
# Allow Azure services
az postgres flexible-server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$SERVER_NAME" \
    --rule-name "AllowAzureServices" \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0 \
    --output table

# Allow current IP
CURRENT_IP=$(curl -s https://api.ipify.org)
if [ ! -z "$CURRENT_IP" ]; then
    echo "Adding firewall rule for current IP: $CURRENT_IP"
    az postgres flexible-server firewall-rule create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$SERVER_NAME" \
        --rule-name "AllowCurrentIP" \
        --start-ip-address "$CURRENT_IP" \
        --end-ip-address "$CURRENT_IP" \
        --output table
fi

echo -e "${BLUE}Step 5: Configuring server parameters...${NC}"
# Set timezone
az postgres flexible-server parameter set \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$SERVER_NAME" \
    --name timezone \
    --value "Asia/Shanghai" \
    --output table

# Enable extensions
az postgres flexible-server parameter set \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$SERVER_NAME" \
    --name shared_preload_libraries \
    --value "pg_stat_statements" \
    --output table

echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo
echo -e "${BLUE}Connection Details:${NC}"
echo "Server: ${SERVER_NAME}.postgres.database.azure.com"
echo "Database: $DATABASE_NAME"
echo "Username: ${ADMIN_USERNAME}@${SERVER_NAME}"
echo "Port: 5432"
echo "SSL Mode: require"
echo
echo -e "${BLUE}Environment Variables:${NC}"
echo "export AZURE_POSTGRES_SERVER=$SERVER_NAME"
echo "export AZURE_POSTGRES_DATABASE=$DATABASE_NAME"
echo "export AZURE_POSTGRES_USERNAME=$ADMIN_USERNAME"
echo "export AZURE_POSTGRES_PASSWORD='$ADMIN_PASSWORD'"
echo
echo -e "${BLUE}Connection String:${NC}"
echo "jdbc:postgresql://${SERVER_NAME}.postgres.database.azure.com:5432/${DATABASE_NAME}?sslmode=require"
echo
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Set the environment variables above"
echo "2. Test connection: psql -h ${SERVER_NAME}.postgres.database.azure.com -U ${ADMIN_USERNAME}@${SERVER_NAME} -d ${DATABASE_NAME}"
echo "3. Deploy your application with: docker-compose -f docker-compose_all.yml up -d"
echo
echo -e "${GREEN}Azure PostgreSQL setup completed successfully!${NC}"
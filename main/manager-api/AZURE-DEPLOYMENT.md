# Azure Server Continuous Deployment Guide

This guide will help you set up the Xiaozhi backend to run continuously on your Azure server using systemd service.

## 🚀 Quick Start

### 1. Initial Environment Setup (One-time)
```bash
# Upload files to your Azure server
scp -r * root@YOUR_AZURE_IP:/root/xiaozhi-esp32-server/main/manager-api/

# SSH to your Azure server
ssh root@YOUR_AZURE_IP

# Navigate to the project directory
cd /root/xiaozhi-esp32-server/main/manager-api

# Run the environment setup (installs Docker, Java, databases)
sudo ./azure-setup.sh
```

### 2. Build and Deploy
```bash
# Build the JAR file
mvn clean package -DskipTests

# Deploy as a systemd service
sudo ./deploy-azure.sh
```

### 3. Service Management
```bash
# Check service status
sudo ./service-manager.sh status

# View live logs
sudo ./service-manager.sh logs

# Restart service
sudo ./service-manager.sh restart

# Check API health
sudo ./service-manager.sh health
```

## 📋 Available Scripts

### `azure-setup.sh`
- **Purpose**: One-time environment setup
- **What it does**:
  - Installs Docker, Docker Compose, Java
  - Sets up MySQL and Redis containers
  - Creates necessary directories
- **Usage**: `sudo ./azure-setup.sh`

### `deploy-azure.sh`
- **Purpose**: Deploy the application as a systemd service
- **What it does**:
  - Stops existing processes
  - Installs systemd service
  - Starts the service with proper configuration
  - Verifies deployment
- **Usage**: `sudo ./deploy-azure.sh`

### `service-manager.sh`
- **Purpose**: Manage the running service
- **Commands**:
  - `start` - Start the service
  - `stop` - Stop the service
  - `restart` - Restart the service
  - `status` - Show service status
  - `logs` - View live logs
  - `health` - Check API health
- **Usage**: `sudo ./service-manager.sh [command]`

## 🔧 Service Configuration

The service is configured to:
- ✅ **Auto-start** on server boot
- ✅ **Auto-restart** if it crashes
- ✅ **Use local databases** (MySQL & Redis)
- ✅ **Log to systemd journal**
- ✅ **Run on port 8002**

## 🗄️ Database Configuration

### MySQL
- **Host**: localhost:3306
- **Database**: xiaozhi_db
- **Username**: xiaozhi_user
- **Password**: xiaozhi_password123

### Redis
- **Host**: localhost:6379
- **No password required**

## 📊 Monitoring and Troubleshooting

### Check Service Status
```bash
sudo systemctl status xiaozhi-backend
```

### View Logs
```bash
# Live logs
sudo journalctl -u xiaozhi-backend -f

# Recent logs
sudo journalctl -u xiaozhi-backend -n 100
```

### Test API Health
```bash
curl http://localhost:8002/toy/user/captcha
```

### Check Database Connectivity
```bash
# Test MySQL
docker exec xiaozhi-mysql mysqladmin ping -h localhost

# Test Redis
docker exec xiaozhi-redis redis-cli ping
```

## 🔄 Updates and Redeployment

When you need to update the application:

1. **Build new JAR file**:
   ```bash
   mvn clean package -DskipTests
   ```

2. **Restart the service**:
   ```bash
   sudo ./service-manager.sh restart
   ```

## 🛡️ Security Notes

- The service runs as root (required for systemd management)
- Databases are local and not exposed externally
- No Railway or external cloud databases are used
- All connections use localhost for security

## 🌐 Access Points

- **Backend API**: http://YOUR_AZURE_IP:8002
- **Frontend**: http://YOUR_AZURE_IP:8886 (if deployed)
- **Health Check**: http://YOUR_AZURE_IP:8002/toy/user/captcha

## 🆘 Common Issues

### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u xiaozhi-backend -n 50

# Check if JAR file exists
ls -la xiaozhi-esp32-api.jar

# Check database connectivity
docker ps | grep xiaozhi
```

### API Not Responding
```bash
# Check if service is running
sudo ./service-manager.sh status

# Check port 8002
netstat -tlnp | grep 8002

# Check firewall
ufw status
```

### Database Connection Issues
```bash
# Restart databases
docker restart xiaozhi-mysql xiaozhi-redis

# Check database logs
docker logs xiaozhi-mysql
docker logs xiaozhi-redis
```

## 📞 Support Commands

```bash
# Complete service restart
sudo ./service-manager.sh stop
sudo ./service-manager.sh start

# View all systemd services
sudo systemctl list-units --type=service

# Disable service (won't start on boot)
sudo systemctl disable xiaozhi-backend

# Enable service (will start on boot)
sudo systemctl enable xiaozhi-backend
```
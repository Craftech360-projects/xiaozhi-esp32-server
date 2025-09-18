# 🌐 Azure Cloud Deployment Guide - Continuous 24/7 Operation

This guide will help you deploy the Xiaozhi backend to run continuously on your Azure cloud server so users can access it 24/7.

## 🎯 Goal
Deploy the backend to run continuously at `http://20.189.97.87:8002` with:
- ✅ 24/7 availability
- ✅ Auto-restart on crashes
- ✅ Auto-start on server reboot
- ✅ Local Azure databases (no external dependencies)

---

## 📋 Step-by-Step Deployment

### Step 1: Prepare Files for Upload
On your local machine, in the `manager-api` folder, you should have these files:
```
xiaozhi-esp32-api.jar          # Built JAR file
azure-setup.sh                # Environment setup
deploy-azure.sh               # Service deployment
service-manager.sh            # Service management
xiaozhi-backend.service       # Systemd service config
docker-compose-azure-local.yml # Database setup
AZURE-CLOUD-DEPLOYMENT.md    # This guide
```

### Step 2: Upload to Azure Server
```bash
# From your local machine, upload all files to Azure
scp -r . root@20.189.97.87:/root/xiaozhi-esp32-server/main/manager-api/

# Alternative: Use your preferred file transfer method (WinSCP, FileZilla, etc.)
```

### Step 3: Connect to Azure Server
```bash
ssh root@20.189.97.87
cd /root/xiaozhi-esp32-server/main/manager-api
```

### Step 4: Set Up Environment (One-time setup)
```bash
# Make scripts executable
chmod +x *.sh

# Run the complete environment setup
sudo ./azure-setup.sh
```

This will:
- Install Docker, Java, and required packages
- Set up MySQL database on port 3306
- Set up Redis cache on port 6379
- Configure all services for auto-restart

### Step 5: Build JAR File (if not already built)
```bash
# If you don't have the JAR file, build it
mvn clean package -DskipTests
```

### Step 6: Deploy as Continuous Service
```bash
# Deploy the application as a systemd service
sudo ./deploy-azure.sh
```

This will:
- Install the service to start automatically
- Configure it to restart on crashes
- Start the service immediately
- Verify it's working

### Step 7: Verify Deployment
```bash
# Check service status
sudo ./service-manager.sh status

# Test the API
curl http://20.189.97.87:8002/toy/user/captcha

# View logs
sudo ./service-manager.sh logs
```

---

## 🔧 Service Management Commands

Once deployed, you can manage the service with these commands:

```bash
# Check if service is running
sudo ./service-manager.sh status

# Start the service
sudo ./service-manager.sh start

# Stop the service
sudo ./service-manager.sh stop

# Restart the service
sudo ./service-manager.sh restart

# View live logs
sudo ./service-manager.sh logs

# Check API health
sudo ./service-manager.sh health
```

---

## 🌐 Public Access Points

After successful deployment, users can access:

- **Backend API**: `http://20.189.97.87:8002`
- **Captcha Endpoint**: `http://20.189.97.87:8002/toy/user/captcha`
- **Frontend** (if deployed): `http://20.189.97.87:8886`

---

## 🛡️ Security & Firewall Configuration

### Open Required Ports
```bash
# Allow backend port
sudo ufw allow 8002

# Allow frontend port (if needed)
sudo ufw allow 8886

# Check firewall status
sudo ufw status
```

### Azure Portal Configuration
In Azure Portal, ensure your VM's Network Security Group allows:
- **Inbound port 8002** (Backend API)
- **Inbound port 8886** (Frontend, if needed)

---

## 🚀 Auto-Start Configuration

The service is configured to:
- ✅ **Start automatically** when the Azure VM boots
- ✅ **Restart automatically** if the application crashes
- ✅ **Use local databases** (no external dependencies)
- ✅ **Log everything** for debugging

### Verify Auto-Start
```bash
# Check if service is enabled for auto-start
sudo systemctl is-enabled xiaozhi-backend

# Should return: enabled
```

---

## 📊 Monitoring & Health Checks

### Real-time Monitoring
```bash
# View live logs
sudo journalctl -u xiaozhi-backend -f

# Check system resources
htop

# Check Docker containers
docker ps
```

### Health Check Script
Create a simple health check:
```bash
#!/bin/bash
# Save as health-check.sh

if curl -s -f http://localhost:8002/toy/user/captcha > /dev/null; then
    echo "✅ Service is healthy"
    exit 0
else
    echo "❌ Service is down"
    exit 1
fi
```

---

## 🔄 Updates & Redeployment

When you need to update the application:

1. **Upload new JAR file**:
   ```bash
   scp xiaozhi-esp32-api.jar root@20.189.97.87:/root/xiaozhi-esp32-server/main/manager-api/
   ```

2. **Restart the service**:
   ```bash
   ssh root@20.189.97.87
   cd /root/xiaozhi-esp32-server/main/manager-api
   sudo ./service-manager.sh restart
   ```

---

## 🆘 Troubleshooting

### Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u xiaozhi-backend -n 100

# Check if JAR file exists
ls -la xiaozhi-esp32-api.jar

# Check Java installation
java -version

# Manually test the JAR
java -jar xiaozhi-esp32-api.jar --spring.profiles.active=azure
```

### Database Issues
```bash
# Check database containers
docker ps | grep xiaozhi

# Restart databases
docker restart xiaozhi-mysql xiaozhi-redis

# Check database logs
docker logs xiaozhi-mysql
docker logs xiaozhi-redis

# Test database connections
docker exec xiaozhi-mysql mysqladmin ping
docker exec xiaozhi-redis redis-cli ping
```

### Network/Firewall Issues
```bash
# Check if port is open
netstat -tlnp | grep 8002

# Test internal connectivity
curl http://localhost:8002/toy/user/captcha

# Check firewall
sudo ufw status

# Test external connectivity (from another machine)
curl http://20.189.97.87:8002/toy/user/captcha
```

### Service Logs
```bash
# Recent logs
sudo journalctl -u xiaozhi-backend -n 50

# Logs from specific time
sudo journalctl -u xiaozhi-backend --since "2 hours ago"

# Follow logs in real-time
sudo journalctl -u xiaozhi-backend -f
```

---

## 📞 Emergency Recovery

If something goes wrong:

1. **Stop everything and restart**:
   ```bash
   sudo ./service-manager.sh stop
   docker restart xiaozhi-mysql xiaozhi-redis
   sleep 10
   sudo ./service-manager.sh start
   ```

2. **Complete redeployment**:
   ```bash
   sudo ./deploy-azure.sh
   ```

3. **Check system resources**:
   ```bash
   df -h          # Disk space
   free -h        # Memory usage
   top            # CPU usage
   ```

---

## ✅ Success Checklist

After deployment, verify these items:

- [ ] Service status shows "active (running)"
- [ ] Captcha endpoint returns HTTP 200
- [ ] Service is enabled for auto-start
- [ ] Databases are running and healthy
- [ ] Firewall ports are open
- [ ] External access works from internet
- [ ] Logs show no errors

---

## 📋 Quick Reference Commands

```bash
# Service management
sudo systemctl status xiaozhi-backend
sudo systemctl start xiaozhi-backend
sudo systemctl stop xiaozhi-backend
sudo systemctl restart xiaozhi-backend

# Database management
docker ps | grep xiaozhi
docker restart xiaozhi-mysql xiaozhi-redis

# Health checks
curl http://localhost:8002/toy/user/captcha
curl http://20.189.97.87:8002/toy/user/captcha

# Logs
sudo journalctl -u xiaozhi-backend -f
```

Your backend will now run continuously at `http://20.189.97.87:8002` and be accessible to users 24/7!
# 🚀 Complete Azure Deployment Solution

## 🎯 Problem Solution
Your backend keeps trying to connect to Railway databases instead of local Azure databases. This complete deployment package fixes all configuration issues and ensures continuous operation.

## 📋 Step 1: Build Fresh JAR with Azure Configuration

Run these commands on your **LOCAL MACHINE**:

```bash
# Navigate to project
cd D:\Crafttech\xiaozhi-esp32-server\main\manager-api

# Clean and build with Azure profile
mvn clean package -DskipTests -Dspring.profiles.active=azure

# Verify JAR was created
ls -la target/xiaozhi-esp32-api.jar
```

## 📋 Step 2: Upload Files to Azure VM

```bash
# Upload JAR and deployment scripts
scp target/xiaozhi-esp32-api.jar root@20.189.97.87:/root/
scp azure-robust-deploy.sh root@20.189.97.87:/root/
scp azure-service-install.sh root@20.189.97.87:/root/
```

## 📋 Step 3: Deploy on Azure VM

SSH to your Azure VM and run:

```bash
ssh root@20.189.97.87
cd /root

# Make scripts executable
chmod +x azure-robust-deploy.sh azure-service-install.sh

# Run deployment (sets up databases and starts backend)
./azure-robust-deploy.sh

# Install as permanent service (runs 24/7)
sudo ./azure-service-install.sh
```

## ✅ Final Result

After deployment:
- ✅ Backend runs at: `http://20.189.97.87:8002`
- ✅ Captcha works at: `http://20.189.97.87:8002/toy/user/captcha`
- ✅ Uses ONLY local Azure databases (no Railway)
- ✅ Runs continuously 24/7
- ✅ Auto-restarts if it crashes
- ✅ Auto-starts on VM reboot

## 🔧 Verification Commands

```bash
# Check service status
sudo systemctl status xiaozhi-backend

# Test API from internet
curl http://20.189.97.87:8002/toy/user/captcha

# View logs
sudo journalctl -u xiaozhi-backend -f
```

This deployment completely eliminates Railway database connections and ensures local Azure database usage only.
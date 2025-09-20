# 🚀 Simple Azure VM Deployment - Get Backend Running Now!

## Problem
- Java backend isn't running on Azure VM
- Users can't get captcha or login
- Need server running continuously 24/7

## Solution
Get your backend running in 3 simple steps!

---

## 📋 Prerequisites on Local Machine

1. **Build the JAR file first**:
   ```bash
   cd D:\Crafttech\xiaozhi-esp32-server\main\manager-api
   mvn clean package -DskipTests
   ```

2. **Upload to Azure VM**:
   ```bash
   # Upload JAR and scripts to your Azure VM
   scp xiaozhi-esp32-api.jar root@20.189.97.87:/root/
   scp quick-deploy.sh root@20.189.97.87:/root/
   scp install-service.sh root@20.189.97.87:/root/
   ```

---

## 🎯 On Azure VM - 3 Steps to Success

### Step 1: Connect to Azure VM
```bash
ssh root@20.189.97.87
cd /root
```

### Step 2: Quick Start (Get running immediately)
```bash
chmod +x quick-deploy.sh
./quick-deploy.sh
```
This will:
- ✅ Setup MySQL and Redis databases locally
- ✅ Start the Java backend immediately
- ✅ Test that everything works

### Step 3: Make it Permanent (Run 24/7)
```bash
chmod +x install-service.sh
sudo ./install-service.sh
```
This will:
- ✅ Install as system service
- ✅ Auto-start on VM reboot
- ✅ Auto-restart if it crashes

---

## 🌐 Access Your Backend

After deployment, users can access:

- **Backend API**: `http://20.189.97.87:8002`
- **Captcha Endpoint**: `http://20.189.97.87:8002/toy/user/captcha`
- **All API endpoints**: `http://20.189.97.87:8002/toy/...`

---

## 📊 Check if Everything is Working

### Test from Azure VM
```bash
# Check if service is running
sudo systemctl status xiaozhi-backend

# Test API locally
curl http://localhost:8002/toy/user/captcha

# View logs
sudo journalctl -u xiaozhi-backend -f
```

### Test from Internet
```bash
# From any computer, test external access
curl http://20.189.97.87:8002/toy/user/captcha
```

---

## 🔧 Database Configuration

Both localhost and Azure VM will use the same local Azure database:

**MySQL Database**:
- Host: `localhost:3306`
- Database: `xiaozhi_db`
- Username: `xiaozhi_user`
- Password: `xiaozhi_password123`

**Redis Cache**:
- Host: `localhost:6379`
- No password

---

## 🛠️ Management Commands

### Service Control
```bash
sudo systemctl start xiaozhi-backend     # Start
sudo systemctl stop xiaozhi-backend      # Stop
sudo systemctl restart xiaozhi-backend   # Restart
sudo systemctl status xiaozhi-backend    # Check status
```

### View Logs
```bash
sudo journalctl -u xiaozhi-backend -f    # Live logs
sudo journalctl -u xiaozhi-backend -n 50 # Last 50 lines
```

### Database Management
```bash
docker ps                               # Check containers
docker restart xiaozhi-mysql xiaozhi-redis  # Restart databases
```

---

## 🆘 Troubleshooting

### Backend Not Starting
```bash
# Check logs for errors
sudo journalctl -u xiaozhi-backend -n 100

# Check if JAR file exists
ls -la /root/xiaozhi-esp32-api.jar

# Manual test
java -jar /root/xiaozhi-esp32-api.jar --spring.profiles.active=azure
```

### Database Connection Issues
```bash
# Check if databases are running
docker ps | grep xiaozhi

# Test MySQL connection
docker exec xiaozhi-mysql mysqladmin ping

# Test Redis connection
docker exec xiaozhi-redis redis-cli ping
```

### Firewall Issues
```bash
# Check if port 8002 is open
netstat -tlnp | grep 8002

# Open firewall port (if needed)
sudo ufw allow 8002
```

---

## ✅ Success Checklist

- [ ] JAR file built successfully
- [ ] Files uploaded to Azure VM
- [ ] Quick deploy script completed without errors
- [ ] Service installed and running
- [ ] Captcha endpoint returns HTTP 200
- [ ] Service starts automatically after VM reboot
- [ ] Users can access from internet

---

## 🎯 Final Result

After following these steps:

✅ **Backend runs continuously** on Azure VM
✅ **Auto-restarts** if it crashes
✅ **Auto-starts** when VM reboots
✅ **Users can access 24/7** at `http://20.189.97.87:8002`
✅ **Local Azure database** - no external dependencies
✅ **Same database** for both localhost and Azure VM

Your users will be able to get captcha and login successfully!
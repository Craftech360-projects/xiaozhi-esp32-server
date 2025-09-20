# 🚀 Xiaozhi ESP32 Server - Pipeline Guide

## 📊 Pipeline Identification Dashboard

### 🧪 **TESTING PIPELINE** (`testing-config.yml`)
**Dashboard Identifier**: `[TEST]` prefix on all jobs
**Workflow Name**: `test-pipeline-xiaozhi-qa`

| **Attribute** | **Value** |
|---------------|-----------|
| **Pipeline Type** | 🧪 Testing & Quality Assurance |
| **Triggers** | **ALL BRANCHES** (including feature branches) |
| **Purpose** | Code quality, testing, security scanning |
| **First Job** | `[TEST] 🧪 Pipeline Type Notification` |
| **Job Count** | ~15 comprehensive testing jobs |
| **Context** | `azure-mqtt-gateway` |

**Visual Identification**:
- 🧪 Emoji in job names
- `[TEST]` prefix on all jobs
- Workflow name contains `test-pipeline`
- Runs on every branch push

---

### 🚀 **PRODUCTION PIPELINE** (`config.yml`)
**Dashboard Identifier**: `[PROD]` prefix on all jobs
**Workflow Name**: `prod-pipeline-xiaozhi-deployment`

| **Attribute** | **Value** |
|---------------|-----------|
| **Pipeline Type** | 🚀 Production Deployment |
| **Triggers** | **DEV BRANCH ONLY** |
| **Purpose** | Build, test, security scan, and deploy to production |
| **First Job** | `[PROD] 🚀 Pipeline Type Notification` |
| **Job Count** | ~25 build, test, and deployment jobs |
| **Context** | `azure-mqtt-gateway` |

**Visual Identification**:
- 🚀 Emoji in job names
- `[PROD]` prefix on all jobs
- Workflow name contains `prod-pipeline`
- Only runs on `dev` branch

---

## 🎯 Quick Pipeline Recognition

### **In CircleCI Dashboard:**

#### Testing Pipeline (All Branches):
```
Workflow: test-pipeline-xiaozhi-qa
├── [TEST] 🧪 Pipeline Type Notification
├── [TEST] Quality Gate Check
├── [TEST] Code Redundancy Analysis
├── [TEST] Dependency Security Scan
├── [TEST] MQTT Gateway - Comprehensive
├── [TEST] Manager API - Comprehensive
├── [TEST] Manager Web - Comprehensive
├── [TEST] LiveKit Server - Comprehensive
├── [TEST] Integration & E2E Testing
├── [TEST] Performance & Load Testing
└── [TEST] Deploy to Test Environment
```

#### Production Pipeline (Dev Branch Only):
```
Workflow: prod-pipeline-xiaozhi-deployment
├── [PROD] 🚀 Pipeline Type Notification
├── [PROD] Build MQTT Gateway
├── [PROD] Build Manager API
├── [PROD] Build Manager Web
├── [PROD] Build LiveKit Server
├── [PROD] Test MQTT Gateway
├── [PROD] Test Manager API
├── [PROD] Test Manager Web
├── [PROD] Test LiveKit Server
├── Security Scans...
└── Deploy to Azure (Staging/Production)
```

---

## 📋 Pipeline Comparison

| **Feature** | **Testing Pipeline** | **Production Pipeline** |
|-------------|---------------------|-------------------------|
| **Branch Trigger** | All branches | `dev` branch only |
| **Focus** | Quality Assurance | Deployment |
| **Job Duration** | Comprehensive testing | Fast deployment |
| **Environment** | Test environments | Production Azure |
| **Security** | Deep vulnerability analysis | Standard security checks |
| **Performance** | Load testing & profiling | Basic smoke tests |
| **Code Quality** | Extensive analysis | Build verification |
| **Deployment** | Test environment only | Full production deployment |

---

## 🔍 Pipeline Logs Identification

### **Testing Pipeline Logs Start With:**
```
==================================================
🧪 XIAOZHI TESTING & QUALITY ASSURANCE PIPELINE
==================================================
📊 PIPELINE METADATA:
  • Pipeline Type: TESTING & QUALITY ASSURANCE
  • Trigger: ALL BRANCHES
  • Purpose: Code quality, testing, security scanning
```

### **Production Pipeline Logs Start With:**
```
==================================================
🚀 XIAOZHI PRODUCTION DEPLOYMENT PIPELINE
==================================================
📊 PIPELINE METADATA:
  • Pipeline Type: PRODUCTION DEPLOYMENT
  • Trigger: DEV BRANCH ONLY
  • Purpose: Build, test, security scan, and deploy
```

---

## 🎯 When Each Pipeline Runs

### **Testing Pipeline Triggers:**
- ✅ Feature branch pushes (`feature/new-feature`)
- ✅ Bugfix branch pushes (`bugfix/fix-issue`)
- ✅ Hotfix branch pushes (`hotfix/urgent-fix`)
- ✅ Any custom branch (`your-branch-name`)
- ✅ Pull request branches
- ❌ **Does NOT deploy to production**

### **Production Pipeline Triggers:**
- ✅ `dev` branch pushes only
- ✅ Deploys to Azure production environment
- ❌ Does not run on feature branches

---

## 🛠️ Configuration Files

| **File** | **Purpose** | **Status** |
|----------|-------------|------------|
| `.circleci/config.yml` | Production deployment pipeline | Active for `dev` branch |
| `.circleci/testing-config.yml` | Testing pipeline for all branches | Ready to activate |
| `.circleci/README.md` | Complete documentation | Reference guide |
| `.circleci/validate-pipeline.sh` | Validation script | Validation tool |
| `.circleci/PIPELINE-GUIDE.md` | This identification guide | Dashboard reference |

---

## 🚀 Activation Instructions

### **Option 1: Use Testing Pipeline as Primary**
```bash
# Backup current production config
mv .circleci/config.yml .circleci/production-config.yml

# Activate testing pipeline
mv .circleci/testing-config.yml .circleci/config.yml
```

### **Option 2: Use Both Pipelines (Recommended)**
Keep both pipelines and use CircleCI's conditional logic to choose which runs based on branch.

### **Option 3: Manual Selection**
Switch between configs manually based on your needs.

---

## 🔧 Environment Variables

Both pipelines use the same CircleCI context: `azure-mqtt-gateway`

**Required Variables:**
- `AZURE_HOST` - Azure VM hostname
- `AZURE_USER` - SSH username
- `AZURE_DEPLOY_PATH` - Deployment path

---

## 📱 Notifications & Alerts

### **Testing Pipeline Alerts:**
- 🧪 Quality gate failures
- 🚨 Security vulnerabilities found
- ⚠️ Performance degradation
- 📊 Test coverage drops

### **Production Pipeline Alerts:**
- 🚀 Deployment failures
- 🔴 Service health check failures
- ⚡ Build failures
- 🌐 Azure deployment issues

---

## ✅ Quick Validation

Run the validation script to check your setup:
```bash
.circleci/validate-pipeline.sh
```

This will verify:
- ✅ Pipeline configurations are valid
- ✅ Required services are present
- ✅ Environment variables are set
- ✅ Dependencies are available

---

**💡 Pro Tip**: Look for the first job in each workflow - it will clearly identify which pipeline type is running with a detailed notification including branch, commit, and pipeline purpose.
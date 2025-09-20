# LiveKit Server Pipeline Integration Test

This file is created to test the integration of livekit-server into the unified CircleCI pipeline.

## Test Details
- **Date**: 2025-09-17
- **Purpose**: Verify livekit-server is properly integrated into the 4-service unified pipeline
- **Expected**: All 4 services (mqtt-gateway, manager-api, manager-web, livekit-server) should build, test, and deploy

## Test Status
✅ Pipeline should trigger automatically when this file is committed

## Services in Unified Pipeline
1. **MQTT Gateway** - Node.js MQTT protocol service on port 1884/8001/8884
2. **Manager API** - Spring Boot backend on port 8002
3. **Manager Web** - Vue.js frontend on port 8885/8886
4. **LiveKit Server** - Python LiveKit agent service on port 8887/8888

## Pipeline Phases
1. **Phase 1: Build** - All 4 services build in parallel
2. **Phase 2: Test** - All 4 services test in parallel
3. **Phase 3: Security** - All 4 services scanned with Trivy in parallel
4. **Phase 4: Deploy** - All 4 services deployed to Azure VM with PM2

## Deployment Environments
- **Development** (all branches except develop/main): ports 8001, 8002, 8886, 8888
- **Staging** (develop branch): ports 8884, 8002, 8885, 8887
- **Production** (main branch): ports 8884, 8002, 8885, 8887

---
*Generated for CircleCI unified 4-service pipeline testing*
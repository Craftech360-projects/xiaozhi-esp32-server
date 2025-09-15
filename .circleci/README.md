# CircleCI Configuration for XiaoZhi ESP32 Server

This CircleCI configuration automatically builds, tests, and deploys three Docker images for the XiaoZhi ESP32 Server project.

## Docker Images Built

1. **XiaoZhi Server** (`xiaozhi/xiaozhi-server`) - Python-based voice processing server
2. **Manager API** (`xiaozhi/manager-api`) - Java Spring Boot REST API
3. **Manager Web** (`xiaozhi/manager-web`) - Combined Vue.js frontend + Java backend

## Workflow Overview

### Build and Deploy Workflow

1. **Parallel Builds**: All three Docker images are built simultaneously for efficiency
2. **Security Scanning**: Images are scanned for vulnerabilities using Trivy
3. **Staging Deployment**: Automatic deployment to staging environment (develop branch)
4. **Production Deployment**: Manual approval required for production deployment (main branch)

### Nightly Security Scan

- Runs daily at 2 AM to check for new vulnerabilities in production images

## Setup Requirements

### 1. CircleCI Project Setup

1. Connect your GitHub repository to CircleCI
2. Set up the following contexts in CircleCI:

#### Context: `docker-hub-creds`
```
DOCKER_USERNAME: Your Docker Hub username
DOCKER_PASSWORD: Your Docker Hub password/token
```

#### Context: `staging-deploy`
```
DEPLOY_ENV: staging
KUBECONFIG: (if using Kubernetes)
STAGING_API_KEY: (deployment API key)
```

#### Context: `production-deploy`
```
DEPLOY_ENV: production
KUBECONFIG: (if using Kubernetes)
PRODUCTION_API_KEY: (deployment API key)
```

### 2. Branch Strategy

The pipeline is configured to work with the following branches:

- **`main`**: Production deployments (manual approval required)
- **`develop`**: Automatic staging deployments
- **`feature/*`**: Build and test only
- **`hotfix/*`**: Build and test only

## Docker Image Tagging Strategy

- **Latest**: `latest` tag for main branch builds
- **Branch**: `{branch-name}-{commit-sha}` for feature/develop branches
- **Commit**: Always tagged with short commit SHA (`{commit-sha}`)

## Security Features

### Vulnerability Scanning

- Uses Trivy scanner for container vulnerability assessment
- Scans for HIGH and CRITICAL vulnerabilities
- Fails build if critical vulnerabilities are found

### Security Best Practices

- Multi-stage builds to reduce image size
- Non-root user execution
- Minimal base images
- Layer caching optimization

## Deployment Customization

The deployment job is currently a placeholder. Customize the `deploy` job based on your deployment strategy:

### Kubernetes Deployment Example

```yaml
- run:
    name: Deploy to Kubernetes
    command: |
      kubectl config use-context ${DEPLOY_ENV}
      kubectl set image deployment/xiaozhi-server xiaozhi-server=$SERVER_IMAGE
      kubectl set image deployment/manager-api manager-api=$API_IMAGE
      kubectl set image deployment/manager-web manager-web=$WEB_IMAGE
      kubectl rollout status deployment/xiaozhi-server
      kubectl rollout status deployment/manager-api
      kubectl rollout status deployment/manager-web
```

### Docker Compose Deployment Example

```yaml
- run:
    name: Deploy with Docker Compose
    command: |
      export XIAOZHI_SERVER_IMAGE=$SERVER_IMAGE
      export MANAGER_API_IMAGE=$API_IMAGE
      export MANAGER_WEB_IMAGE=$WEB_IMAGE
      docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring and Notifications

Add notification steps to your jobs:

### Slack Notifications

```yaml
- slack/notify:
    event: fail
    template: basic_fail_1
- slack/notify:
    event: pass
    template: success_tagged_deploy_1
```

### Email Notifications

Configure in CircleCI project settings under "Email Notifications"

## Performance Optimization

### Current Optimizations

- **Docker Layer Caching**: Enabled for faster builds
- **Parallel Builds**: All images build simultaneously
- **Workspace Persistence**: Share artifacts between jobs
- **Large Resource Class**: Use more powerful executors

### Additional Optimizations

1. **Multi-arch Builds**: Add ARM64 support
```yaml
- run:
    name: Build Multi-arch Image
    command: |
      docker buildx build --platform linux/amd64,linux/arm64 \
        -t xiaozhi/xiaozhi-server:${TAG} --push .
```

2. **Build Caching**: Use external cache
```yaml
- run:
    name: Build with Cache
    command: |
      docker build --cache-from xiaozhi/xiaozhi-server:cache \
        -t xiaozhi/xiaozhi-server:${TAG} .
```

## Troubleshooting

### Common Issues

1. **Docker Build Failures**
   - Check Dockerfile syntax
   - Verify all COPY paths exist
   - Check for dependency conflicts

2. **Authentication Failures**
   - Verify Docker Hub credentials in context
   - Check token permissions

3. **Security Scan Failures**
   - Update base images
   - Review vulnerability reports
   - Apply security patches

### Debugging Commands

```bash
# Check image contents
docker run --rm -it xiaozhi/xiaozhi-server:latest sh

# Scan specific image locally
trivy image xiaozhi/xiaozhi-server:latest

# Test deployment locally
docker-compose -f docker-compose.yml up -d
```

## CI/CD Metrics

The pipeline provides the following metrics:

- **Build Time**: Total time for all three images
- **Image Size**: Final compressed image sizes
- **Vulnerability Count**: Number of security issues found
- **Deployment Status**: Success/failure of deployments

## Contributing

When making changes to the CI/CD pipeline:

1. Test changes in a feature branch first
2. Update this documentation
3. Verify all contexts and secrets are properly configured
4. Test the complete pipeline flow

## Support

For issues with the CI/CD pipeline:

1. Check CircleCI build logs
2. Review this documentation
3. Verify all required secrets are configured
4. Contact the DevOps team for deployment issues
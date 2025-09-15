module.exports = {
  apps: [
    {
      name: 'manager-api',
      script: 'java',
      args: '-jar target/xiaozhi-esp32-api.jar',
      cwd: 'D:/Crafttech/xiaozhi-esp32-server/main/manager-api',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        NODE_ENV: 'development',
        SPRING_PROFILES_ACTIVE: 'dev',
        SERVER_PORT: 8080
      },
      env_staging: {
        NODE_ENV: 'staging',
        SPRING_PROFILES_ACTIVE: 'staging',
        SERVER_PORT: 8080
      },
      env_production: {
        NODE_ENV: 'production',
        SPRING_PROFILES_ACTIVE: 'prod',
        SERVER_PORT: 8080
      },
      error_file: './logs/manager-api-error.log',
      out_file: './logs/manager-api-out.log',
      log_file: './logs/manager-api-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
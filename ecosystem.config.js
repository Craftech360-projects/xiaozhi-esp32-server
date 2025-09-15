module.exports = {
  apps: [
    {
      name: "manager-api",
      script: "java",
      args: "-jar target/xiaozhi-esp32-api.jar",
      cwd: "/opt/xiaozhi-esp32-server/main/manager-api",
      interpreter: "none",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        NODE_ENV: 'development',
        SPRING_PROFILES_ACTIVE: 'dev'
      },
      env_staging: {
        NODE_ENV: 'staging',
        SPRING_PROFILES_ACTIVE: 'staging'
      },
      env_production: {
        NODE_ENV: 'production',
        SPRING_PROFILES_ACTIVE: 'prod'
      },
      error_file: '/var/log/pm2/manager-api-error.log',
      out_file: '/var/log/pm2/manager-api-out.log',
      log_file: '/var/log/pm2/manager-api-combined.log',
      time: true
    },
    {
      name: "manager-web",
      script: "serve",
      args: "-s dist -l 8080",
      cwd: "/opt/xiaozhi-esp32-server/main/manager-web",
      interpreter: "none",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        NODE_ENV: 'development'
      },
      env_staging: {
        NODE_ENV: 'staging'
      },
      env_production: {
        NODE_ENV: 'production'
      },
      error_file: '/var/log/pm2/manager-web-error.log',
      out_file: '/var/log/pm2/manager-web-out.log',
      log_file: '/var/log/pm2/manager-web-combined.log',
      time: true
    },
    {
      name: "mqtt-gateway",
      script: "app.js",
      cwd: "/opt/xiaozhi-esp32-server/main/mqtt-gateway",
      interpreter: "node",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'development',
        MQTT_PORT: 1883,
        HTTP_PORT: 8884
      },
      env_staging: {
        NODE_ENV: 'staging',
        MQTT_PORT: 1883,
        HTTP_PORT: 8884
      },
      env_production: {
        NODE_ENV: 'production',
        MQTT_PORT: 1883,
        HTTP_PORT: 8884
      },
      error_file: '/var/log/pm2/mqtt-gateway-error.log',
      out_file: '/var/log/pm2/mqtt-gateway-out.log',
      log_file: '/var/log/pm2/mqtt-gateway-combined.log',
      time: true
    }
  ]
};


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
        SPRING_PROFILES_ACTIVE: 'dev',
        SERVER_PORT: 8080,
        JAVA_OPTS: '-Xms512m -Xmx2g'
      },
      env_staging: {
        NODE_ENV: 'staging',
        SPRING_PROFILES_ACTIVE: 'staging',
        SERVER_PORT: 8080,
        JAVA_OPTS: '-Xms512m -Xmx2g'
      },
      env_production: {
        NODE_ENV: 'production',
        SPRING_PROFILES_ACTIVE: 'prod',
        SERVER_PORT: 8080,
        JAVA_OPTS: '-Xms1g -Xmx2g'
      },
      error_file: '/var/log/pm2/manager-api-error.log',
      out_file: '/var/log/pm2/manager-api-out.log',
      log_file: '/var/log/pm2/manager-api-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: "manager-web",
      script: "serve",
      args: "-s dist -l 8081",
      cwd: "/opt/xiaozhi-esp32-server/main/manager-web",
      interpreter: "none",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        NODE_ENV: 'development',
        PORT: 8081
      },
      env_staging: {
        NODE_ENV: 'staging',
        PORT: 8081
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 8081
      },
      error_file: '/var/log/pm2/manager-web-error.log',
      out_file: '/var/log/pm2/manager-web-out.log',
      log_file: '/var/log/pm2/manager-web-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
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
        HTTP_PORT: 8884,
        DEBUG: ''
      },
      env_staging: {
        NODE_ENV: 'staging',
        MQTT_PORT: 1883,
        HTTP_PORT: 8884,
        DEBUG: ''
      },
      env_production: {
        NODE_ENV: 'production',
        MQTT_PORT: 1883,
        HTTP_PORT: 8884,
        DEBUG: ''
      },
      error_file: '/var/log/pm2/mqtt-gateway-error.log',
      out_file: '/var/log/pm2/mqtt-gateway-out.log',
      log_file: '/var/log/pm2/mqtt-gateway-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};


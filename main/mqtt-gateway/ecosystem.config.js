module.exports = {
  apps: [
    {
      name: 'mqtt-gateway',
      script: './app.js',
      cwd: '/opt/xiaozhi-esp32-server/main/mqtt-gateway',
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

module.exports = {
  apps: [
    {
      name: 'mqtt-gateway',
      script: './app.js',
      cwd: 'D:/Crafttech/xiaozhi-esp32-server/main/mqtt-gateway',
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
      error_file: './logs/mqtt-gateway-error.log',
      out_file: './logs/mqtt-gateway-out.log',
      log_file: './logs/mqtt-gateway-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};

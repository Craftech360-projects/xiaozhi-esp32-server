module.exports = {
  apps: [
    {
      name: 'manager-web',
      script: 'serve',
      args: '-s dist -l 8080',
      cwd: 'D:/Crafttech/xiaozhi-esp32-server/main/manager-web',
      interpreter: 'none',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        NODE_ENV: 'development',
        PORT: 8080
      },
      env_staging: {
        NODE_ENV: 'staging',
        PORT: 8080
      },
      env_production: {
        NODE_ENV: 'production',
        PORT: 8080
      },
      error_file: './logs/manager-web-error.log',
      out_file: './logs/manager-web-out.log',
      log_file: './logs/manager-web-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
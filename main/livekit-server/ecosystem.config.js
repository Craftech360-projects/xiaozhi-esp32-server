module.exports = {
  apps: [{
    name: 'livekit-server',
    script: 'uv',
    args: 'run python main.py dev',
    cwd: '/root/xiaozhi-esp32-server/main/livekit-server',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'development'
    },
    env_production: {
      NODE_ENV: 'production'
    },
    log_file: './logs/livekit-server.log',
    error_file: './logs/livekit-server-error.log',
    out_file: './logs/livekit-server-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};
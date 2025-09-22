module.exports = {
  apps: [
    {
      name: "manager-api",
      script: "mvn",
      args: 'spring-boot:run "-Dspring-boot.run.arguments=--spring.profiles.active=dev"',
      cwd: "/root/xiaozhi-esp32-server/main/manager-api",
      interpreter: "none",
      env: {
        JAVA_HOME: "/usr/lib/jvm/java-21-openjdk-amd64",
        MAVEN_HOME: "/usr/share/maven"
      },
      max_memory_restart: "2G",
      restart_delay: 5000,
      autorestart: true,
      watch: false
    },
    {
      name: "livekit-agent",
      script: "/root/.local/bin/uv",
      args: "run python main.py dev",
      cwd: "/root/xiaozhi-esp32-server/main/livekit-server",
      interpreter: "none",
      env: {
        PATH: "/root/.local/bin:" + process.env.PATH
      },
      max_memory_restart: "2G",
      restart_delay: 10000,
      autorestart: true,
      watch: false
    },
    {
      name: "manager-web",
      script: "npm",
      args: "run serve",
      cwd: "/root/xiaozhi-esp32-server/main/manager-web",
      interpreter: "none",
      env: {
        NODE_ENV: "development"
      },
      max_memory_restart: "1G",
      restart_delay: 3000,
      autorestart: true,
      watch: false
    },
    {
      name: "mqtt-gateway",
      script: "app.js",
      cwd: "/root/xiaozhi-esp32-server/main/mqtt-gateway",
      interpreter: "node",
      env: {
        NODE_ENV: "production"
      },
      max_memory_restart: "512M",
      restart_delay: 3000,
      autorestart: true,
      watch: false
    }
  ]
};


module.exports = {
  apps: [
    {
      name: "manager-api",
      script: "mvn",
      args: "spring-boot:run -Dspring-boot.run.profiles=dev",
      cwd: "/root/xiaozhi-esp32-server/main/manager-api",
      interpreter: "none"
    },
    {
      name: "manager-web",
      script: "npm",
      args: "run serve",
      cwd: "/root/xiaozhi-esp32-server/main/manager-web",
      interpreter: "none"
    },
    {
      name: "mqtt-gateway",
      script: "app.js",
      cwd: "/root/xiaozhi-esp32-server/main/mqtt-gateway",
      interpreter: "node",
      watch: true
    },
    {
      name: "livekit-server",
      script: "python",
      args: "main.py dev",
      cwd: "/root/xiaozhi-esp32-server/main/livekit-server",
      interpreter: "none"
    }
  ]
};


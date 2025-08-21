This is a development documentation. For deployment instructions, [click here to view the deployment guide](../../README.md#deployment-documentation)

# Project Introduction

manager-api is a project based on the SpringBoot framework.

When importing the project in your code editor, select the `manager-api` folder as the project directory.

# Development Environment

JDK 21

Maven 3.8+

MySQL 8.0+

Redis 5.0+

Vue 3.x

# API Documentation

After startup, open: http://localhost:8002/xiaozhi/doc.html

# How to Run

## Prerequisites

- JDK 17+ (JDK 21 recommended)

- Maven 3.8+

- MySQL 8.0+ (configure in application.yml)

- Redis 5.0+ (configure in application.yml)

## Running Steps

1. Navigate to the project directory:

```bash

cd /mnt/d/cheekofinal/xiaozhi-esp32-server/main/manager-api

```

2. Build the project:

```bash

mvn clean install

```

3. Run the application:

```bash

mvn spring-boot:run

```

Or run the JAR file after building:

```bash

java -jar target/xiaozhi-esp32-api-0.0.1.jar

```

The API will start on port 8002 with context path `/xiaozhi`. Once running, you can access the API documentation at:

http://localhost:8002/xiaozhi/doc.html
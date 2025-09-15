# =========================
# Stage 1: Build (Maven)
# =========================
FROM maven:3.9-eclipse-temurin-17-alpine AS build

WORKDIR /app

# Copy only the pom first to leverage layer caching
COPY pom.xml ./
RUN --mount=type=cache,target=/root/.m2 \
    mvn -B -q dependency:go-offline

# Copy sources and build
COPY src ./src
# If you use Lombok, ensure pom has annotationProcessorPaths configured
RUN --mount=type=cache,target=/root/.m2 \
    mvn -B -q clean package -DskipTests

# =========================
# Stage 2: Runtime (JRE)
# =========================
FROM eclipse-temurin:17-jre-alpine AS runtime
# (You can keep openjdk:17-jre-alpine if you prefer; Temurin tends to be slimmer & well maintained)

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user
RUN addgroup -g 1001 -S appgroup \
    && adduser  -S appuser -G appgroup -u 1001

WORKDIR /app

# Copy the built jar (adjust name if your artifactId/version differs)
# You can also set this with a build arg if you like
COPY --from=build /app/target/xiaozhi-esp32-api-*.jar /app/app.jar
RUN chown -R appuser:appgroup /app

USER appuser

# Ports & env
EXPOSE 8002

# Prefer JAVA_TOOL_OPTIONS so JVM auto-picks it up (no shell wrapper)
# Tweak memory as needed; these are safe defaults for most services
ENV JAVA_TOOL_OPTIONS="-Xms256m -Xmx512m"
ENV SPRING_PROFILES_ACTIVE=prod

# Healthcheck (your app appears to be under /toy)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8002/toy/actuator/health || exit 1

# Run app (exec form; no shell)
ENTRYPOINT ["java","-jar","/app/app.jar"]

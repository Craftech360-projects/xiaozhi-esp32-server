# Dockerfile for LiveKit Server Simple on Cerebrium
# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11.6
FROM python:${PYTHON_VERSION}-slim

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Create a non-privileged user that the app will run under.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Install system dependencies for audio processing and compilation
RUN apt-get update && \
    apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libasound2-dev \
    portaudio19-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

USER appuser

RUN mkdir -p /home/appuser/.cache
RUN chown -R appuser /home/appuser/.cache

WORKDIR /home/appuser

# Copy requirements and install Python dependencies
COPY simple_requirements.txt .
RUN python -m pip install --user --no-cache-dir -r simple_requirements.txt

# Copy the entire application
COPY . .

# Ensure that any dependent models are downloaded at build-time
RUN python simple_main.py download-files || echo "No download-files command available"

# Expose healthcheck port
EXPOSE 8081

# Run the application
CMD ["python", "simple_main.py", "start"]
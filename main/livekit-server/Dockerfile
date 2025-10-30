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
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create directories and set ownership BEFORE switching to appuser
RUN mkdir -p /home/appuser/.cache /home/appuser/model_cache/funasr && \
    chown -R appuser:appuser /home/appuser/.cache /home/appuser/model_cache

USER appuser

WORKDIR /home/appuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python -m pip install --user --no-cache-dir -r requirements.txt

# Copy pyproject.toml and install its dependencies
COPY pyproject.toml .
RUN python -m pip install --user --no-cache-dir \
    'livekit-agents[openai,turn-detector,silero,cartesia,deepgram]~=1.2' \
    'livekit-plugins-noise-cancellation~=0.2' \
    'livekit-plugins-groq' \
    'livekit.plugins.deepgram' \
    'livekit-plugins-elevenlabs' \
    'python-dotenv' \
    'paho-mqtt' \
    'aiohttp' \
    'pydub' \
    'edge-tts' \
    'gtts' \
    'pyttsx3' \
    'mem0ai' \
    'jinja2' \
    'pytz' \
    'qdrant-client>=1.7.0' \
    'sentence-transformers>=2.2.0' \
    'funasr' \
    'modelscope' \
    'onnxruntime' \
    'psutil' \
    'psutil' \
    'datadog-api-client' \
    'ddtrace' \
    'torchaudio'
# Copy the entire application
COPY . .

# Download FunASR model at build-time using the download script
RUN python scripts/download_funasr_model.py

# Ensure that any dependent models are downloaded at build-time
RUN python main.py download-files || echo "No download-files command available"

# Expose healthcheck port
EXPOSE 8081

# Run the application
CMD ["python", "main.py", "start"]
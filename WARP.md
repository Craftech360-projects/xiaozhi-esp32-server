# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

`xiaozhi-esp32-server` is a multi-service backend for the Xiaozhi ESP32 voice assistant ecosystem. It provides:

- A Python real-time AI server (`xiaozhi-server`) handling WebSocket audio, ASR, LLM, TTS, VAD, plugins, and OTA.
- A Java Spring Boot management API (`manager-api`) with MySQL + Redis for configuration, users, devices, and model settings.
- A Vue.js web console (`manager-web`) for configuring models, devices, and system parameters.
- An MQTT/UDP ↔ WebSocket gateway (`main/mqtt-gateway`) bridging ESP32 devices and the Python server.
- A LiveKit-based voice agent (`main/livekit-server`) built on the LiveKit Agents Python starter.
- Optional remote services: Whisper STT (`main/remote-whisper-server`) and Piper TTS (`main/remote-piper-server`).

Core ports (default, when running all modules):

- `xiaozhi-server` (Python AI engine): WebSocket on `8000` (path `/xiaozhi/v1/`), OTA HTTP on `8002/xiaozhi/ota/` when using docker full stack.
- `manager-api` (Java): HTTP on `8002` (context path `/toy` or `/xiaozhi` depending on deployment).
- `manager-web` (Vue console): proxied behind `manager-api` in Docker, or `npm run serve` in dev.

## High-Level Architecture

### 1. Core Voice Pipeline (`main/xiaozhi-server`)

- Entry point is `app.py` in `main/xiaozhi-server`.
- ESP32 clients connect via WebSocket (e.g. `ws://<host>:8000/xiaozhi/v1/`).
- Audio flow:
  - ESP32 streams audio frames (typically Opus/PCM) over WebSocket.
  - `receiveAudioHandle.py` runs VAD (e.g. Silero/TenVAD) to segment speech.
  - Segmented audio chunks are passed to an ASR provider (local FunASR or remote APIs) via the provider pattern under `core/providers/asr/`.
  - Recognized text, along with conversation history from memory providers, is fed to an LLM provider under `core/providers/llm/`.
  - If the LLM emits function calls, `core/handle/functionHandler.py` invokes plugin functions in `plugins_func/` (e.g. Home Assistant, tools, MCP endpoints) and returns results back to the LLM.
  - Final text replies go through TTS providers (`core/providers/tts/`) to synthesize audio.
  - TTS audio is streamed back to the device via WebSocket, with synchronized control messages like `tts start/sentence_start/stop`.
- Configuration is layered:
  - Base config in `main/xiaozhi-server/config.yaml`.
  - Per-deployment overrides in `main/xiaozhi-server/data/.config.yaml`.
  - When full stack is enabled, `manager-api` is the source of truth; `xiaozhi-server` fetches config via HTTP (`manager-api.url` + `manager-api.secret` in `.config.yaml`).
- Plugins & tools:
  - `plugins_func/` defines callable tools the LLM can trigger via function calling.
  - MQTT gateway integration is documented in `main/xiaozhi-server/docs/mqtt-gateway-message-flow.md` (see below).

### 2. Management Backend (`main/manager-api`)

- Spring Boot service (`JDK 21`, Maven) exposing REST APIs for:
  - Users, auth, roles/permissions (Apache Shiro).
  - Devices and device configuration.
  - Model/TTS/VAD/ASR/intent/memory configuration and keys.
  - OTA metadata and timbre/voice management.
- Persistence:
  - MySQL for long-term data (via MyBatis-Plus).
  - Redis for caching and session/state.
- Configuration profiles:
  - `src/main/resources/application.yml` base config.
  - `application-dev.yml` for local dev (ports, DB, Redis, etc.).
  - `application-prod.yml` for production.
- DB schema managed with Liquibase; migrations run on startup.
- API documentation exposed at `http://localhost:8002/toy/doc.html` (or `/xiaozhi/doc.html` depending on context path).

### 3. Web Console (`main/manager-web`)

- Vue 2 SPA built with Vue CLI.
- Uses Vue Router + Vuex + Element UI.
- Talks to `manager-api` via HTTP (Flyio/Axios wrappers in `src/apis/`).
- Primary responsibilities:
  - Configure LLM/ASR/TTS/VAD/memory providers and their API keys.
  - Manage ESP32 devices and associate them with users/kids.
  - Configure server URLs like `server.websocket` and `server.ota` used by `xiaozhi-server` and ESP32 firmware.
- In Docker full-stack deployment, served behind the same endpoint as `manager-api` (e.g. `http://localhost:8002/xiaozhi`).

### 4. MQTT Gateway (`main/mqtt-gateway`)

- Node.js service bridging between:
  - MQTT (control messages) and UDP (audio) on the device side.
  - WebSocket on the `xiaozhi-server` side.
- Typical flow (see `main/xiaozhi-server/docs/mqtt-gateway-message-flow.md` and `main/mqtt-gateway/README.md`):
  - Client publishes control messages to `device-server` topic.
  - Gateway maintains WebSocket connection(s) to `xiaozhi-server`.
  - Gateway publishes server responses to per-device MQTT topics (e.g. `devices/p2p/{mac_address}`).
  - Audio is streamed via encrypted UDP (AES-128-CTR), with session-specific keys and nonces returned in a `hello` response.
- Core pieces:
  - `app.js` — main entry and protocol routing.
  - `mqtt-protocol.js` — MQTT message handling and session lifecycle.
  - `config/mqtt.json` — environment-specific endpoints and allowed MACs.

### 5. LiveKit Agent (`main/livekit-server`)

- Based on the LiveKit Agents Python starter (`agent-starter-python`).
- Project structure:
  - `main.py` — organized entrypoint, recommended for dev/prod.
  - `src/agent/main_agent.py` — main agent class (assistant behavior + tools).
  - `src/config/config_loader.py` — environment-based config.
  - `src/providers/provider_factory.py` — central factory for LLM/STT/TTS/VAD providers.
  - `src/handlers/chat_logger.py` — event handlers and logging.
  - `src/utils/helpers.py` — usage tracking and utilities.
- Uses `uv` for environment management and `pytest` + `ruff` for tests/linting (see `pyproject.toml`).

### 6. Remote Whisper & Piper Servers

- `main/remote-whisper-server`:
  - Standalone HTTP server for Whisper STT (Python).
  - Exposes `/health`, `/transcribe`, and `/info` endpoints.
  - Designed to be called from `xiaozhi-server` as an external ASR provider.
- `main/remote-piper-server`:
  - Standalone HTTP server for Piper TTS.
  - Exposes `/health`, `/synthesize`, and `/info` endpoints.
  - Used as an external TTS provider.

### 7. Kid Profile Flow & Manager Integration

Kid profile APIs and tests are described in `TESTING_GUIDE.md` and `TEST_SCRIPTS_README.md`:

- `manager-api` exposes:
  - `/toy/user/login` and `/toy/user/login` for auth.
  - `/toy/api/mobile/kids/create` for kid profile creation.
  - `/toy/device/assign-kid-by-mac` to assign a kid to a device.
  - `/toy/config/child-profile-by-mac` to retrieve kid profile (used by LiveKit/xiaozhi-server for personalized prompts).
- Python scripts on the Python side (root of repo) exercise this fully via HTTP, not SQL.

## Common Commands

Below are concrete commands taken from the repo docs/configs. Paths are relative to the repo root (`xiaozhi-esp32-server`). Use PowerShell (`pwsh`) on Windows or a POSIX shell on Linux/macOS as appropriate.

### 1. Core Python Server (`main/xiaozhi-server`)

**Conda-based environment setup (local source, server-only mode)** — from `docs/Deployment.md`:

```bash
# Create / reset conda env
conda remove -n xiaozhi-esp32-server --all -y
conda create -n xiaozhi-esp32-server python=3.10 -y
conda activate xiaozhi-esp32-server

# Add Tsinghua mirrors (optional, China mirror example)
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge

# System libs needed by audio stack
conda install libopus -y
conda install ffmpeg -y
```

Install Python dependencies:

```bash
cd main/xiaozhi-server
conda activate xiaozhi-esp32-server
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt
```

Run the server locally (source mode):

```bash
cd main/xiaozhi-server
conda activate xiaozhi-esp32-server
python app.py
```

**Docker (server-only)** — from `docs/Deployment.md`:

```bash
# In your external deployment directory containing docker-compose.yml
docker-compose up -d

# Tail logs for the server container
docker logs -f xiaozhi-esp32-server
```

**Docker (full stack: server + manager-api + manager-web + DB/Redis)** — from `docs/Deployment_all.md`:

```bash
# In your external deployment directory containing docker-compose_all.yml
docker compose -f docker-compose_all.yml up -d

# Console (web + API) logs
docker logs -f xiaozhi-esp32-server-web

# Restart Python server after updating manager-api secret/config
docker restart xiaozhi-esp32-server
docker logs -f xiaozhi-esp32-server
```

### 2. Manager API (`main/manager-api`)

Development mode (local DB/Redis via Docker) — from `main/manager-api/README.md`:

```powershell
# From main/manager-api
# Start DB + Redis + tooling
docker-compose up -d

# Run Spring Boot app with dev profile
mvn spring-boot:run "-Dspring-boot.run.arguments=--spring.profiles.active=dev"
```

Manual DB/Redis access (useful when debugging data issues):

```bash
# MySQL shell in container
docker exec -it manager-api-db mysql -u manager -p'managerpassword' manager_api

# Redis CLI
docker exec -it manager-api-redis redis-cli -a redispassword
```

Key local URLs:

- API base: `http://localhost:8002/toy`
- API docs: `http://localhost:8002/toy/doc.html`
- phpMyAdmin: `http://localhost:8080`
- Redis Commander: `http://localhost:8081`

### 3. Manager Web Console (`main/manager-web`)

From `main/manager-web/README.md` and `package.json`:

```bash
cd main/manager-web

# Install dependencies
npm install

# Development server with HMR
npm run serve

# Production build
npm run build

# Bundle analysis
npm run analyze
```

### 4. MQTT Gateway (`main/mqtt-gateway`)

From `main/mqtt-gateway/README.md`:

```bash
cd main/mqtt-gateway

# Install dependencies
npm install

# Development run
node app.js

# Debug runs
DEBUG=mqtt-server node app.js
DEBUG=* node app.js

# Production with PM2
npm install -g pm2
pm2 start ecosystem.config.js
pm2 logs xz-mqtt
pm2 monit
```

Important config:

- Copy and edit `config/mqtt.json` (from `config/mqtt.json.example`).
- `.env` defines `MQTT_PORT`, `UDP_PORT`, `PUBLIC_IP` (see README for details).

### 5. LiveKit Agent (`main/livekit-server`)

There are two parallel ways to run this project:

**Using `uv` (as in upstream LiveKit starter `README.md`):**

```bash
cd main/livekit-server

# Install dependencies to a uv-managed env
uv sync

# One-off console test
uv run python src/agent.py download-files
uv run python src/agent.py console

# Dev / prod agent entrypoints
uv run python src/agent.py dev
uv run python src/agent.py start
```

**Using the organized `main.py` wrapper (`HOW_TO_RUN.md`, recommended here):

```bash
cd main/livekit-server

# Install via requirements + editable package
pip install -r requirements.txt
pip install -e .

# Dev agent
python main.py dev

# Production agent
python main.py start
```

Environment configuration (`.env` or `.env.local`):

- LiveKit: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.
- AI providers: `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `CARTESIA_API_KEY`, or alternative providers.
- Optional: `GROQ_API_KEY` and model names (see `HOW_TO_RUN.md`).

**Tests and linting for LiveKit agent** — from `pyproject.toml` and upstream README:

```bash
cd main/livekit-server

# Run full test suite
uv run pytest

# Run a single test file
uv run pytest tests/test_your_module.py

# Run a single test case
uv run pytest tests/test_your_module.py::TestClass::test_case

# Lint with Ruff
uv run ruff check .
```

### 6. Remote Whisper STT (`main/remote-whisper-server`)

From `main/remote-whisper-server/README.md`:

```bash
cd main/remote-whisper-server

# Windows
setup.bat
start.bat

# Linux / macOS
chmod +x setup.sh
./setup.sh
./start.sh
```

Basic HTTP checks:

```bash
# Health
curl http://localhost:8000/health

# Transcription
curl -X POST http://localhost:8000/transcribe \
  -F "audio=@test.wav"
```

### 7. Remote Piper TTS (`main/remote-piper-server`)

From `main/remote-piper-server/README.md`:

```bash
cd main/remote-piper-server

# Windows
setup.bat
start.bat

# Linux / macOS
chmod +x setup.sh
./setup.sh
./start.sh
```

Sanity checks:

```bash
# Health
curl http://localhost:8001/health

# TTS
curl -X POST http://localhost:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}' \
  --output test.wav
```

### 8. Kid Profile API Test Scripts (End-to-End Checks)

From `TESTING_GUIDE.md` and `TEST_SCRIPTS_README.md`:

1. Start `manager-api` in dev mode (see section above) so it listens on `http://localhost:8002/toy`.
2. From the repo root, run the Python test scripts (they use only REST APIs, no direct SQL):

```bash
# Quick full-flow test (login → create kid → assign to device → verify)
python test_kid_profile_api.py

# Detailed interactive test
python test_kid_profile_api_complete.py

# Verify existing kid/device link
python verify_kid_device_link.py

# Manager API health check
python check_manager_api.py
```

You can adjust base URL and MAC address inside the scripts (see `TEST_SCRIPTS_README.md`).

## How Components Work Together

- **Core ESP32 voice loop:**
  - ESP32 → MQTT Gateway (MQTT control, UDP audio) → `xiaozhi-server` (WebSocket/UDP).
  - `xiaozhi-server` performs VAD → ASR → LLM (+ plugins) → TTS and streams audio back.
- **Configuration & state:**
  - `manager-web` is the human-facing console backed by `manager-api`.
  - `manager-api` persists config and serves it to `xiaozhi-server` via the `manager-api.url` and `manager-api.secret` settings in `.config.yaml`.
- **LiveKit pipeline:**
  - `main/livekit-server` implements a separate LiveKit-based agent (telephone/web/SDK clients) using similar ASR/LLM/TTS concepts.
  - It can use kid profile data (via `manager-api`) to personalize prompts and behavior.
- **Remote ASR/TTS services:**
  - `remote-whisper-server` and `remote-piper-server` can be wired into `xiaozhi-server` as external ASR/TTS providers via provider configuration.

When making changes, consider how a given module participates in these flows (e.g. adding a new LLM provider requires updating provider factories and possibly manager-api config schemas, plus UI in manager-web).

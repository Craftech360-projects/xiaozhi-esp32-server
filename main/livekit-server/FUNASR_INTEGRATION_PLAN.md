# FunASR Integration Plan for LiveKit Server (Local Mode Only)

**Date**: 2025-10-28
**Status**: Planning Phase
**Target**: Integrate Alibaba FunASR local inference into livekit-server as an STT provider
**Mode**: Local inference only (no API calls)

---

## Table of Contents

- [Overview](#overview)
- [Current Architecture Analysis](#current-architecture-analysis)
- [FunASR Implementation Analysis](#funasr-implementation-analysis)
- [Integration Strategy](#integration-strategy)
- [Implementation Plan](#implementation-plan)
- [File Structure Changes](#file-structure-changes)
- [Code Implementation](#code-implementation)
- [Configuration Changes](#configuration-changes)
- [Testing Strategy](#testing-strategy)
- [Migration Path](#migration-path)
- [Rollback Plan](#rollback-plan)

---

## Overview

### Objective

Integrate Alibaba's FunASR speech-to-text system with **local inference only** into the livekit-server architecture as an alternative STT provider alongside existing Groq and Deepgram options.

### Why FunASR Local?

**Advantages:**
- **Multilingual Support**: Chinese, English, Japanese, Korean out-of-the-box
- **Built-in VAD**: Native voice activity detection (no separate VAD needed)
- **Local Inference**: Runs completely locally - no API calls required
- **Privacy**: All audio processing stays on-device
- **Cost Savings**: Zero API costs after initial setup
- **Fast Processing**: Optimized for real-time applications
- **ITN Support**: Inverse Text Normalization (converts spoken numbers to digits)
- **Proven**: Already working in xiaozhi-server production
- **Offline Capable**: Works without internet connection

**Trade-offs:**
- **Memory**: Requires minimum 2GB RAM
- **Model Size**: ~300MB for SenseVoiceSmall (one-time download)
- **CPU Usage**: Higher CPU load during inference
- **GPU Optional**: CPU inference supported, GPU accelerates significantly
- **Initial Setup**: One-time model download required

---

## Current Architecture Analysis

### Current STT Pipeline (livekit-server)

**File**: `src/providers/provider_factory.py:31-95`

```
User Audio → Silero VAD → STT Provider → Text Transcript
                          (Groq/Deepgram - API calls)
```

**Current Implementation:**

```python
def create_stt(config, vad=None):
    stt_provider = config.get('stt_provider', 'groq')

    if stt_provider == 'groq':
        primary_stt = groq.STT(
            model=config['stt_model'],
            language=config['stt_language']
        )
    elif stt_provider == 'deepgram':
        primary_stt = deepgram.STT(
            model=config.get('deepgram_model', 'nova-3')
        )

    # Wrap with StreamAdapter + VAD
    return stt.StreamAdapter(
        stt=primary_stt,
        vad=vad
    )
```

**Key Components:**
1. **Provider Selection**: Based on `STT_PROVIDER` env variable
2. **VAD Integration**: Silero VAD wrapped with StreamAdapter
3. **Fallback Support**: Optional stt.FallbackAdapter
4. **Configuration**: Via ConfigLoader from .env

**File Locations:**
- Provider Factory: `src/providers/provider_factory.py`
- Config Loader: `src/config/config_loader.py`
- VAD Creation: `src/providers/provider_factory.py:96-110`
- Entry Point: `main.py:451-484`

---

## FunASR Implementation Analysis

### FunASR Local Architecture (xiaozhi-server)

**File**: `xiaozhi-server/core/providers/asr/fun_local.py`

**Key Features:**

#### 1. Local Inference Mode

**Initialization** (`fun_local.py:59-66`):

```python
from funasr import AutoModel

self.model = AutoModel(
    model=self.model_dir,                              # "models/SenseVoiceSmall"
    vad_kwargs={"max_single_segment_time": 30000},     # 30s max segments
    disable_update=True,
    hub="hf",                                          # HuggingFace
    device="cpu"                                       # or "cuda:0" for GPU
)
```

**Inference** (`fun_local.py:98-106`):

```python
result = self.model.generate(
    input=combined_pcm_data,      # Raw PCM audio bytes
    cache={},
    language="auto",              # Auto-detect language
    use_itn=True,                 # Inverse Text Normalization
    batch_size_s=60,              # Process 60s batches
)

text = rich_transcription_postprocess(result[0]["text"])
```

#### 2. Audio Processing Pipeline

```
Opus/PCM Audio
    ↓
Decode Opus → PCM (if needed)
    ↓
Combine PCM chunks
    ↓
FunASR.generate() [LOCAL INFERENCE]
    ↓
rich_transcription_postprocess()
    ↓
Text Output
```

#### 3. Built-in VAD

FunASR has native VAD support:
```python
vad_kwargs={"max_single_segment_time": 30000}  # 30 seconds
```

Can also integrate with external VAD (SileroVAD) for better control.

#### 4. Memory Requirements

**File**: `fun_local.py:43-48`

```python
# Memory check - require 2GB minimum
min_mem_bytes = 2 * 1024 * 1024 * 1024
total_mem = psutil.virtual_memory().total
if total_mem < min_mem_bytes:
    raise RuntimeError(
        f"Insufficient memory: {total_mem / (1024**3):.2f}GB available, "
        f"minimum 2GB required for FunASR"
    )
```

---

## Integration Strategy

### Approach: Multi-Provider Pattern

Add FunASR as a **third STT provider option** alongside Groq and Deepgram, maintaining backwards compatibility.

### Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LiveKit Server                       │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Provider Factory                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │  │   Groq   │  │ Deepgram │  │   FunASR     │  │  │
│  │  │   STT    │  │   STT    │  │  (LOCAL)     │  │  │
│  │  │  (API)   │  │  (API)   │  │  (No API)    │  │  │
│  │  └──────────┘  └──────────┘  └──────────────┘  │  │
│  │       ↓              ↓              ↓           │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │      STT StreamAdapter + VAD            │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Configuration: STT_PROVIDER = groq | deepgram | funasr│
└─────────────────────────────────────────────────────────┘
```

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Integration Mode** | Local Only | Privacy, cost savings, offline capability |
| **VAD Strategy** | Hybrid | Use FunASR built-in VAD + optional Silero |
| **Provider Pattern** | Factory | Consistent with existing architecture |
| **Fallback** | Optional | FunASR can fallback to Groq if fails |
| **Model Storage** | Local cache | Store in `model_cache/funasr/` |
| **Configuration** | Environment | Follow existing .env pattern |
| **GPU Support** | Optional | Default CPU, configurable GPU |

---

## Implementation Plan

### Phase 1: File Structure Setup (Day 1)

**1.1 Create FunASR Provider Files**

```
livekit-server/
├── src/
│   ├── providers/
│   │   ├── funasr_provider.py          # NEW - Local inference
│   │   └── provider_factory.py         # MODIFY - Add FunASR
│   │
│   └── config/
│       └── config_loader.py            # MODIFY - Add FunASR config
│
├── model_cache/
│   └── funasr/                         # NEW - Model storage
│       └── SenseVoiceSmall/            # NEW - Downloaded model
│
└── requirements.txt                    # MODIFY - Add funasr
```

**1.2 Create Model Cache Directory**

```bash
mkdir -p model_cache/funasr/SenseVoiceSmall
```

### Phase 2: Dependencies (Day 1)

**2.1 Update requirements.txt**

Add to `requirements.txt`:

```txt
# FunASR Speech Recognition (Local Inference)
funasr==1.2.3
modelscope
onnxruntime
psutil
```

**2.2 Install Dependencies**

```bash
pip install funasr==1.2.3 modelscope onnxruntime psutil
```

**2.3 Download FunASR Model**

Create one-time setup script:

**File**: `scripts/download_funasr_model.py`

```python
#!/usr/bin/env python3
"""Download FunASR SenseVoiceSmall model"""

import os
from modelscope.hub.snapshot_download import snapshot_download

def download_funasr_model():
    """Download FunASR model to local cache"""

    cache_dir = os.path.join(os.getcwd(), 'model_cache', 'funasr')
    os.makedirs(cache_dir, exist_ok=True)

    print(f"Downloading FunASR SenseVoiceSmall model to {cache_dir}...")

    model_dir = snapshot_download(
        'iic/SenseVoiceSmall',
        cache_dir=cache_dir,
        revision='master'
    )

    print(f"Model downloaded successfully to: {model_dir}")
    print(f"Model size: ~300MB")
    return model_dir

if __name__ == "__main__":
    download_funasr_model()
```

**Run script:**

```bash
python scripts/download_funasr_model.py
```

### Phase 3: Core Implementation (Day 2)

**3.1 Create FunASR Local Provider**

**File**: `src/providers/funasr_provider.py`

```python
"""FunASR Local Speech-to-Text Provider for LiveKit"""

import os
import time
import psutil
from typing import Optional
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from livekit import agents
from livekit.agents import stt
import logging

logger = logging.getLogger(__name__)

class FunASRSTT(stt.STT):
    """
    FunASR Local Inference Provider for LiveKit

    Provides multilingual speech-to-text using Alibaba's FunASR
    with local inference (no API calls required).

    Features:
    - Multilingual: Chinese, English, Japanese, Korean
    - Built-in VAD
    - ITN (Inverse Text Normalization)
    - Privacy-preserving (all processing local)
    - Zero API costs
    """

    def __init__(
        self,
        *,
        model_dir: str = "model_cache/funasr/SenseVoiceSmall",
        language: str = "auto",
        use_itn: bool = True,
        max_single_segment_time: int = 30000,
        device: str = "cpu",
    ):
        """
        Initialize FunASR STT provider

        Args:
            model_dir: Path to local model directory
            language: Language code ('auto', 'zh', 'en', 'ja', 'ko')
            use_itn: Enable Inverse Text Normalization
            max_single_segment_time: Max VAD segment duration (ms)
            device: Compute device ('cpu' or 'cuda:0')
        """
        super().__init__()

        self.model_dir = model_dir
        self.language = language
        self.use_itn = use_itn
        self.max_single_segment_time = max_single_segment_time
        self.device = device

        # Memory check - require 2GB minimum
        self._check_memory()

        # Initialize model
        self.model = None
        self._initialize_model()

    def _check_memory(self):
        """Check system has sufficient memory"""
        min_mem_bytes = 2 * 1024 * 1024 * 1024  # 2GB
        total_mem = psutil.virtual_memory().total

        if total_mem < min_mem_bytes:
            raise RuntimeError(
                f"Insufficient memory for FunASR: "
                f"{total_mem / (1024**3):.2f}GB available, "
                f"minimum 2GB required"
            )

        logger.info(
            f"FunASR memory check passed: "
            f"{total_mem / (1024**3):.2f}GB available"
        )

    def _initialize_model(self):
        """Initialize FunASR model"""
        try:
            logger.info(f"Loading FunASR model from {self.model_dir}")

            if not os.path.exists(self.model_dir):
                raise FileNotFoundError(
                    f"FunASR model not found at {self.model_dir}. "
                    f"Run: python scripts/download_funasr_model.py"
                )

            self.model = AutoModel(
                model=self.model_dir,
                vad_kwargs={"max_single_segment_time": self.max_single_segment_time},
                disable_update=True,
                hub="hf",
                device=self.device
            )

            logger.info(
                f"FunASR model loaded successfully "
                f"(device={self.device}, language={self.language})"
            )

        except Exception as e:
            logger.error(f"Failed to load FunASR model: {e}")
            raise

    async def recognize(
        self,
        *,
        buffer: agents.utils.AudioBuffer,
        language: Optional[str] = None
    ) -> stt.SpeechEvent:
        """
        Recognize speech from audio buffer

        Args:
            buffer: Audio buffer from LiveKit
            language: Optional language override

        Returns:
            SpeechEvent with transcription
        """
        try:
            start_time = time.time()

            # Convert AudioBuffer to PCM bytes
            audio_data = self._buffer_to_pcm(buffer)

            if len(audio_data) == 0:
                logger.warning("Empty audio buffer received")
                return self._empty_result()

            # Run inference
            result = self.model.generate(
                input=audio_data,
                cache={},
                language=language or self.language,
                use_itn=self.use_itn,
                batch_size_s=60,
            )

            # Post-process
            text = rich_transcription_postprocess(result[0]["text"])

            elapsed = time.time() - start_time
            logger.info(
                f"FunASR transcription completed in {elapsed:.2f}s: "
                f"'{text}' (length={len(audio_data)} bytes)"
            )

            # Return SpeechEvent
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[
                    stt.SpeechData(
                        text=text,
                        language=language or self.language,
                        confidence=1.0  # FunASR doesn't provide confidence
                    )
                ]
            )

        except Exception as e:
            logger.error(f"FunASR recognition error: {e}", exc_info=True)
            return self._empty_result()

    def _buffer_to_pcm(self, buffer: agents.utils.AudioBuffer) -> bytes:
        """
        Convert LiveKit AudioBuffer to PCM bytes

        FunASR expects:
        - Sample rate: 16kHz
        - Bit depth: 16-bit
        - Channels: Mono

        Args:
            buffer: LiveKit audio buffer

        Returns:
            PCM audio bytes
        """
        # Get frames from buffer
        frames = buffer.get_frames()

        if not frames:
            return b""

        # Convert frames to bytes
        # LiveKit frames are already in PCM format
        pcm_data = b"".join(
            frame.data.tobytes() for frame in frames
        )

        return pcm_data

    def _empty_result(self) -> stt.SpeechEvent:
        """Return empty speech event"""
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                stt.SpeechData(
                    text="",
                    language=self.language,
                    confidence=0.0
                )
            ]
        )
```

### Phase 4: Provider Factory Integration (Day 2-3)

**4.1 Update Provider Factory**

**File**: `src/providers/provider_factory.py`

**Add import:**

```python
from .funasr_provider import FunASRSTT
```

**Modify create_stt:**

```python
@staticmethod
def create_stt(config, vad=None):
    """Create STT provider with optional VAD"""

    stt_provider = config.get('stt_provider', 'groq')

    # FunASR Provider (LOCAL ONLY - NO API CALLS)
    if stt_provider == 'funasr':
        from src.config.config_loader import ConfigLoader
        funasr_config = ConfigLoader.get_funasr_config()

        primary_stt = FunASRSTT(
            model_dir=funasr_config['model_dir'],
            language=funasr_config['language'],
            use_itn=funasr_config['use_itn'],
            max_single_segment_time=funasr_config['max_single_segment_time'],
            device=funasr_config['device']
        )

        # FunASR has built-in VAD, but we can optionally wrap with Silero
        if funasr_config.get('use_external_vad', False) and vad:
            logger.info("Using FunASR with external Silero VAD")
            return stt.StreamAdapter(stt=primary_stt, vad=vad)
        else:
            logger.info("Using FunASR with built-in VAD")
            # Return FunASR directly (uses built-in VAD)
            return primary_stt

    # Groq Provider (Existing)
    elif stt_provider == 'groq':
        primary_stt = groq.STT(
            model=config['stt_model'],
            language=config['stt_language']
        )

    # Deepgram Provider (Existing)
    elif stt_provider == 'deepgram':
        primary_stt = deepgram.STT(
            model=config.get('deepgram_model', 'nova-3')
        )

    else:
        raise ValueError(f"Unknown STT provider: {stt_provider}")

    # Wrap with StreamAdapter + VAD (for Groq/Deepgram)
    return stt.StreamAdapter(stt=primary_stt, vad=vad)
```

### Phase 5: Configuration (Day 3)

**5.1 Update Config Loader**

**File**: `src/config/config_loader.py`

**Add new method:**

```python
@staticmethod
def get_funasr_config() -> dict:
    """
    Get FunASR configuration (local inference only)

    Returns:
        dict: FunASR configuration
    """
    return {
        # Model settings
        'model_dir': os.getenv(
            'FUNASR_MODEL_DIR',
            'model_cache/funasr/SenseVoiceSmall'
        ),

        # Language: 'auto', 'zh', 'en', 'ja', 'ko'
        'language': os.getenv('FUNASR_LANGUAGE', 'auto'),

        # Inverse Text Normalization (converts spoken numbers to digits)
        'use_itn': os.getenv('FUNASR_USE_ITN', 'true').lower() == 'true',

        # Max VAD segment duration (milliseconds)
        'max_single_segment_time': int(
            os.getenv('FUNASR_MAX_SEGMENT_TIME', '30000')
        ),

        # Compute device: 'cpu' or 'cuda:0' for GPU
        'device': os.getenv('FUNASR_DEVICE', 'cpu'),

        # Use external Silero VAD alongside FunASR's built-in VAD
        'use_external_vad': os.getenv(
            'FUNASR_USE_EXTERNAL_VAD',
            'false'
        ).lower() == 'true',
    }
```

**5.2 Environment Variables**

Add to `.env`:

```env
# ============================================
# FunASR Configuration (Local Inference Only)
# ============================================

# STT Provider: 'groq', 'deepgram', or 'funasr'
STT_PROVIDER=funasr

# Model directory (download once with scripts/download_funasr_model.py)
FUNASR_MODEL_DIR=model_cache/funasr/SenseVoiceSmall

# Language: 'auto' (auto-detect), 'zh' (Chinese), 'en' (English), 'ja' (Japanese), 'ko' (Korean)
FUNASR_LANGUAGE=auto

# Inverse Text Normalization: converts spoken numbers to digits (e.g., "一百" → "100")
FUNASR_USE_ITN=true

# Max VAD segment duration in milliseconds (default: 30 seconds)
FUNASR_MAX_SEGMENT_TIME=30000

# Compute device: 'cpu' (default) or 'cuda:0' (requires GPU)
# Note: GPU can significantly speed up inference
FUNASR_DEVICE=cpu

# Use external Silero VAD alongside FunASR's built-in VAD (optional)
# Set to 'true' only if you need more precise VAD control
FUNASR_USE_EXTERNAL_VAD=false
```

### Phase 6: Model Preloading (Day 3-4)

**6.1 Update Model Cache**

**File**: `src/utils/model_cache.py`

**Add method:**

```python
@classmethod
def get_funasr_model(cls, config: dict):
    """
    Get cached FunASR model (must run on main thread)

    Args:
        config: FunASR configuration dict

    Returns:
        FunASR AutoModel instance
    """

    def load_funasr():
        from funasr import AutoModel

        model_dir = config['model_dir']
        device = config['device']
        max_segment_time = config['max_single_segment_time']

        logger.info(f"Loading FunASR model from {model_dir} (device={device})")

        if not os.path.exists(model_dir):
            raise FileNotFoundError(
                f"FunASR model not found at {model_dir}. "
                f"Download it first: python scripts/download_funasr_model.py"
            )

        model = AutoModel(
            model=model_dir,
            vad_kwargs={"max_single_segment_time": max_segment_time},
            disable_update=True,
            hub="hf",
            device=device
        )

        logger.info("FunASR model loaded successfully")
        return model

    return cls.get_model('funasr_model', load_funasr)
```

**6.2 Update Prewarm Function**

**File**: `main.py`

**Modify prewarm:**

```python
async def prewarm(proc: JobProcess):
    """
    Prewarm function to preload models on worker startup

    This runs once per worker process and caches heavy models
    to avoid reloading on each session.
    """
    from src.config.config_loader import ConfigLoader
    from src.utils.model_cache import ModelCache

    logger.info("Starting prewarm process...")

    # Load VAD model (existing - Silero)
    logger.info("Loading VAD model...")
    ModelCache.get_vad_model()

    # Load FunASR model if configured
    config = ConfigLoader.get_groq_config()
    if config.get('stt_provider') == 'funasr':
        logger.info("Loading FunASR model...")
        funasr_config = ConfigLoader.get_funasr_config()
        ModelCache.get_funasr_model(funasr_config)

    # Load embedding model (existing - for semantic search)
    logger.info("Loading embedding model...")
    ModelCache.get_embedding_model(
        os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    )

    # Cache Qdrant client (existing)
    logger.info("Initializing Qdrant client...")
    ModelCache.get_qdrant_client()

    logger.info("Prewarm process completed successfully")
```

**6.3 Update FunASR Provider to Use Cache**

**Modify** `src/providers/funasr_provider.py`:

```python
def _initialize_model(self):
    """Initialize FunASR model (uses cached model if available)"""
    try:
        logger.info(f"Loading FunASR model from {self.model_dir}")

        # Try to get cached model first
        from src.utils.model_cache import ModelCache

        config = {
            'model_dir': self.model_dir,
            'device': self.device,
            'max_single_segment_time': self.max_single_segment_time
        }

        self.model = ModelCache.get_funasr_model(config)

        logger.info(
            f"FunASR model loaded successfully "
            f"(device={self.device}, language={self.language})"
        )

    except Exception as e:
        logger.error(f"Failed to load FunASR model: {e}")
        raise
```

---

## Configuration Changes

### Environment Variables Summary

| Variable | Default | Description |
|----------|---------|-------------|
| `STT_PROVIDER` | `groq` | Options: `groq`, `deepgram`, `funasr` |
| `FUNASR_MODEL_DIR` | `model_cache/funasr/SenseVoiceSmall` | Local model path |
| `FUNASR_LANGUAGE` | `auto` | Language: `auto`, `zh`, `en`, `ja`, `ko` |
| `FUNASR_USE_ITN` | `true` | Inverse Text Normalization |
| `FUNASR_MAX_SEGMENT_TIME` | `30000` | Max VAD segment (ms) |
| `FUNASR_DEVICE` | `cpu` | Device: `cpu` or `cuda:0` |
| `FUNASR_USE_EXTERNAL_VAD` | `false` | Use Silero VAD alongside FunASR |

### Configuration Files

**requirements.txt additions:**

```txt
# FunASR Local Inference
funasr==1.2.3
modelscope
onnxruntime
psutil
```

---

## Testing Strategy

### Phase 1: Unit Tests

**File**: `tests/test_funasr_provider.py`

```python
import pytest
import os
from src.providers.funasr_provider import FunASRSTT
from src.config.config_loader import ConfigLoader

@pytest.fixture
def funasr_config():
    """Get FunASR test configuration"""
    return ConfigLoader.get_funasr_config()

def test_funasr_initialization(funasr_config):
    """Test FunASR provider initialization"""
    stt = FunASRSTT(
        model_dir=funasr_config['model_dir'],
        language=funasr_config['language'],
        use_itn=funasr_config['use_itn'],
        device=funasr_config['device']
    )
    assert stt.model is not None
    assert stt.language == funasr_config['language']

def test_funasr_memory_check():
    """Test memory requirements check"""
    # This should pass if system has > 2GB RAM
    stt = FunASRSTT()
    # If we get here, memory check passed

@pytest.mark.asyncio
async def test_funasr_empty_audio(funasr_config):
    """Test FunASR with empty audio buffer"""
    from livekit.agents.utils import AudioBuffer

    stt = FunASRSTT(**funasr_config)

    # Create empty buffer
    buffer = AudioBuffer()

    result = await stt.recognize(buffer=buffer)

    assert result.type == "FINAL_TRANSCRIPT"
    assert result.alternatives[0].text == ""

@pytest.mark.asyncio
async def test_funasr_transcription(funasr_config):
    """Test FunASR transcription with real audio"""
    from livekit.agents.utils import AudioBuffer
    import numpy as np

    stt = FunASRSTT(**funasr_config)

    # Load sample audio (PCM, 16kHz, 16-bit, mono)
    # You need to provide test_audio.pcm file
    if os.path.exists('tests/fixtures/test_audio.pcm'):
        with open('tests/fixtures/test_audio.pcm', 'rb') as f:
            audio_data = f.read()

        # Convert to AudioBuffer
        buffer = AudioBuffer()
        # Add frames to buffer
        # ... (conversion logic)

        result = await stt.recognize(buffer=buffer)

        assert result.type == "FINAL_TRANSCRIPT"
        assert len(result.alternatives) > 0
        assert result.alternatives[0].text != ""
```

### Phase 2: Integration Tests

**File**: `tests/test_funasr_integration.py`

```python
import pytest
from src.providers.provider_factory import ProviderFactory
from src.config.config_loader import ConfigLoader

def test_provider_factory_funasr():
    """Test ProviderFactory creates FunASR correctly"""

    # Mock config
    config = {
        'stt_provider': 'funasr'
    }

    stt = ProviderFactory.create_stt(config)

    # Should return FunASRSTT instance (not wrapped if using built-in VAD)
    assert stt is not None

def test_provider_factory_funasr_with_vad():
    """Test ProviderFactory creates FunASR with external VAD"""

    config = {
        'stt_provider': 'funasr'
    }

    # Create VAD
    vad = ProviderFactory.create_vad()

    # Create STT with VAD
    stt = ProviderFactory.create_stt(config, vad=vad)

    assert stt is not None
```

### Phase 3: Performance Testing

**Metrics:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Transcription Latency** | < 500ms | Time from audio end to text output |
| **Memory Usage** | < 3GB | Peak RAM during inference |
| **CPU Usage** | < 80% | Average CPU during transcription |
| **Accuracy** | > 90% | WER (Word Error Rate) |
| **Throughput** | > 5 concurrent | Max concurrent sessions on CPU |

**Benchmark Script:**

**File**: `tests/benchmark_funasr.py`

```python
"""Benchmark FunASR performance"""

import time
import asyncio
import psutil
import os
from src.providers.funasr_provider import FunASRSTT
from livekit.agents.utils import AudioBuffer

async def benchmark_latency():
    """Benchmark transcription latency"""

    stt = FunASRSTT()

    # Load test audio
    with open('tests/fixtures/test_audio.pcm', 'rb') as f:
        audio_data = f.read()

    # Create buffer
    buffer = AudioBuffer()
    # Add audio to buffer...

    # Warm-up
    await stt.recognize(buffer=buffer)

    # Benchmark
    iterations = 100
    latencies = []

    for _ in range(iterations):
        start = time.time()
        await stt.recognize(buffer=buffer)
        latency = time.time() - start
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)

    print(f"\n=== Latency Benchmark ===")
    print(f"Average: {avg_latency * 1000:.2f}ms")
    print(f"Min: {min_latency * 1000:.2f}ms")
    print(f"Max: {max_latency * 1000:.2f}ms")
    print(f"Throughput: {iterations / sum(latencies):.2f} transcriptions/sec")

async def benchmark_memory():
    """Benchmark memory usage"""

    process = psutil.Process()

    # Baseline memory
    baseline_mem = process.memory_info().rss / (1024 ** 2)  # MB

    print(f"\n=== Memory Benchmark ===")
    print(f"Baseline: {baseline_mem:.2f} MB")

    # Load model
    stt = FunASRSTT()

    after_load_mem = process.memory_info().rss / (1024 ** 2)
    model_mem = after_load_mem - baseline_mem

    print(f"After model load: {after_load_mem:.2f} MB")
    print(f"Model memory: {model_mem:.2f} MB")

    # Run inference
    with open('tests/fixtures/test_audio.pcm', 'rb') as f:
        audio_data = f.read()

    buffer = AudioBuffer()
    # Add audio...

    for i in range(10):
        await stt.recognize(buffer=buffer)

    after_inference_mem = process.memory_info().rss / (1024 ** 2)

    print(f"After 10 inferences: {after_inference_mem:.2f} MB")
    print(f"Memory growth: {after_inference_mem - after_load_mem:.2f} MB")

async def benchmark_cpu():
    """Benchmark CPU usage"""

    import threading

    cpu_percentages = []
    monitoring = True

    def monitor_cpu():
        while monitoring:
            cpu_percentages.append(psutil.cpu_percent(interval=0.1))

    # Start monitoring
    monitor_thread = threading.Thread(target=monitor_cpu)
    monitor_thread.start()

    # Run inference
    stt = FunASRSTT()

    with open('tests/fixtures/test_audio.pcm', 'rb') as f:
        audio_data = f.read()

    buffer = AudioBuffer()
    # Add audio...

    for _ in range(50):
        await stt.recognize(buffer=buffer)

    # Stop monitoring
    monitoring = False
    monitor_thread.join()

    avg_cpu = sum(cpu_percentages) / len(cpu_percentages)
    max_cpu = max(cpu_percentages)

    print(f"\n=== CPU Benchmark ===")
    print(f"Average CPU: {avg_cpu:.2f}%")
    print(f"Max CPU: {max_cpu:.2f}%")

async def main():
    """Run all benchmarks"""
    print("=" * 50)
    print("FunASR Performance Benchmark")
    print("=" * 50)

    await benchmark_latency()
    await benchmark_memory()
    await benchmark_cpu()

    print("\n" + "=" * 50)
    print("Benchmark complete")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
```

**Run benchmarks:**

```bash
python tests/benchmark_funasr.py
```

---

## Migration Path

### Option 1: Gradual Rollout (Recommended)

**Week 1: Development**
- Implement FunASR provider
- Unit tests passing
- Integration tests passing
- Performance benchmarks acceptable

**Week 2: Staging**
- Deploy to staging environment
- Test with 10% of devices
- Monitor metrics:
  - Transcription accuracy
  - Latency
  - Memory usage
  - CPU usage
  - Error rates

**Week 3: Production Rollout**
- Deploy to 25% of devices → Monitor 3 days
- Increase to 50% → Monitor 3 days
- Increase to 75% → Monitor 3 days
- Full rollout to 100%

**Configuration per Device:**

```env
# Test devices (10%)
STT_PROVIDER=funasr

# Control devices (90%)
STT_PROVIDER=groq
```

### Option 2: Feature Flag

Use feature flags to control rollout:

```python
# In main.py or config

FUNASR_ENABLED_DEVICES = [
    "00:1a:2b:3c:4d:5e",  # Test device 1
    "00:1a:2b:3c:4d:5f",  # Test device 2
]

def get_stt_provider(device_mac):
    if device_mac in FUNASR_ENABLED_DEVICES:
        return "funasr"
    else:
        return "groq"
```

### Option 3: A/B Testing

Deploy both providers simultaneously and compare:

**Metrics Dashboard:**

```
┌─────────────────────────────────────────────────┐
│         STT Provider Comparison                 │
├──────────────┬──────────────┬──────────────────┤
│   Metric     │    FunASR    │      Groq        │
├──────────────┼──────────────┼──────────────────┤
│ Accuracy     │    94.2%     │     92.8%        │
│ Latency      │   350ms      │     450ms        │
│ Error Rate   │    2.1%      │      3.5%        │
│ Cost/1000    │    $0.00     │      $0.25       │
│ Privacy      │   100% Local │   Cloud-based    │
│ Offline      │   Yes        │      No          │
└──────────────┴──────────────┴──────────────────┘
```

---

## Rollback Plan

### Immediate Rollback (< 5 minutes)

If critical issues occur in production:

**Step 1: Change Environment Variable**

```env
# Rollback to Groq
STT_PROVIDER=groq
```

**Step 2: Restart Service**

```bash
# Stop current workers
pkill -f main.py

# Restart with Groq
python main.py --workers 3
```

**Result:** System immediately switches back to Groq STT

### Gradual Rollback (Staging Issues)

If issues found in staging:

1. Reduce rollout percentage: 10% → 5% → 0%
2. Analyze logs for root cause
3. Fix issues in development
4. Re-test before next rollout attempt

### Full Removal (If Abandoning Integration)

**Step 1: Remove Provider File**

```bash
rm src/providers/funasr_provider.py
```

**Step 2: Remove Dependencies**

Edit `requirements.txt`, remove:
```txt
funasr==1.2.3
modelscope
onnxruntime
```

**Step 3: Remove Configuration**

Edit `src/config/config_loader.py`, remove `get_funasr_config()` method

**Step 4: Remove from Provider Factory**

Edit `src/providers/provider_factory.py`, remove FunASR case

**Step 5: Clean Model Cache**

```bash
rm -rf model_cache/funasr/
```

**Step 6: Reinstall Dependencies**

```bash
pip install -r requirements.txt --force-reinstall
```

---

## File Structure Changes

### Before (Current)

```
livekit-server/
├── src/
│   ├── providers/
│   │   ├── provider_factory.py
│   │   ├── edge_tts_provider.py
│   │   └── ten_vad_wrapper.py
│   └── config/
│       └── config_loader.py
├── requirements.txt
└── model_cache/
```

### After (With FunASR Local)

```
livekit-server/
├── src/
│   ├── providers/
│   │   ├── provider_factory.py         # MODIFIED
│   │   ├── edge_tts_provider.py        # unchanged
│   │   ├── ten_vad_wrapper.py          # unchanged
│   │   └── funasr_provider.py          # NEW - Local inference only
│   │
│   ├── config/
│   │   └── config_loader.py            # MODIFIED
│   │
│   └── utils/
│       └── model_cache.py              # MODIFIED
│
├── scripts/
│   └── download_funasr_model.py        # NEW - One-time model download
│
├── model_cache/
│   └── funasr/
│       └── SenseVoiceSmall/            # NEW - ~300MB (one-time download)
│
├── tests/
│   ├── test_funasr_provider.py         # NEW
│   ├── test_funasr_integration.py      # NEW
│   └── benchmark_funasr.py             # NEW
│
└── requirements.txt                     # MODIFIED
```

---

## Code Implementation Checklist

- [ ] **Phase 1: File Structure**
  - [ ] Create `src/providers/funasr_provider.py`
  - [ ] Create `scripts/download_funasr_model.py`
  - [ ] Create `model_cache/funasr/` directory

- [ ] **Phase 2: Dependencies**
  - [ ] Add FunASR to `requirements.txt`
  - [ ] Install dependencies: `pip install funasr==1.2.3 modelscope onnxruntime psutil`
  - [ ] Run `python scripts/download_funasr_model.py` (one-time, ~300MB)

- [ ] **Phase 3: Configuration**
  - [ ] Add `get_funasr_config()` to `config_loader.py`
  - [ ] Update `.env` with FunASR variables
  - [ ] Document configuration options

- [ ] **Phase 4: Provider Factory**
  - [ ] Import `FunASRSTT` in `provider_factory.py`
  - [ ] Add `funasr` case to `create_stt()`
  - [ ] Implement VAD integration logic (optional external VAD)

- [ ] **Phase 5: Model Caching**
  - [ ] Add `get_funasr_model()` to `model_cache.py`
  - [ ] Update `prewarm()` in `main.py`
  - [ ] Update `FunASRSTT._initialize_model()` to use cache

- [ ] **Phase 6: Testing**
  - [ ] Write unit tests: `tests/test_funasr_provider.py`
  - [ ] Write integration tests: `tests/test_funasr_integration.py`
  - [ ] Create performance benchmarks: `tests/benchmark_funasr.py`
  - [ ] Test with real LiveKit rooms

- [ ] **Phase 7: Documentation**
  - [ ] Update main `README.md`
  - [ ] Create FunASR configuration guide
  - [ ] Document troubleshooting steps

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Memory Issues** | Medium | High | Enforce 2GB check, monitor memory usage, add swap |
| **Model Download Failure** | Low | Medium | Provide clear error messages, manual download option |
| **Latency Increase** | Low | Medium | Benchmark before deployment, optimize with GPU |
| **Compatibility Issues** | Low | Medium | Extensive testing, fallback to Groq on failure |
| **CPU Bottleneck** | Medium | Medium | Monitor CPU usage, recommend GPU for high load |
| **Model File Missing** | Low | High | Check file existence on startup, clear error message |

---

## Success Criteria

### Technical Metrics

✅ **Functionality**
- FunASR transcribes audio with >90% accuracy
- Supports English, Chinese, Japanese, Korean
- Latency < 500ms for 5-second audio clips
- Zero API calls (100% local processing)

✅ **Performance**
- Memory usage < 3GB per session
- CPU usage < 80% during transcription (CPU mode)
- Handles 5+ concurrent sessions on CPU
- Handles 20+ concurrent sessions on GPU

✅ **Reliability**
- 99.9% uptime
- Graceful fallback to Groq on initialization failure
- No memory leaks after 1000+ transcriptions

### User Experience Metrics

✅ **Accuracy**
- Word Error Rate (WER) < 10%
- Equal or better than current Groq baseline

✅ **Responsiveness**
- User perceives no latency increase
- Real-time conversation flow maintained

✅ **Privacy**
- 100% local processing (no audio sent to external APIs)
- Works offline

---

## Timeline

| Week | Tasks | Deliverables |
|------|-------|--------------|
| **Week 1** | Phase 1-3: Setup + Core Implementation | Working FunASR provider, model downloaded |
| **Week 2** | Phase 4-5: Factory Integration + Caching | Full integration with LiveKit |
| **Week 3** | Phase 6: Testing + Optimization | Tests passing, benchmarks complete |
| **Week 4** | Phase 7: Documentation + Staging | Staging deployment ready |
| **Week 5** | Production rollout (10% → 100%) | Production deployment complete |

---

## GPU Acceleration (Optional)

If you have NVIDIA GPU available, you can significantly speed up inference:

### Enable GPU Support

**1. Install CUDA dependencies:**

```bash
pip install onnxruntime-gpu
```

**2. Update environment variable:**

```env
# Use GPU
FUNASR_DEVICE=cuda:0
```

**3. Performance improvement:**

| Device | Latency | Throughput |
|--------|---------|------------|
| CPU | ~350ms | 5 concurrent |
| GPU | ~100ms | 20+ concurrent |

---

## Next Steps

1. **Review this plan** with the team
2. **Approve architecture** and design decisions
3. **Set up development environment**
4. **Download FunASR model**: `python scripts/download_funasr_model.py`
5. **Begin Phase 1** implementation
6. **Test thoroughly** before production deployment

---

## Quick Start Guide

### Minimal Setup (3 Steps)

**Step 1: Install dependencies**

```bash
pip install funasr==1.2.3 modelscope onnxruntime psutil
```

**Step 2: Download model (one-time, ~300MB)**

```bash
python scripts/download_funasr_model.py
```

**Step 3: Update .env**

```env
STT_PROVIDER=funasr
FUNASR_DEVICE=cpu
```

**Step 4: Run**

```bash
python main.py --workers 3
```

**Done!** FunASR is now handling all speech recognition locally with zero API calls.

---

## References

- **FunASR GitHub**: https://github.com/alibaba-damo-academy/FunASR
- **FunASR Documentation**: https://alibaba-damo-academy.github.io/FunASR/
- **SenseVoiceSmall Model**: https://modelscope.cn/models/iic/SenseVoiceSmall
- **LiveKit STT Docs**: https://docs.livekit.io/agents/integrations/stt/
- **xiaozhi-server Implementation**: `main/xiaozhi-server/core/providers/asr/fun_local.py`

---

**Document Version**: 2.0 (Local Only)
**Last Updated**: 2025-10-28
**Mode**: Local Inference Only (No API Calls)

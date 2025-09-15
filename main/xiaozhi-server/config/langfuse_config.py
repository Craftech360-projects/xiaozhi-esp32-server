import os
from langfuse import Langfuse
from config.logger import setup_logging
import json
from dotenv import load_dotenv

# Load environment variables from .env file - try multiple paths
import pathlib
current_dir = pathlib.Path(__file__).parent.parent
env_paths = [
    current_dir / '.env',
    pathlib.Path.cwd() / '.env',
    pathlib.Path(__file__).parent.parent.parent / '.env'
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, verbose=True)
        env_loaded = True
        print(f"[LANGFUSE] Loaded .env from: {env_path}")
        break

if not env_loaded:
    print(f"[LANGFUSE] Warning: .env file not found. Tried: {[str(p) for p in env_paths]}")

# Force reload to ensure variables are available
load_dotenv(override=True)

logger = setup_logging()
TAG = __name__


class LangfuseConfig:
    """Enhanced Langfuse configuration singleton with comprehensive tracking"""
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LangfuseConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize Langfuse client with environment variables or defaults"""
        try:
            # Get configuration from environment variables
            secret_key = os.getenv('LANGFUSE_SECRET_KEY')
            public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
            host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')

            print(f"[LANGFUSE DEBUG] Secret key present: {bool(secret_key)}")
            print(f"[LANGFUSE DEBUG] Public key present: {bool(public_key)}")
            print(f"[LANGFUSE DEBUG] Host: {host}")

            if secret_key and public_key:
                self._client = Langfuse(
                    secret_key=secret_key,
                    public_key=public_key,
                    host=host,
                    debug=os.getenv('LANGFUSE_DEBUG', 'false').lower() == 'true'
                )
                print(f"[LANGFUSE DEBUG] Client created successfully")
                print(f"[LANGFUSE DEBUG] Available methods: {[m for m in dir(self._client) if not m.startswith('_')][:10]}")
                logger.bind(tag=TAG).info("Langfuse client configured successfully with API keys.")
            else:
                print(f"[LANGFUSE DEBUG] Missing keys - will disable tracking")
                logger.bind(tag=TAG).warning(
                    f"Langfuse keys not found in environment variables. "
                    f"SECRET_KEY: {bool(secret_key)}, PUBLIC_KEY: {bool(public_key)} "
                    f"Set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY to enable tracking."
                )
                self._client = None
        except Exception as e:
            print(f"[LANGFUSE DEBUG] Exception during initialization: {e}")
            print(f"[LANGFUSE DEBUG] Exception type: {type(e)}")
            if "Authentication error" in str(e):
                logger.bind(tag=TAG).error(f"Langfuse authentication failed. Check your API keys: {e}")
                self._client = None
            else:
                logger.bind(tag=TAG).error(f"Langfuse initialization error: {e}")
                self._client = None

    def get_client(self):
        """Get the Langfuse client instance"""
        return self._client

    def is_enabled(self):
        """Check if Langfuse tracking is enabled"""
        # Only enable if client is properly initialized with valid keys
        if self._client is None:
            logger.bind(tag=TAG).debug("Langfuse client not initialized - missing API keys")
            return False
        return True

    def get_pricing_config(self):
        """Get model pricing configuration"""
        return {
            # OpenAI Models (USD per 1K tokens)
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},

            # Anthropic Models
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},

            # Google Models
            "gemini-pro": {"input": 0.001, "output": 0.002},
            "gemini-pro-vision": {"input": 0.002, "output": 0.004},

            # Groq Models (often free but including for completeness)
            "llama3-70b-8192": {"input": 0.0008, "output": 0.0008},
            "llama3-8b-8192": {"input": 0.0001, "output": 0.0001},
            "mixtral-8x7b-32768": {"input": 0.0006, "output": 0.0006},

            # Default fallback
            "default": {"input": 0.002, "output": 0.004}
        }


# Global instance
langfuse_config = LangfuseConfig()

#!/usr/bin/env python3
"""Download FunASR SenseVoiceSmall model"""

import os
import sys

def download_funasr_model():
    """Download FunASR model to local cache"""

    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except ImportError:
        print("Error: modelscope not installed. Run: pip install modelscope")
        sys.exit(1)

    # Get project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    cache_dir = os.path.join(project_root, 'model_cache', 'funasr')

    os.makedirs(cache_dir, exist_ok=True)

    print("=" * 60)
    print("FunASR SenseVoiceSmall Model Download")
    print("=" * 60)
    print(f"Downloading to: {cache_dir}")
    print("Model size: ~300MB")
    print("This is a one-time download...")
    print()

    try:
        model_dir = snapshot_download(
            'iic/SenseVoiceSmall',
            cache_dir=cache_dir,
            revision='master'
        )

        print()
        print("=" * 60)
        print("✓ Model downloaded successfully!")
        print("=" * 60)
        print(f"Model location: {model_dir}")
        print()
        print("Next steps:")
        print("1. Update .env: STT_PROVIDER=funasr")
        print("2. Run: python main.py --workers 3")
        print("=" * 60)

        return model_dir

    except Exception as e:
        print()
        print("=" * 60)
        print("✗ Download failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check internet connection")
        print("2. Try again (download may have been interrupted)")
        print("3. Check disk space (~300MB required)")
        sys.exit(1)

if __name__ == "__main__":
    download_funasr_model()

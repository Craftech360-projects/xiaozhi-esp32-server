#!/usr/bin/env python3
"""
Download Piper TTS voice models
"""
import os
import sys
import urllib.request
import tarfile
from pathlib import Path

# Voice model URLs from HuggingFace Piper voices
# Each voice needs both .onnx and .onnx.json files
VOICES = {
    'en_US-amy-medium': {
        'onnx': 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx',
        'json': 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json',
    },
    'en_US-amy-low': {
        'onnx': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx',
        'json': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx.json',
    },
    'en_US-lessac-medium': {
        'onnx': 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx',
        'json': 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json',
    },
    'en_GB-alan-medium': {
        'onnx': 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx',
        'json': 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json',
    },
}

def download_voice(voice_name: str, output_dir: str = './piper_models'):
    """Download a Piper voice model (both .onnx and .json files)"""

    if voice_name not in VOICES:
        print(f"[ERROR] Unknown voice: {voice_name}")
        print(f"Available voices: {', '.join(VOICES.keys())}")
        return False

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    voice_urls = VOICES[voice_name]
    onnx_url = voice_urls['onnx']
    json_url = voice_urls['json']

    print(f"[INFO] Downloading {voice_name}...")

    try:
        # Download .onnx file
        onnx_filename = os.path.basename(onnx_url)
        onnx_path = os.path.join(output_dir, onnx_filename)

        print(f"[INFO] Downloading {onnx_filename}...")
        urllib.request.urlretrieve(onnx_url, onnx_path, reporthook=download_progress)
        print(f"\n[SUCCESS] Downloaded ONNX model to {onnx_path}")

        # Download .json config file
        json_filename = os.path.basename(json_url)
        json_path = os.path.join(output_dir, json_filename)

        print(f"[INFO] Downloading {json_filename}...")
        urllib.request.urlretrieve(json_url, json_path, reporthook=download_progress)
        print(f"\n[SUCCESS] Downloaded config file to {json_path}")

        print(f"\n[SUCCESS] Voice model ready!")
        print(f"\nTo use this voice, update your .env file:")
        print(f"PIPER_MODEL_PATH={onnx_path}")
        print(f"\nOr use the voice name directly (will auto-search):")
        print(f"PIPER_VOICE={voice_name}")

        return True

    except Exception as e:
        print(f"[ERROR] Error downloading voice: {e}")
        import traceback
        traceback.print_exc()
        return False

def download_progress(block_num, block_size, total_size):
    """Show download progress"""
    downloaded = block_num * block_size
    percent = min(100, (downloaded / total_size) * 100)
    bar_length = 40
    filled = int(bar_length * percent / 100)
    bar = '#' * filled + '-' * (bar_length - filled)
    print(f'\r[{bar}] {percent:.1f}%', end='', flush=True)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python download_piper_voice.py <voice_name>")
        print(f"\nAvailable voices:")
        for voice in VOICES.keys():
            print(f"  - {voice}")
        print(f"\nExample: python download_piper_voice.py en_US-amy-medium")
        sys.exit(1)

    voice_name = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './piper_models'

    success = download_voice(voice_name, output_dir)

    if success:
        print("\n[SUCCESS] Voice model installed successfully!")
        print("\nNext steps:")
        print("1. Update your .env file with PIPER_MODEL_PATH")
        print("2. Or move the .onnx file to the current directory")
        print("3. Run your agent!")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Installation script for KittenTTS integration
"""

import os
import sys
import subprocess

def install_kittentts():
    """Install KittenTTS and its dependencies"""
    print("Installing KittenTTS and dependencies...")
    
    try:
        # Install KittenTTS dependencies
        dependencies = [
            "onnxruntime",
            "soundfile", 
            "phonemizer",
            "huggingface_hub"
        ]
        
        for dep in dependencies:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        
        print("✅ KittenTTS Python dependencies installed successfully!")
        
        # Check for eSpeak installation
        print("\n🔍 Checking for eSpeak installation...")
        try:
            import phonemizer
            phonemizer.backend.EspeakBackend(language="en-us")
            print("✅ eSpeak is already installed and working!")
        except RuntimeError as e:
            if "espeak not installed" in str(e):
                print("❌ eSpeak is not installed.")
                print("\n📋 To install eSpeak on Windows:")
                print("1. Download eSpeak-NG from: https://github.com/espeak-ng/espeak-ng/releases")
                print("2. Install the Windows installer (.msi file)")
                print("3. Or use conda: conda install -c conda-forge espeak-ng")
                print("4. Or use winget: winget install espeak-ng")
                print("\nAfter installing eSpeak, run this script again.")
                return
        
        # Test import
        print("Testing KittenTTS import...")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from core.utils.kittentts_model import KittenTTS
        print("✅ KittenTTS import successful!")
        
        # Test model download
        print("Testing model download (this may take a moment)...")
        model = KittenTTS("KittenML/kitten-tts-nano-0.1")
        print("✅ Model download and initialization successful!")
        
        print("\n🎉 KittenTTS installation completed successfully!")
        print("\nTo use KittenTTS in xiaozhi-server:")
        print("1. Update your config.yaml to set: selected_module.TTS: kittentts")
        print("2. Restart xiaozhi-server")
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        if "espeak not installed" in str(e) or "eSpeak" in str(e):
            print("\n📋 eSpeak Installation Required:")
            print("KittenTTS requires eSpeak for text phonemization.")
            print("Please install eSpeak-NG:")
            print("1. Download from: https://github.com/espeak-ng/espeak-ng/releases")
            print("2. Or use conda: conda install -c conda-forge espeak-ng") 
            print("3. Or use winget: winget install espeak-ng")
        else:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    install_kittentts()
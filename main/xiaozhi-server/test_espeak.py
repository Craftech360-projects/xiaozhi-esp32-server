#!/usr/bin/env python3
"""
Test script to debug eSpeak installation on Windows
"""

import os
import platform
import subprocess

def test_espeak():
    """Test eSpeak installation and provide debugging info"""
    print("🔍 Testing eSpeak installation...")
    print(f"Platform: {platform.system()} {platform.release()}")
    print()
    
    # Test 1: Check if espeak is in PATH
    print("1. Testing espeak command in PATH...")
    try:
        result = subprocess.run(["espeak", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ eSpeak found in PATH: {result.stdout.strip()}")
        else:
            print(f"❌ eSpeak command failed: {result.stderr}")
    except FileNotFoundError:
        print("❌ eSpeak not found in PATH")
    except Exception as e:
        print(f"❌ Error testing eSpeak: {e}")
    
    # Test 2: Check common Windows installation paths
    if platform.system() == "Windows":
        print("\n2. Checking common Windows installation paths...")
        common_paths = [
            r"C:\Program Files\eSpeak NG\espeak-ng.exe",
            r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe", 
            r"C:\espeak-ng\espeak-ng.exe",
            r"C:\tools\espeak-ng\espeak-ng.exe"
        ]
        
        found_paths = []
        for path in common_paths:
            if os.path.exists(path):
                print(f"✅ Found eSpeak at: {path}")
                found_paths.append(path)
                
                # Test this executable
                try:
                    result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"   Version: {result.stdout.strip()}")
                    else:
                        print(f"   ❌ Failed to run: {result.stderr}")
                except Exception as e:
                    print(f"   ❌ Error running: {e}")
            else:
                print(f"❌ Not found: {path}")
        
        if not found_paths:
            print("❌ eSpeak not found in any common locations")
    
    # Test 3: Test phonemizer library
    print("\n3. Testing phonemizer library...")
    try:
        import phonemizer
        print("✅ phonemizer library imported successfully")
        
        # Try to create EspeakBackend
        try:
            backend = phonemizer.backend.EspeakBackend(language="en-us")
            print("✅ EspeakBackend created successfully")
            
            # Test phonemization
            try:
                result = backend.phonemize(["hello world"])
                print(f"✅ Phonemization test successful: {result}")
            except Exception as e:
                print(f"❌ Phonemization failed: {e}")
                
        except Exception as e:
            print(f"❌ EspeakBackend creation failed: {e}")
            
    except ImportError as e:
        print(f"❌ phonemizer library not installed: {e}")
    
    # Test 4: Check PATH environment
    print("\n4. Checking PATH environment...")
    path_env = os.environ.get("PATH", "")
    espeak_in_path = any("espeak" in p.lower() for p in path_env.split(os.pathsep))
    
    if espeak_in_path:
        print("✅ Found eSpeak-related path in PATH environment")
        for p in path_env.split(os.pathsep):
            if "espeak" in p.lower():
                print(f"   {p}")
    else:
        print("❌ No eSpeak-related paths found in PATH")
    
    print("\n" + "="*50)
    print("📋 RECOMMENDATIONS:")
    
    if platform.system() == "Windows":
        print("For Windows users:")
        print("1. Download eSpeak-NG from: https://github.com/espeak-ng/espeak-ng/releases")
        print("2. Install the .msi file (choose default installation path)")
        print("3. Add to PATH: C:\\Program Files\\eSpeak NG\\")
        print("4. Restart your terminal/IDE")
        print("5. Or use conda: conda install -c conda-forge espeak-ng")

if __name__ == "__main__":
    test_espeak()
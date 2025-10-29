#!/usr/bin/env python3
"""
Simple startup script for the simplified LiveKit agent
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Set environment file
    env_file = script_dir / "simple.env"
    if not env_file.exists():
        print(f"❌ Environment file not found: {env_file}")
        print("Please copy simple.env.example to simple.env and configure it")
        return 1
    
    # Set environment variable for dotenv
    os.environ["DOTENV_PATH"] = str(env_file)
    
    # Run the simple agent
    simple_main = script_dir / "simple_main.py"
    
    print("🚀 Starting simplified LiveKit agent...")
    print(f"📁 Working directory: {script_dir}")
    print(f"🔧 Environment file: {env_file}")
    print(f"🤖 Agent script: {simple_main}")
    print("-" * 50)
    
    try:
        # Run with development mode
        result = subprocess.run([
            sys.executable, str(simple_main), "dev"
        ], cwd=script_dir)
        return result.returncode
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
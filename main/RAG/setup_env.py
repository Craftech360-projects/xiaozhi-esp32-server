import venv
import subprocess
import sys
import os

def setup_venv():
    # Create virtual environment
    venv.create("venv", with_pip=True)
    
    # Get the path to the virtual environment's Python executable
    if sys.platform == "win32":
        python_path = os.path.join("venv", "Scripts", "python.exe")
        pip_path = os.path.join("venv", "Scripts", "pip.exe")
    else:
        python_path = os.path.join("venv", "bin", "python")
        pip_path = os.path.join("venv", "bin", "pip")
    
    # Upgrade pip
    subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    subprocess.run([pip_path, "install", "-r", "requirements.txt"])

if __name__ == "__main__":
    setup_venv()
    print("Virtual environment setup complete!")

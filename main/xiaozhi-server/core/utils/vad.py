import importlib
import os
import sys
from core.providers.vad.base import VADProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

def create_instance(class_name: str, *args, **kwargs) -> VADProviderBase:
    """Factory method to create VAD instance"""
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find the provider directly under core/providers/vad
    provider_file_direct = os.path.join(current_dir, '..', 'providers', 'vad', f'{class_name}.py')
    
    # Try to find the provider in a subdirectory (e.g., core/providers/vad/silero/silero.py)
    provider_file_subdir = os.path.join(current_dir, '..', 'providers', 'vad', class_name, f'{class_name}.py')

    if os.path.exists(provider_file_direct):
        lib_name = f"core.providers.vad.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f"{lib_name}")
        return sys.modules[lib_name].VADProvider(*args, **kwargs)
    elif os.path.exists(provider_file_subdir):
        lib_name = f"core.providers.vad.{class_name}.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f"{lib_name}")
        return sys.modules[lib_name].VADProvider(*args, **kwargs)
    
    raise ValueError(f"Unsupported VAD type: {class_name}, please check if the type configuration is correct")

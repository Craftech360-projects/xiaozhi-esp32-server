import importlib
import logging
import os
import sys
import time
import wave
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from core.providers.asr.base import ASRProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


def create_instance(class_name: str, *args, **kwargs) -> ASRProviderBase:
    """Factory method to create ASR instance"""
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find the provider directly under core/providers/asr
    provider_file_direct = os.path.join(current_dir, '..', 'providers', 'asr', f'{class_name}.py')
    
    # Try to find the provider in a subdirectory (e.g., core/providers/asr/amazon_transcribe_realtime/amazon_transcribe_realtime.py)
    provider_file_subdir = os.path.join(current_dir, '..', 'providers', 'asr', class_name, f'{class_name}.py')

    if os.path.exists(provider_file_direct):
        lib_name = f"core.providers.asr.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f"{lib_name}")
        return sys.modules[lib_name].ASRProvider(*args, **kwargs)
    elif os.path.exists(provider_file_subdir):
        lib_name = f"core.providers.asr.{class_name}.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f"{lib_name}")
        return sys.modules[lib_name].ASRProvider(*args, **kwargs)
    
    raise ValueError(
        f"Unsupported ASR type: {class_name}, please check if the type in this configuration is set correctly")

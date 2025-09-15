import os
import sys
import importlib
from config.logger import setup_logging

logger = setup_logging()


def create_instance(class_name, *args, **kwargs):
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the provider file
    provider_path = os.path.join(current_dir, '..', 'providers', 'memory', class_name, f'{class_name}.py')

    if os.path.exists(provider_path):
        lib_name = f'core.providers.memory.{class_name}.{class_name}'
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f'{lib_name}')
        return sys.modules[lib_name].MemoryProvider(*args, **kwargs)

    raise ValueError(f"Unsupported memory service type: {class_name}")

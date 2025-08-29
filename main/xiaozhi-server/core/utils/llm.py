import importlib
from config.logger import setup_logging
import os
import sys
# Add project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, project_root)


logger = setup_logging()


def create_instance(class_name, *args, **kwargs):
    # Create LLM instance
    logger.info(f"🔧 Creating LLM instance: {class_name} with args: {args}")
    
    # Special handling for openai_realtime type
    if class_name == "openai_realtime":
        try:
            from core.providers.llm.openai_realtime.openai_realtime import OpenAIRealtimeProvider
            instance = OpenAIRealtimeProvider(*args, **kwargs)
            logger.info(f"✅ Created OpenAI Realtime instance: {type(instance)}")
            return instance
        except ImportError as e:
            logger.error(f"❌ Failed to import OpenAI Realtime provider: {e}")
            raise ValueError(f"OpenAI Realtime provider not available: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to create OpenAI Realtime instance: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    # Standard LLM provider loading
    if os.path.exists(os.path.join('core', 'providers', 'llm', class_name, f'{class_name}.py')):
        lib_name = f'core.providers.llm.{class_name}.{class_name}'
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f'{lib_name}')
        instance = sys.modules[lib_name].LLMProvider(*args, **kwargs)
        logger.info(f"✅ Created standard LLM instance: {type(instance)}")
        return instance

    raise ValueError(
        f"Unsupported LLM type: {class_name}, please check if the type in this configuration is set correctly")

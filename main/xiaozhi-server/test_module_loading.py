#!/usr/bin/env python3
"""
Test script to verify module loading works with OpenAI Realtime API
"""

import sys
from pathlib import Path

# Add the xiaozhi-server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.logger import setup_logging
from config.settings import load_config
from core.utils.llm import create_instance

TAG = __name__
logger = setup_logging()

def test_module_loading():
    """Test if OpenAI Realtime module loads correctly"""
    logger.bind(tag=TAG).info("🔧 Testing OpenAI Realtime module loading...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Get LLM configuration
        selected_llm = config["selected_module"]["LLM"]
        llm_config = config["LLM"][selected_llm]
        
        logger.bind(tag=TAG).info(f"Selected LLM: {selected_llm}")
        logger.bind(tag=TAG).info(f"LLM Config: {llm_config}")
        
        # Try to create the instance
        llm_instance = create_instance("openai_realtime", llm_config)
        
        if llm_instance:
            logger.bind(tag=TAG).info("✅ OpenAI Realtime module loaded successfully!")
            logger.bind(tag=TAG).info(f"API Key configured: {'Yes' if llm_instance.api_key else 'No'}")
            logger.bind(tag=TAG).info(f"Model: {llm_instance.model}")
            logger.bind(tag=TAG).info(f"Voice: {llm_instance.voice}")
            return True
        else:
            logger.bind(tag=TAG).error("❌ Failed to create OpenAI Realtime instance")
            return False
            
    except Exception as e:
        logger.bind(tag=TAG).error(f"❌ Module loading error: {e}")
        import traceback
        logger.bind(tag=TAG).error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_module_loading()
    if success:
        print("\n🎉 Module loading test PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Module loading test FAILED!")
        sys.exit(1)
#!/usr/bin/env python3
"""
Debug what the actual server configuration uses
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_server_config():
    """Debug the actual server configuration"""
    print("DEBUGGING ACTUAL SERVER CONFIGURATION")
    print("=" * 50)
    
    try:
        # Use the EXACT same imports as app.py
        from config.settings import load_config
        from core.websocket_server import WebSocketServer
        from config.logger import setup_logging
        
        logger = setup_logging()
        
        # Load config exactly like app.py does
        config = load_config()
        print("[OK] Config loaded successfully")
        
        # Check selected modules
        selected_modules = config.get("selected_module", {})
        print(f"[INFO] Selected modules: {selected_modules}")
        
        # Check LLM configuration
        llm_selected = selected_modules.get("LLM", "unknown")
        print(f"[INFO] Selected LLM module: {llm_selected}")
        
        if llm_selected != "unknown" and "LLM" in config:
            llm_config = config["LLM"].get(llm_selected, {})
            print(f"[INFO] LLM config keys: {list(llm_config.keys())}")
            
            # Check what type/provider is being used
            llm_type = llm_config.get("type", llm_selected)
            print(f"[CRITICAL] Actual LLM provider type: {llm_type}")
            
            model_name = llm_config.get("model_name", "unknown")
            print(f"[INFO] Model name: {model_name}")
        
        # Create WebSocketServer to see what LLM gets initialized
        print(f"\n[INFO] Creating WebSocketServer to check LLM initialization...")
        ws_server = WebSocketServer(config)
        
        # Check what LLM module was actually created
        llm_module = ws_server._llm
        if llm_module:
            print(f"[CRITICAL] Actual LLM instance type: {type(llm_module)}")
            print(f"[CRITICAL] LLM module file: {llm_module.__class__.__module__}")
            print(f"[INFO] LLM model name: {getattr(llm_module, 'model_name', 'unknown')}")
            
            # Check if methods are decorated
            response_method = getattr(llm_module, 'response', None)
            if hasattr(response_method, '__wrapped__'):
                print(f"[OK] response() method IS DECORATED!")
            else:
                print(f"[ERROR] response() method is NOT DECORATED!")
                
            response_with_functions_method = getattr(llm_module, 'response_with_functions', None)
            if hasattr(response_with_functions_method, '__wrapped__'):
                print(f"[OK] response_with_functions() method IS DECORATED!")
            else:
                print(f"[ERROR] response_with_functions() method is NOT DECORATED!")
        else:
            print(f"[ERROR] No LLM module initialized!")
        
    except Exception as e:
        print(f"[ERROR] Debug failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("[SOLUTION] Based on the results above:")
    print("1. If LLM provider type is 'openai' and methods are decorated: Real tracking should work")
    print("2. If LLM provider type is NOT 'openai': You're using different provider, need to check that one")
    print("3. If methods are NOT decorated: Provider module not importing decorators correctly")
    print("=" * 50)

if __name__ == "__main__":
    debug_server_config()
#!/usr/bin/env python3
"""
Test script for OpenAI Realtime API integration
Tests connection, audio conversion, and basic functionality
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add the xiaozhi-server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.logger import setup_logging
from config.settings import load_config
from core.providers.llm.openai_realtime import OpenAIRealtimeProvider
from core.utils.audio_converter import AudioConverter

TAG = __name__
logger = setup_logging()


class RealtimeAPITester:
    """Test suite for OpenAI Realtime API integration"""
    
    def __init__(self):
        self.config = load_config()
        self.provider = None
        
    def test_configuration(self) -> bool:
        """Test if Realtime API is properly configured"""
        logger.bind(tag=TAG).info("🔧 Testing configuration...")
        
        realtime_config = self.config.get("openai_realtime", {})
        
        if not realtime_config.get("enabled", False):
            logger.bind(tag=TAG).warning("❌ Realtime API is disabled in config")
            return False
            
        api_key = realtime_config.get("api_key")
        if not api_key or "your-openai-api-key" in api_key:
            logger.bind(tag=TAG).error("❌ OpenAI API key not configured")
            return False
            
        logger.bind(tag=TAG).info("✅ Configuration looks good")
        return True
    
    def test_audio_utilities(self) -> bool:
        """Test if audio encoding/decoding utilities are available"""
        logger.bind(tag=TAG).info("🎵 Testing audio utilities...")
        
        try:
            # Test Opus encoder utility
            from core.utils.opus_encoder_utils import OpusEncoderUtils
            encoder = OpusEncoderUtils(16000, 1, 60)
            logger.bind(tag=TAG).info("✅ Opus encoder utility available")
            
            # Test Opus decoder utility
            from core.providers.asr.base import ASRProviderBase
            logger.bind(tag=TAG).info("✅ Opus decoder utility available")
            
            # Test opuslib_next dependency
            import opuslib_next
            logger.bind(tag=TAG).info("✅ opuslib_next dependency available")
            
            return True
            
        except ImportError as e:
            logger.bind(tag=TAG).error(f"❌ Missing audio utility: {e}")
            logger.bind(tag=TAG).info("Install required: pip install opuslib-next scipy numpy")
            return False
        except Exception as e:
            logger.bind(tag=TAG).error(f"❌ Audio utility test failed: {e}")
            return False
    
    def test_dependencies(self) -> bool:
        """Test if required Python dependencies are available"""
        logger.bind(tag=TAG).info("📦 Testing Python dependencies...")
        
        required_deps = ['websockets', 'scipy', 'numpy']
        missing_deps = []
        
        for dep in required_deps:
            try:
                __import__(dep)
                logger.bind(tag=TAG).info(f"✅ {dep} is available")
            except ImportError:
                logger.bind(tag=TAG).error(f"❌ {dep} is missing")
                missing_deps.append(dep)
        
        if missing_deps:
            logger.bind(tag=TAG).error(f"Install missing dependencies: pip install {' '.join(missing_deps)}")
            return False
            
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to OpenAI Realtime API"""
        logger.bind(tag=TAG).info("🌐 Testing OpenAI Realtime API connection...")
        
        try:
            realtime_config = self.config.get("openai_realtime", {})
            api_key = realtime_config.get("api_key")
            model = realtime_config.get("model", "gpt-4o-realtime-preview")
            
            self.provider = OpenAIRealtimeProvider(api_key=api_key, model=model)
            
            # Start connection in background
            connection_task = asyncio.create_task(self.provider.connect())
            
            # Wait for initial connection and session setup
            try:
                # Give more time for connection and session setup
                await asyncio.sleep(3)  # Wait for connection to establish
                
                # Check if we got a session (means connection worked)
                if self.provider.session_id or self.provider.connected:
                    logger.bind(tag=TAG).info("✅ Connected to OpenAI Realtime API")
                    # Cancel the connection task since we're done testing
                    connection_task.cancel()
                    return True
                else:
                    logger.bind(tag=TAG).error("❌ Failed to establish connection")
                    connection_task.cancel()
                    return False
                    
            except Exception as e:
                logger.bind(tag=TAG).error(f"❌ Connection test error: {e}")
                connection_task.cancel()
                return False
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"❌ Connection error: {e}")
            return False
    
    def test_audio_conversion(self) -> bool:
        """Test audio format conversion using existing utilities"""
        logger.bind(tag=TAG).info("🔊 Testing audio conversion...")
        
        try:
            # Create a simple test audio data (sine wave)
            import numpy as np
            from core.utils.opus_encoder_utils import OpusEncoderUtils
            from core.providers.asr.base import ASRProviderBase
            
            # Generate 1 second of 16kHz sine wave (440 Hz)
            sample_rate = 16000
            duration = 1.0
            frequency = 440
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            sine_wave = np.sin(2 * np.pi * frequency * t)
            
            # Convert to int16 PCM
            pcm_data = (sine_wave * 32767).astype(np.int16).tobytes()
            
            # Test PCM to Opus conversion using existing encoder
            encoder = OpusEncoderUtils(16000, 1, 60)
            opus_packets = encoder.encode_pcm_to_opus(pcm_data, end_of_stream=True)
            
            if opus_packets:
                logger.bind(tag=TAG).info("✅ PCM to Opus conversion works")
                
                # Test Opus to PCM conversion using existing decoder
                pcm_frames = ASRProviderBase.decode_opus(opus_packets)
                
                if pcm_frames:
                    logger.bind(tag=TAG).info("✅ Opus to PCM conversion works")
                    return True
                else:
                    logger.bind(tag=TAG).error("❌ Opus to PCM conversion failed")
                    return False
            else:
                logger.bind(tag=TAG).error("❌ PCM to Opus conversion failed")
                return False
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"❌ Audio conversion test failed: {e}")
            return False
    
    async def test_text_interaction(self) -> bool:
        """Test text-based interaction with Realtime API"""
        logger.bind(tag=TAG).info("💬 Testing text interaction...")
        
        if not self.provider or not self.provider.connected:
            logger.bind(tag=TAG).error("❌ Provider not connected")
            return False
            
        try:
            # Send a simple text message
            await self.provider._send_text_message("Hello, can you hear me?")
            
            # Wait a moment for response
            await asyncio.sleep(2)
            
            logger.bind(tag=TAG).info("✅ Text message sent successfully")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"❌ Text interaction failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up test resources"""
        if self.provider:
            await self.provider.disconnect()
        logger.bind(tag=TAG).info("🧹 Cleanup completed")


async def main():
    """Run all tests"""
    logger.bind(tag=TAG).info("🚀 Starting OpenAI Realtime API tests...")
    
    tester = RealtimeAPITester()
    
    tests = [
        ("Configuration", tester.test_configuration),
        ("Dependencies", tester.test_dependencies), 
        ("Audio Utilities", tester.test_audio_utilities),
        ("Audio Conversion", tester.test_audio_conversion),
        ("API Connection", tester.test_connection),
        ("Text Interaction", tester.test_text_interaction),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.bind(tag=TAG).info(f"\n{'='*50}")
        logger.bind(tag=TAG).info(f"Running test: {test_name}")
        logger.bind(tag=TAG).info(f"{'='*50}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
                logger.bind(tag=TAG).info(f"✅ {test_name}: PASSED")
            else:
                logger.bind(tag=TAG).error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"❌ {test_name}: ERROR - {e}")
    
    # Cleanup
    await tester.cleanup()
    
    # Results summary
    logger.bind(tag=TAG).info(f"\n{'='*50}")
    logger.bind(tag=TAG).info(f"TEST RESULTS SUMMARY")
    logger.bind(tag=TAG).info(f"{'='*50}")
    logger.bind(tag=TAG).info(f"Passed: {passed}/{total}")
    logger.bind(tag=TAG).info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        logger.bind(tag=TAG).info("🎉 All tests passed! Realtime API integration is ready.")
        return 0
    else:
        logger.bind(tag=TAG).warning(f"⚠️  {total-passed} test(s) failed. Check configuration and dependencies.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
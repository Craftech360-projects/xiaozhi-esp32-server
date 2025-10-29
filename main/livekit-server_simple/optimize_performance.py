#!/usr/bin/env python3
"""
Performance Optimization Script for Simple LiveKit Agent
Applies system-level optimizations for better multi-client performance
"""

import os
import sys
import logging
import platform
import subprocess

logger = logging.getLogger(__name__)

def setup_logging():
    """Setup logging for the optimization script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def check_system_requirements():
    """Check if system meets minimum requirements"""
    logger.info("🔍 Checking system requirements...")
    
    try:
        import psutil
        
        # Check CPU cores
        cpu_count = psutil.cpu_count()
        logger.info(f"CPU cores: {cpu_count}")
        if cpu_count < 4:
            logger.warning("⚠️ Recommended: 4+ CPU cores for optimal multi-client performance")
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        logger.info(f"Total memory: {memory_gb:.1f} GB")
        if memory_gb < 8:
            logger.warning("⚠️ Recommended: 8+ GB RAM for optimal multi-client performance")
        
        # Check available memory
        available_gb = memory.available / (1024**3)
        logger.info(f"Available memory: {available_gb:.1f} GB")
        if available_gb < 4:
            logger.warning("⚠️ Low available memory - consider closing other applications")
        
        return True
        
    except ImportError:
        logger.error("❌ psutil not available - install with: pip install psutil")
        return False

def optimize_python_settings():
    """Apply Python-specific optimizations"""
    logger.info("🐍 Applying Python optimizations...")
    
    # Set environment variables for better performance
    optimizations = {
        'PYTHONUNBUFFERED': '1',  # Disable output buffering
        'PYTHONDONTWRITEBYTECODE': '1',  # Don't write .pyc files
        'MALLOC_ARENA_MAX': '2',  # Limit malloc arenas for better memory usage
        'MALLOC_MMAP_THRESHOLD_': '131072',  # Use mmap for large allocations
        'MALLOC_TRIM_THRESHOLD_': '131072',  # Trim memory more aggressively
    }
    
    for key, value in optimizations.items():
        os.environ[key] = value
        logger.info(f"✅ Set {key}={value}")

def optimize_audio_settings():
    """Apply audio-specific optimizations"""
    logger.info("🎵 Applying audio optimizations...")
    
    audio_optimizations = {
        'AUDIO_FRAME_SIZE': '240',  # 5ms frames at 48kHz
        'AUDIO_BUFFER_SIZE': '480',  # Minimal buffering
        'TTS_STREAMING': 'true',  # Enable streaming TTS
        'AUDIO_JITTER_BUFFER': 'false',  # Disable jitter buffer
        'AUDIO_ECHO_CANCELLATION': 'false',  # Disable to reduce CPU
    }
    
    for key, value in audio_optimizations.items():
        os.environ[key] = value
        logger.info(f"✅ Set {key}={value}")

def optimize_system_priority():
    """Set high priority for the process"""
    logger.info("⚡ Setting process priority...")
    
    try:
        import psutil
        process = psutil.Process()
        
        if platform.system() == "Windows":
            # Set high priority on Windows
            process.nice(psutil.HIGH_PRIORITY_CLASS)
            logger.info("✅ Set Windows high priority")
        else:
            # Set nice value on Unix-like systems
            process.nice(-10)  # Higher priority (lower nice value)
            logger.info("✅ Set Unix high priority (nice -10)")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not set process priority: {e}")

def check_network_settings():
    """Check and suggest network optimizations"""
    logger.info("🌐 Checking network settings...")
    
    try:
        import psutil
        net_io = psutil.net_io_counters()
        
        logger.info(f"Network bytes sent: {net_io.bytes_sent / 1024 / 1024:.1f} MB")
        logger.info(f"Network bytes received: {net_io.bytes_recv / 1024 / 1024:.1f} MB")
        
        # Check for network interface optimizations
        if platform.system() == "Linux":
            logger.info("💡 Linux network optimization tips:")
            logger.info("   - Consider: echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf")
            logger.info("   - Consider: echo 'net.core.wmem_max = 16777216' >> /etc/sysctl.conf")
        
    except Exception as e:
        logger.warning(f"⚠️ Could not check network settings: {e}")

def optimize_garbage_collection():
    """Optimize Python garbage collection"""
    logger.info("🗑️ Optimizing garbage collection...")
    
    import gc
    
    # Get current GC thresholds
    thresholds = gc.get_threshold()
    logger.info(f"Current GC thresholds: {thresholds}")
    
    # Set more aggressive GC for memory efficiency
    # (generation0, generation1, generation2)
    gc.set_threshold(500, 10, 10)  # More frequent collection
    
    new_thresholds = gc.get_threshold()
    logger.info(f"✅ New GC thresholds: {new_thresholds}")
    
    # Enable automatic garbage collection
    gc.enable()
    logger.info("✅ Garbage collection enabled")

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger.info("📦 Checking dependencies...")
    
    # Map package names to their import names
    packages_to_check = {
        'livekit': 'livekit',
        'livekit-agents': 'livekit.agents',
        'livekit-plugins-groq': 'livekit.plugins.groq',
        'livekit-plugins-silero': 'livekit.plugins.silero',
        'edge-tts': 'edge_tts',
        'psutil': 'psutil',
    }
    
    missing_packages = []
    
    for package_name, import_name in packages_to_check.items():
        try:
            __import__(import_name)
            logger.info(f"✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            logger.error(f"❌ {package_name} - MISSING")
    
    if missing_packages:
        logger.error(f"Missing packages: {missing_packages}")
        logger.error("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def display_performance_tips():
    """Display additional performance tips"""
    logger.info("💡 Additional Performance Tips:")
    logger.info("   1. Close unnecessary applications to free up CPU and memory")
    logger.info("   2. Use SSD storage for faster model loading")
    logger.info("   3. Ensure stable network connection for cloud TTS/STT")
    logger.info("   4. Monitor resource usage with the built-in ResourceMonitor")
    logger.info("   5. Consider using Groq TTS instead of EdgeTTS for better performance")
    logger.info("   6. Limit concurrent clients to 6 or fewer for best experience")
    logger.info("   7. Use wired network connection instead of WiFi if possible")

def main():
    """Main optimization function"""
    setup_logging()
    
    logger.info("🚀 Starting LiveKit Agent Performance Optimization")
    logger.info("=" * 60)
    
    # Check system requirements
    if not check_system_requirements():
        logger.error("❌ System requirements check failed")
        return False
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed")
        return False
    
    # Apply optimizations
    optimize_python_settings()
    optimize_audio_settings()
    optimize_system_priority()
    optimize_garbage_collection()
    check_network_settings()
    
    logger.info("=" * 60)
    logger.info("✅ Performance optimization completed!")
    
    display_performance_tips()
    
    logger.info("=" * 60)
    logger.info("🎯 Ready to run optimized LiveKit Agent")
    logger.info("   Start with: python simple_main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
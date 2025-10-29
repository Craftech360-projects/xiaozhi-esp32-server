#!/usr/bin/env python3
"""
Optimized Launcher for Simple LiveKit Agent
Runs performance optimizations before starting the agent
"""

import sys
import subprocess
import logging
import os

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def run_optimizations():
    """Run performance optimizations"""
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Running performance optimizations...")
    
    try:
        # Run optimization script
        result = subprocess.run([
            sys.executable, 'optimize_performance.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("✅ Performance optimizations completed successfully")
            return True
        else:
            logger.warning(f"⚠️ Optimization script returned code {result.returncode}")
            logger.warning(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Optimization script timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to run optimizations: {e}")
        return False

def start_agent():
    """Start the LiveKit agent"""
    logger = logging.getLogger(__name__)
    
    logger.info("🤖 Starting LiveKit Agent...")
    
    try:
        # Start the agent
        subprocess.run([sys.executable, 'simple_main.py'] + sys.argv[1:])
        
    except KeyboardInterrupt:
        logger.info("🛑 Agent stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start agent: {e}")
        return False
    
    return True

def main():
    """Main function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🎯 Optimized LiveKit Agent Launcher")
    logger.info("=" * 50)
    
    # Check if optimization should be skipped
    if '--skip-optimization' in sys.argv:
        logger.info("⏭️ Skipping optimizations (--skip-optimization flag)")
        sys.argv.remove('--skip-optimization')
    else:
        # Run optimizations
        optimization_success = run_optimizations()
        if not optimization_success:
            logger.warning("⚠️ Optimizations failed, but continuing anyway...")
    
    logger.info("=" * 50)
    
    # Start the agent
    start_agent()

if __name__ == "__main__":
    main()
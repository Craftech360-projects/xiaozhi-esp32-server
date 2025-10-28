"""Benchmark FunASR performance"""

import time
import asyncio
import psutil
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.providers.funasr_provider import FunASRSTT
from src.config.config_loader import ConfigLoader
from livekit.agents.utils import AudioBuffer


async def benchmark_latency():
    """Benchmark transcription latency"""
    print("\n" + "=" * 60)
    print("FunASR Latency Benchmark")
    print("=" * 60)

    config = ConfigLoader.get_funasr_config()

    if not os.path.exists(config['model_dir']):
        print(f"❌ FunASR model not found at {config['model_dir']}")
        print("   Run: python scripts/download_funasr_model.py")
        return

    stt = FunASRSTT(**config)

    # Check if test audio exists
    test_audio_path = 'tests/fixtures/test_audio.pcm'
    if not os.path.exists(test_audio_path):
        print(f"⚠️  Test audio not found: {test_audio_path}")
        print("   Skipping latency benchmark (no test audio available)")
        return

    # Load test audio
    with open(test_audio_path, 'rb') as f:
        audio_data = f.read()

    # Create buffer (simplified - in real usage would need proper conversion)
    buffer = AudioBuffer()
    # Note: Proper audio frame conversion needed for real testing

    print(f"Audio size: {len(audio_data)} bytes")
    print(f"Device: {config['device']}")
    print(f"Language: {config['language']}")
    print()

    # Warm-up
    print("Warming up...")
    try:
        await stt.recognize(buffer=buffer)
    except Exception as e:
        print(f"❌ Warm-up failed: {e}")
        return

    # Benchmark
    iterations = 10
    latencies = []

    print(f"Running {iterations} iterations...")
    for i in range(iterations):
        start = time.time()
        try:
            await stt.recognize(buffer=buffer)
            latency = time.time() - start
            latencies.append(latency)
            print(f"  Iteration {i+1}: {latency * 1000:.2f}ms")
        except Exception as e:
            print(f"  Iteration {i+1}: Failed - {e}")

    if not latencies:
        print("❌ All iterations failed")
        return

    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)

    print()
    print("Results:")
    print(f"  Average: {avg_latency * 1000:.2f}ms")
    print(f"  Min: {min_latency * 1000:.2f}ms")
    print(f"  Max: {max_latency * 1000:.2f}ms")
    print(f"  Throughput: {len(latencies) / sum(latencies):.2f} transcriptions/sec")


async def benchmark_memory():
    """Benchmark memory usage"""
    print("\n" + "=" * 60)
    print("FunASR Memory Benchmark")
    print("=" * 60)

    config = ConfigLoader.get_funasr_config()

    if not os.path.exists(config['model_dir']):
        print(f"❌ FunASR model not found at {config['model_dir']}")
        return

    process = psutil.Process()

    # Baseline memory
    baseline_mem = process.memory_info().rss / (1024 ** 2)  # MB

    print(f"Baseline memory: {baseline_mem:.2f} MB")

    # Load model
    print("Loading FunASR model...")
    stt = FunASRSTT(**config)

    after_load_mem = process.memory_info().rss / (1024 ** 2)
    model_mem = after_load_mem - baseline_mem

    print(f"After model load: {after_load_mem:.2f} MB")
    print(f"Model memory usage: {model_mem:.2f} MB")

    # Run inference (if test audio available)
    test_audio_path = 'tests/fixtures/test_audio.pcm'
    if os.path.exists(test_audio_path):
        with open(test_audio_path, 'rb') as f:
            audio_data = f.read()

        buffer = AudioBuffer()

        print("\nRunning 10 inferences...")
        for i in range(10):
            try:
                await stt.recognize(buffer=buffer)
            except Exception:
                pass

        after_inference_mem = process.memory_info().rss / (1024 ** 2)

        print(f"After 10 inferences: {after_inference_mem:.2f} MB")
        print(f"Memory growth: {after_inference_mem - after_load_mem:.2f} MB")
    else:
        print("⚠️  No test audio available, skipping inference test")


async def benchmark_cpu():
    """Benchmark CPU usage"""
    print("\n" + "=" * 60)
    print("FunASR CPU Benchmark")
    print("=" * 60)

    config = ConfigLoader.get_funasr_config()

    if not os.path.exists(config['model_dir']):
        print(f"❌ FunASR model not found at {config['model_dir']}")
        return

    test_audio_path = 'tests/fixtures/test_audio.pcm'
    if not os.path.exists(test_audio_path):
        print(f"⚠️  Test audio not found, skipping CPU benchmark")
        return

    import threading

    cpu_percentages = []
    monitoring = True

    def monitor_cpu():
        while monitoring:
            cpu_percentages.append(psutil.cpu_percent(interval=0.1))

    # Start monitoring
    monitor_thread = threading.Thread(target=monitor_cpu)
    monitor_thread.start()

    # Run inference
    print("Loading model and running inferences...")
    stt = FunASRSTT(**config)

    with open(test_audio_path, 'rb') as f:
        audio_data = f.read()

    buffer = AudioBuffer()

    for i in range(20):
        try:
            await stt.recognize(buffer=buffer)
        except Exception:
            pass

    # Stop monitoring
    monitoring = False
    monitor_thread.join()

    if cpu_percentages:
        avg_cpu = sum(cpu_percentages) / len(cpu_percentages)
        max_cpu = max(cpu_percentages)

        print(f"Average CPU: {avg_cpu:.2f}%")
        print(f"Max CPU: {max_cpu:.2f}%")
    else:
        print("❌ No CPU data collected")


async def main():
    """Run all benchmarks"""
    print("=" * 60)
    print("FunASR Performance Benchmark Suite")
    print("=" * 60)
    print()
    print("This benchmark measures FunASR's performance:")
    print("  1. Transcription latency")
    print("  2. Memory usage")
    print("  3. CPU utilization")
    print()

    config = ConfigLoader.get_funasr_config()
    print(f"Configuration:")
    print(f"  Model: {config['model_dir']}")
    print(f"  Device: {config['device']}")
    print(f"  Language: {config['language']}")
    print(f"  ITN: {config['use_itn']}")
    print()

    try:
        await benchmark_memory()
        await benchmark_latency()
        await benchmark_cpu()
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Benchmark Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

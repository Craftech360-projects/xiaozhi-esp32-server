"""
STT Provider Comparison Test for Kids' Voice Recognition
Tests multiple STT providers with kids' audio samples to find the best accuracy.

Usage:
    python test_stt_comparison.py <audio_file.wav>
    python test_stt_comparison.py --directory ./test_audio/
"""

import asyncio
import os
import sys
import io

# Fix Windows console encoding for unicode
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import wave
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime

# Import the transcription functions from agent.py
from agent import (
    transcribe_with_assemblyai,
    transcribe_with_deepgram,
    transcribe_with_groq_whisper,
    ASSEMBLYAI_AVAILABLE,
    DEEPGRAM_AVAILABLE
)

load_dotenv(".env")


def read_wav_file(filepath):
    """Read WAV file and return PCM bytes and sample rate"""
    with wave.open(str(filepath), 'rb') as wav_file:
        sample_rate = wav_file.getframerate()
        n_channels = wav_file.getnchannels()
        audio_bytes = wav_file.readframes(wav_file.getnframes())

        print(f"📂 Loaded: {filepath}")
        print(f"   Sample rate: {sample_rate}Hz")
        print(f"   Channels: {n_channels}")
        print(f"   Duration: {len(audio_bytes) / (sample_rate * n_channels * 2):.2f}s")

        return audio_bytes, sample_rate


async def test_all_providers(audio_file):
    """Test all available STT providers with the same audio file"""
    print(f"\n{'='*60}")
    print(f"Testing: {audio_file}")
    print(f"{'='*60}\n")

    # Read audio file
    try:
        audio_bytes, sample_rate = read_wav_file(audio_file)
    except Exception as e:
        print(f"❌ Error reading audio file: {e}")
        return None

    results = {}
    start_time = datetime.now()

    # Test AssemblyAI
    if ASSEMBLYAI_AVAILABLE and os.getenv("ASSEMBLYAI_API_KEY"):
        print("🔄 Testing AssemblyAI...")
        try:
            t_start = datetime.now()
            transcript = await transcribe_with_assemblyai(audio_bytes, sample_rate)
            t_end = datetime.now()
            latency = (t_end - t_start).total_seconds()
            results['assemblyai'] = {
                'transcript': transcript,
                'latency': latency,
                'status': 'success' if transcript else 'failed'
            }
            print(f"✅ AssemblyAI: {transcript} ({latency:.2f}s)")
        except Exception as e:
            results['assemblyai'] = {'error': str(e), 'status': 'error'}
            print(f"❌ AssemblyAI error: {e}")
    else:
        results['assemblyai'] = {'status': 'unavailable'}
        print("⚠️  AssemblyAI: Not configured")

    # Test Deepgram
    if DEEPGRAM_AVAILABLE and os.getenv("DEEPGRAM_API_KEY"):
        print("\n🔄 Testing Deepgram...")
        try:
            t_start = datetime.now()
            transcript = await transcribe_with_deepgram(audio_bytes, sample_rate)
            t_end = datetime.now()
            latency = (t_end - t_start).total_seconds()
            results['deepgram'] = {
                'transcript': transcript,
                'latency': latency,
                'status': 'success' if transcript else 'failed'
            }
            print(f"✅ Deepgram: {transcript} ({latency:.2f}s)")
        except Exception as e:
            results['deepgram'] = {'error': str(e), 'status': 'error'}
            print(f"❌ Deepgram error: {e}")
    else:
        results['deepgram'] = {'status': 'unavailable'}
        print("⚠️  Deepgram: Not configured")

    # Test Groq Whisper
    if os.getenv("GROQ_API_KEY"):
        print("\n🔄 Testing Groq Whisper...")
        try:
            t_start = datetime.now()
            transcript = await transcribe_with_groq_whisper(audio_bytes, sample_rate)
            t_end = datetime.now()
            latency = (t_end - t_start).total_seconds()
            results['groq'] = {
                'transcript': transcript,
                'latency': latency,
                'status': 'success' if transcript else 'failed'
            }
            print(f"✅ Groq Whisper: {transcript} ({latency:.2f}s)")
        except Exception as e:
            results['groq'] = {'error': str(e), 'status': 'error'}
            print(f"❌ Groq error: {e}")
    else:
        results['groq'] = {'status': 'unavailable'}
        print("⚠️  Groq: Not configured")

    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY - {audio_file.name}")
    print(f"{'='*60}")
    print(f"Total test time: {total_time:.2f}s\n")

    for provider, data in results.items():
        status = data.get('status', 'unknown')
        if status == 'success':
            print(f"✅ {provider.upper():15} {data['latency']:.2f}s")
            print(f"   \"{data['transcript']}\"")
        elif status == 'unavailable':
            print(f"⚠️  {provider.upper():15} Not configured")
        elif status == 'failed':
            print(f"❌ {provider.upper():15} Failed - no transcript")
        elif status == 'error':
            print(f"❌ {provider.upper():15} Error: {data.get('error', 'Unknown')}")
        print()

    return results


async def test_directory(directory):
    """Test all WAV files in a directory"""
    audio_files = list(Path(directory).glob("*.wav"))

    if not audio_files:
        print(f"❌ No WAV files found in {directory}")
        return

    print(f"Found {len(audio_files)} audio files to test")

    all_results = {}
    for audio_file in audio_files:
        results = await test_all_providers(audio_file)
        if results:
            all_results[str(audio_file)] = results

    # Save results to JSON
    output_file = Path(directory) / f"stt_comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    # Print recommendation
    print(f"\n{'='*60}")
    print("RECOMMENDATION")
    print(f"{'='*60}")

    # Count successes per provider
    provider_stats = {}
    for file_results in all_results.values():
        for provider, data in file_results.items():
            if provider not in provider_stats:
                provider_stats[provider] = {'success': 0, 'total': 0, 'latency': []}

            provider_stats[provider]['total'] += 1
            if data.get('status') == 'success':
                provider_stats[provider]['success'] += 1
                provider_stats[provider]['latency'].append(data['latency'])

    for provider, stats in provider_stats.items():
        if stats['success'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            avg_latency = sum(stats['latency']) / len(stats['latency'])
            print(f"{provider.upper():15} {success_rate:.1f}% success, {avg_latency:.2f}s avg latency")

    # Find best provider
    best_provider = max(
        [p for p, s in provider_stats.items() if s['success'] > 0],
        key=lambda p: provider_stats[p]['success'],
        default=None
    )

    if best_provider:
        print(f"\n🏆 Recommended: {best_provider.upper()}")
        print(f"   Update STT_PROVIDER={best_provider} in your .env file")


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Test single file:  python test_stt_comparison.py <audio_file.wav>")
        print("  Test directory:    python test_stt_comparison.py --directory ./test_audio/")
        sys.exit(1)

    if sys.argv[1] == "--directory":
        if len(sys.argv) < 3:
            print("❌ Please specify directory path")
            sys.exit(1)
        await test_directory(sys.argv[2])
    else:
        audio_file = Path(sys.argv[1])
        if not audio_file.exists():
            print(f"❌ File not found: {audio_file}")
            sys.exit(1)

        await test_all_providers(audio_file)


if __name__ == "__main__":
    asyncio.run(main())

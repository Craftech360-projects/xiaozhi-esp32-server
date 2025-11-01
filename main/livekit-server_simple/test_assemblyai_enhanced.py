"""
Test AssemblyAI with enhanced configuration for kids' speech.
Uses word boost to prioritize common kids' phrases.
"""

import assemblyai as aai
import os
from dotenv import load_dotenv

load_dotenv(".env")

# Configure API
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Audio file
audio_file = "hita3.wav"

print(f"Testing {audio_file} with AssemblyAI enhanced configuration...")
print("=" * 60)

# Test 1: Standard configuration (what we just tested)
print("\n1. Standard Configuration:")
config1 = aai.TranscriptionConfig(
    speech_model=aai.SpeechModel.best,
    punctuate=True,
    format_text=True
)
transcript1 = aai.Transcriber().transcribe(audio_file, config1)
print(f"   Result: {transcript1.text}")

# Test 2: With word boost for common kids' phrases
print("\n2. With Word Boost (common kids' phrases):")
config2 = aai.TranscriptionConfig(
    speech_model=aai.SpeechModel.best,
    punctuate=True,
    format_text=True,
    word_boost=[
        "play", "johnny", "yes", "papa", "mama",
        "song", "music", "game", "toy", "story"
    ],
    boost_param="high"  # How much to prioritize these words
)
transcript2 = aai.Transcriber().transcribe(audio_file, config2)
print(f"   Result: {transcript2.text}")

# Test 3: With language code specified
print("\n3. With English (India) language hint:")
config3 = aai.TranscriptionConfig(
    speech_model=aai.SpeechModel.best,
    punctuate=True,
    format_text=True,
    language_code="en",  # Force English
    word_boost=["play", "johnny", "yes", "papa"],
    boost_param="high"
)
transcript3 = aai.Transcriber().transcribe(audio_file, config3)
print(f"   Result: {transcript3.text}")

# Test 4: Nano model (faster, different training)
print("\n4. Using Nano model (lightweight):")
config4 = aai.TranscriptionConfig(
    speech_model=aai.SpeechModel.nano,
    punctuate=True,
    format_text=True,
    word_boost=["play", "johnny", "yes", "papa"],
    boost_param="high"
)
transcript4 = aai.Transcriber().transcribe(audio_file, config4)
print(f"   Result: {transcript4.text}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print(f"Expected: 'play johnny johnny yes papa'")
print("\nBest result:")
results = [
    ("Standard", transcript1.text),
    ("Word Boost", transcript2.text),
    ("Language Hint", transcript3.text),
    ("Nano Model", transcript4.text)
]

# Find closest match
for name, text in results:
    print(f"  {name:15} {text}")

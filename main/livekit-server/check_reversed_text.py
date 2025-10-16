"""
Analyze Qdrant chunks to detect which ones have reversed text
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
current_dir = Path(__file__).parent
load_dotenv(current_dir / '.env')

QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

def detect_reversed_text(text: str) -> bool:
    """Detect if text is reversed"""
    reversed_indicators = ['edarG', 'ecneicS', 'koobtxeT', 'ytisoiruC', 'dlroW']
    text_start = text[:200] if text else ""
    return any(indicator in text_start for indicator in reversed_indicators)

def analyze_qdrant_collection():
    """Analyze all chunks in Qdrant"""

    url = f"{QDRANT_URL}/collections/grade_06_science/points/scroll"
    headers = {
        "api-key": QDRANT_API_KEY,
        "Content-Type": "application/json"
    }

    total_chunks = 0
    reversed_chunks = 0
    normal_chunks = 0

    payload = {
        "limit": 100,
        "with_payload": True,
        "with_vector": False
    }

    print(f"\nAnalyzing Qdrant collection: grade_06_science")
    print(f"URL: {url}")
    print("-" * 80)

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    points = data.get('result', {}).get('points', [])

    print(f"\nFound {len(points)} chunks")
    print("-" * 80)

    for point in points:
        total_chunks += 1
        payload_data = point.get('payload', {})
        content = payload_data.get('content', '')
        chunk_id = payload_data.get('chunk_id', 'unknown')

        if detect_reversed_text(content):
            reversed_chunks += 1
            print(f"\n🔴 REVERSED - Chunk {chunk_id}")
            print(f"   First 100 chars: {content[:100]}")
        else:
            normal_chunks += 1
            print(f"\n✅ NORMAL - Chunk {chunk_id}")
            print(f"   First 100 chars: {content[:100]}")

    print("\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Reversed: {reversed_chunks} ({reversed_chunks/total_chunks*100:.1f}%)")
    print(f"  Normal: {normal_chunks} ({normal_chunks/total_chunks*100:.1f}%)")
    print("=" * 80)

if __name__ == "__main__":
    analyze_qdrant_collection()

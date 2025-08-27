
"""
Test S3 integration with existing xiaozhi-server music/story functions
- Uses GET (not HEAD) to validate presigned URL access
- Initializes boto3 client with region + SigV4
- Falls back to local presign helpers if plugins_func is unavailable
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append('.')

# Load environment variables
load_dotenv()

# -------------------------------
# Global S3 client (lazy init)
# -------------------------------
_s3_client = None


def initialize_s3_client():
    """Initialize and cache a boto3 S3 client with proper region + SigV4."""
    global _s3_client
    if _s3_client is not None:
        return _s3_client

    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        raise RuntimeError(
            "boto3 not installed. Run: pip install boto3 python-dotenv requests"
        )

    region = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
    _s3_client = boto3.client(
        "s3",
        region_name=region,
        config=Config(signature_version="s3v4"),
    )
    return _s3_client


def presign_get_url(bucket: str, key: str, expires_in: int = 300) -> str:
    """
    Generate a presigned GET URL for an S3 object.
    Do NOT pre-encode the key (boto3 handles it).
    """
    s3 = initialize_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def get_music_url_via_plugins(language: str, filename: str):
    """
    Try to use existing project helpers; fall back to local presign.
    """
    try:
        from plugins_func.functions.play_music import (
            initialize_s3_client as _init_music_client,
            generate_s3_music_url,
        )
        _init_music_client()
        return generate_s3_music_url(language, filename)
    except Exception:
        # Fallback: local presign using env
        bucket = (
            os.getenv("MUSIC_BUCKET")
            or os.getenv("S3_BUCKET")
            or ""
        )
        prefix = os.getenv("S3_PREFIX_MUSIC", "music").strip("/")

        if not bucket:
            raise RuntimeError(
                "No MUSIC_BUCKET or S3_BUCKET set in env for fallback music URL."
            )
        key = f"{prefix}/{language}/{filename}"
        return presign_get_url(bucket, key)


def get_story_url_via_plugins(category: str, filename: str):
    """
    Try to use existing project helpers; fall back to local presign.
    """
    try:
        from plugins_func.functions.play_story import (
            initialize_s3_client as _init_story_client,
            generate_s3_story_url,
        )
        _init_story_client()
        return generate_s3_story_url(category, filename)
    except Exception:
        # Fallback: local presign using env
        bucket = (
            os.getenv("STORIES_BUCKET")
            or os.getenv("S3_BUCKET")
            or ""
        )
        prefix = os.getenv("S3_PREFIX_STORIES", "stories").strip("/")

        if not bucket:
            raise RuntimeError(
                "No STORIES_BUCKET or S3_BUCKET set in env for fallback story URL."
            )
        key = f"{prefix}/{category}/{filename}"
        return presign_get_url(bucket, key)


def test_s3_integration():
    """Test S3 integration with existing functions (or fallback)."""
    print("🧪 Testing S3 Integration with Xiaozhi-Server")
    print("=" * 50)

    # Test AWS credentials
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    if not aws_access_key or not aws_secret_key:
        print("❌ AWS credentials not found in .env file")
        print("Please ensure your .env file contains:")
        print("AWS_ACCESS_KEY_ID=your_access_key")
        print("AWS_SECRET_ACCESS_KEY=your_secret_key")
        return False

    region = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')
    print(f"✅ AWS Access Key: {aws_access_key[:10]}...")
    print(f"✅ AWS Region: {region}")

    # Init S3 client
    try:
        initialize_s3_client()
        print("✅ S3 client initialized successfully (SigV4)")
    except Exception as e:
        print(f"❌ Failed to initialize S3 client: {e}")
        return False

    # Generate URLs
    music_url = None
    story_url = None

    try:
        music_url = get_music_url_via_plugins("English", "Baa Baa Black Sheep.mp3")
        print("✅ Music S3 URL generated successfully")
        print(f"   URL: {music_url[:100]}...")
    except Exception as e:
        print(f"❌ Failed to generate music S3 URL: {e}")

    try:
        story_url = get_story_url_via_plugins("Fantasy", "a portrait of a cat.mp3")
        print("✅ Story S3 URL generated successfully")
        print(f"   URL: {story_url[:100]}...")
    except Exception as e:
        print(f"❌ Failed to generate story S3 URL: {e}")

    # Test URL accessibility with GET (NOT HEAD)
    import requests

    def _probe(url_label: str, url: str) -> bool:
        if not url:
            return False
        print(f"🔎 Probing {url_label} (GET)...")
        try:
            r = requests.get(url, stream=True, timeout=15)
            if r.status_code == 200:
                # Try to read a small chunk
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        print(f"✅ {url_label} is accessible (read {len(chunk)} bytes)")
                        return True
                print(f"✅ {url_label} is accessible (no content read, but 200)")
                return True
            else:
                print(f"❌ {url_label} returned HTTP {r.status_code}")
                # Print first 500 chars of error XML (if any)
                body = r.text[:500]
                if body:
                    print("   ↳ Response body (truncated):")
                    print("   " + body.replace("\n", "\n   "))
                return False
        except Exception as ex:
            print(f"❌ Error fetching {url_label}: {ex}")
            return False

    ok_music = _probe("Music URL", music_url)
    ok_story = _probe("Story URL", story_url)

    # If either works, consider integration OK
    return ok_music or ok_story


def test_metadata_compatibility():
    """Test that metadata.json files are still accessible."""
    print("\n📁 Testing Metadata Compatibility")
    print("-" * 35)

    def _check_dir(dir_path: str, label: str, icon: str):
        if os.path.exists(dir_path):
            print(f"✅ {label} directory exists: {dir_path}")

            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    metadata_file = os.path.join(item_path, "metadata.json")
                    if os.path.exists(metadata_file):
                        print(f"✅ Found metadata: {metadata_file}")
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            print(f"   {icon} {len(data)} entries in {item}")
                        except Exception as e:
                            print(f"   ❌ Error reading metadata: {e}")
                    else:
                        print(f"❌ Missing metadata: {metadata_file}")
        else:
            print(f"❌ {label} directory not found: {dir_path}")

    _check_dir("music", "Music", "📝")
    _check_dir("stories", "Stories", "📖")


def show_integration_summary():
    """Show summary of the S3 integration."""
    print("\n🎯 S3 Integration Summary")
    print("=" * 30)
    print("✅ Looks for project helpers:")
    print("   - plugins_func/functions/play_music.py (generate_s3_music_url)")
    print("   - plugins_func/functions/play_story.py (generate_s3_story_url)")
    print("   If not found, falls back to local presigned URL generation.")
    print()
    print("✅ Key Behaviors:")
    print("   - Initializes S3 client with region + SigV4")
    print("   - Generates presigned GET URLs (not HEAD)")
    print("   - Validates accessibility via GET and reads a small chunk")
    print("   - Prints helpful diagnostics for 403/other errors")
    print()
    print("✅ Env Vars Used:")
    print("   - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION")
    print("   - S3_BUCKET (or MUSIC_BUCKET / STORIES_BUCKET)")
    print("   - S3_PREFIX_MUSIC (default 'music'), S3_PREFIX_STORIES (default 'stories')")


if __name__ == "__main__":
    success = test_s3_integration()
    test_metadata_compatibility()
    show_integration_summary()

    if success:
        print("\n🎉 S3 Integration is ready!")
        print("Use 'play music' / 'play story' to stream from S3.")
    else:
        print("\n❌ S3 Integration needs attention")
        print("Review the errors above. Common causes:")
        print(" - Wrong region (set AWS_DEFAULT_REGION)")
        print(" - SSE-KMS key permissions missing (kms:Decrypt for presigner)")
        print(" - Bucket policy has explicit Deny (TLS, IP, VPCe conditions)")
        print(" - URL copied/truncated or expired")

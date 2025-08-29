"""
CDN Test Script
Test CloudFront CDN integration
"""
from fastapi import FastAPI, Response
from dotenv import load_dotenv
import httpx
import asyncio

# Load environment variables first
load_dotenv()

# Now import CDN helper (after env vars are loaded)
from utils.cdn_helper import get_audio_url, get_cache_headers, cdn

app = FastAPI()

@app.get("/cdn-status")
async def cdn_status():
    """Check CDN configuration status"""
    return cdn.get_status()

@app.get("/test-audio-url/{audio_file}")
async def test_audio_url(audio_file: str):
    """Test audio URL generation"""
    url = get_audio_url(audio_file)
    return {
        "audio_file": audio_file,
        "generated_url": url,
        "cdn_enabled": cdn.is_cdn_enabled(),
        "cache_headers": get_cache_headers()
    }

@app.get("/test-audio-access/{audio_file}")
async def test_audio_access(audio_file: str):
    """Test actual audio file access through CDN"""
    url = get_audio_url(audio_file)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(url)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "accessible": response.status_code == 200,
                "content_type": response.headers.get("content-type"),
                "cache_status": response.headers.get("x-cache", "Unknown")
            }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "accessible": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
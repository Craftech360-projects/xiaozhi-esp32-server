#!/bin/bash
# Quick script to download ONLY English music files to save space
# Run this on the media server (192.168.1.99)

set -e  # Exit on error

echo "=================================================="
echo "Downloading English Music Files"
echo "=================================================="
echo ""
echo "This will download ONLY English music files"
echo "to save disk space (~50-100 MB)"
echo ""

# Configuration
export QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
export MEDIA_ROOT="${MEDIA_ROOT:-/var/www/html}"
export LANGUAGE_FILTER="English"
export USE_CDN="true"

echo "Configuration:"
echo "  Qdrant URL: $QDRANT_URL"
echo "  Destination: $MEDIA_ROOT"
echo "  Languages: English only"
echo ""

# Check if running on the correct server
current_ip=$(hostname -I | awk '{print $1}')
if [[ "$current_ip" != "192.168.1.99" ]]; then
    echo "⚠️  WARNING: This script should be run on 192.168.1.99 (media server)"
    echo "Current IP: $current_ip"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Check if Qdrant is accessible
if ! curl -s "$QDRANT_URL" > /dev/null 2>&1; then
    echo "❌ Cannot connect to Qdrant at $QDRANT_URL"
    echo ""
    echo "If Qdrant is on another server (192.168.1.2), either:"
    echo "  1. Set QDRANT_URL: QDRANT_URL=http://192.168.1.2:6333 $0"
    echo "  2. Or create SSH tunnel: ssh -L 6333:localhost:6333 user@192.168.1.2 -N"
    exit 1
fi

# Check Python and dependencies
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3"
    exit 1
fi

# Check if qdrant-client is installed
if ! python3 -c "import qdrant_client" 2>/dev/null; then
    echo "Installing qdrant-client..."
    pip3 install qdrant-client
fi

# Run download script
script_dir=$(dirname "$0")
python3 "$script_dir/download_media_files.py"

echo ""
echo "=================================================="
echo "✅ Download Complete!"
echo "=================================================="
echo ""
echo "Files are in: $MEDIA_ROOT/music/English/"
echo ""
echo "Next: Make sure HTTP server is running on port 8080"
echo "Test: curl -I http://localhost:8080/music/English/Twinkle%20Twinkle%20Little%20Star.mp3"

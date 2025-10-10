# Media File Downloader

Downloads music and story files from cloud storage (S3/CloudFront) to your media server based on Qdrant database index.

## Overview

This script reads the Qdrant database to get all indexed music and story files, then downloads them from cloud storage to your local media server.

## Prerequisites

1. **Python 3.7+** with required packages:
   ```bash
   pip install qdrant-client
   ```

2. **Qdrant database** must be accessible (default: http://localhost:6333)

3. **Write permissions** to the media server directory (default: /var/www/html)

## Usage

### Run on Media Server (192.168.1.99)

The script should be run **directly on the media server** where you want to store the files:

```bash
# Copy script to media server
scp download_media_files.py user@192.168.1.99:/tmp/

# SSH to media server
ssh user@192.168.1.99

# Install dependencies
pip3 install qdrant-client

# Run script with default settings (downloads to /var/www/html)
cd /tmp
python3 download_media_files.py

# Or specify custom destination
MEDIA_ROOT=/path/to/web/root python3 download_media_files.py
```

### Configuration Options

All configuration is via environment variables:

#### Required Settings

- `QDRANT_URL` - Qdrant server URL (default: `http://localhost:6333`)
  - If running from remote machine, use: `http://192.168.1.2:6333` or tunnel via SSH

#### Storage Settings

- `MEDIA_ROOT` - Destination directory (default: `/var/www/html`)
  ```bash
  MEDIA_ROOT=/opt/media python3 download_media_files.py
  ```

#### Language Filter (Save Space)

Download only specific languages:

```bash
# Download only English files
LANGUAGE_FILTER=English python3 download_media_files.py

# Download English and Hindi
LANGUAGE_FILTER="English,Hindi" python3 download_media_files.py

# Download all languages (default)
LANGUAGE_FILTER="" python3 download_media_files.py
```

Available languages in database:
- English (27 songs)
- Hindi
- Telugu
- Kannada
- Phonics
- Slokas
- Bhagavad Gita (40+ episodes)

#### Source Settings

- `USE_CDN` - Use CloudFront CDN vs direct S3 (default: `true`)
- `CLOUDFRONT_DOMAIN` - CloudFront domain (default: `dbtnllz9fcr1z.cloudfront.net`)
- `S3_BASE_URL` - Direct S3 URL (default: `https://cheeko-audio-files.s3.us-east-1.amazonaws.com`)

### Example: Download English Music Only

```bash
ssh user@192.168.1.99

# Set environment variables
export QDRANT_URL=http://192.168.1.2:6333
export MEDIA_ROOT=/var/www/html
export LANGUAGE_FILTER=English

# Run download
python3 download_media_files.py
```

## Output Structure

Files will be organized as:

```
/var/www/html/
├── music/
│   ├── English/
│   │   ├── Twinkle Twinkle Little Star.mp3
│   │   ├── Baby Shark Dance.mp3
│   │   └── ...
│   ├── Hindi/
│   │   └── ...
│   └── Telugu/
│       └── ...
└── stories/
    ├── English/
    └── ...
```

## Features

- ✅ **Smart Resume** - Skips already downloaded files
- ✅ **Language Filtering** - Download only needed languages to save space
- ✅ **Progress Tracking** - Shows download progress and statistics
- ✅ **Error Handling** - Continues on errors, reports failed downloads
- ✅ **Permission Checking** - Validates write access before downloading
- ✅ **CDN Support** - Uses CloudFront CDN for faster downloads

## Troubleshooting

### Permission Denied

Run with sudo or change MEDIA_ROOT to a writable location:

```bash
sudo python3 download_media_files.py
# OR
MEDIA_ROOT=$HOME/media python3 download_media_files.py
```

### Cannot Connect to Qdrant

If running script on media server (192.168.1.99), you need to connect to Qdrant on 192.168.1.2:

```bash
QDRANT_URL=http://192.168.1.2:6333 python3 download_media_files.py
```

Or set up SSH tunnel:

```bash
# On media server, create tunnel to Qdrant server
ssh -L 6333:localhost:6333 user@192.168.1.2 -N &

# Then run script (it will use localhost:6333 which tunnels to 192.168.1.2)
python3 download_media_files.py
```

### Disk Space Issues

Check available space:

```bash
df -h /var/www/html
```

Use language filter to download only needed files:

```bash
LANGUAGE_FILTER=English python3 download_media_files.py
```

Expected sizes:
- English music: ~50-100 MB (27 files)
- All music: ~500 MB - 1 GB (105 files)
- All music + stories: ~1-2 GB

## After Download

1. **Verify files were downloaded:**
   ```bash
   ls -lh /var/www/html/music/English/
   ```

2. **Set up HTTP server** (if not already running):

   **Python (simple, for testing):**
   ```bash
   cd /var/www/html
   python3 -m http.server 8080
   ```

   **Node.js (with CORS):**
   ```bash
   cd /var/www/html
   npx http-server -p 8080 --cors
   ```

   **Nginx (recommended for production):**
   ```nginx
   server {
       listen 8080;
       root /var/www/html;
       autoindex on;

       location / {
           add_header Access-Control-Allow-Origin *;
       }
   }
   ```

3. **Test access from LiveKit server:**
   ```bash
   # From 192.168.1.2 (LiveKit server)
   curl -I "http://192.168.1.99:8080/music/English/Twinkle%20Twinkle%20Little%20Star.mp3"
   # Should return: HTTP/1.1 200 OK
   ```

4. **Update .env** (already done):
   ```bash
   LOCAL_MEDIA_URL=http://192.168.1.99:8080
   ```

## Re-running the Script

Safe to run multiple times:
- Skips existing files (checks file size > 0)
- Only downloads new/missing files
- Updates progress statistics

```bash
python3 download_media_files.py
# Will skip already downloaded files
```

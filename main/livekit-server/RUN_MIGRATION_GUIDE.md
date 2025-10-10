# 🔄 Migration Scripts Execution Guide

Complete guide to run the migration scripts for offline operation.

## Prerequisites

### 1. Start Docker Services

```bash
cd d:\cheekofinal\xiaozhi-esp32-server\main\livekit-server

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                IMAGE                       STATUS
livekit-server      livekit/livekit-server     Up
qdrant-local        qdrant/qdrant              Up
ollama-llm          ollama/ollama              Up
media-server        nginx:alpine               Up
```

### 2. Pull Gemma3:1b Model

```bash
# This will download ~700MB
docker exec ollama-llm ollama pull gemma3:1b

# Verify it's downloaded
docker exec ollama-llm ollama list
```

### 3. Verify Python Dependencies

```bash
# Check if installed
python -c "import qdrant_client; import boto3; print('Dependencies OK')"

# If missing, install
pip install qdrant-client boto3
```

---

## Migration Script 1: Qdrant Collections

### Purpose
Migrates vector database collections (music and stories) from Qdrant Cloud to your local Qdrant instance.

### Run the Script

```bash
cd d:\cheekofinal\xiaozhi-esp32-server\main\livekit-server

# Run migration
python scripts/migrate_qdrant_collections.py
```

### Expected Output

```
============================================================
Qdrant Collection Migration Tool
============================================================
Connecting to Qdrant Cloud: https://...
✅ Connected to Qdrant Cloud
Connecting to Local Qdrant: http://localhost:6333
✅ Connected to Local Qdrant
Available collections in cloud: ...

Starting migration for collection: music_collection
Collection info: ...
Creating collection 'music_collection' in local Qdrant...
Collection 'music_collection' created successfully
Migrated 100 points...
Migrated 200 points...
✅ Migration complete for 'music_collection': 250 points migrated

Starting migration for collection: story_collection
...
✅ Migration complete for 'story_collection': 180 points migrated

============================================================
✅ Migration Complete!
Total points migrated: 430
Collections migrated: music_collection, story_collection
============================================================
```

### Verify Migration

```bash
# Check collections exist
curl http://localhost:6333/collections

# Should show:
# {
#   "collections": [
#     {"name": "music_collection"},
#     {"name": "story_collection"}
#   ]
# }
```

### Troubleshooting

**Error: Cannot connect to Qdrant Cloud**
- Check internet connection (required for this step)
- Verify credentials in script are correct

**Error: Cannot connect to Local Qdrant**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Check logs
docker logs qdrant-local

# Restart if needed
docker-compose restart qdrant
```

**Error: Collection already exists**
- This is OK! The script will append data
- To start fresh: Delete and recreate

---

## Migration Script 2: S3 Media Files

### Purpose
Downloads all music and story audio files from AWS S3 to local storage.

### Run the Script

```bash
cd d:\cheekofinal\xiaozhi-esp32-server\main\livekit-server

# Run download
python scripts/download_media_from_s3.py
```

### Expected Output

```
============================================================
S3 Media Download Tool
============================================================
Verifying AWS credentials...
✅ AWS credentials are valid

------------------------------------------------------------
Downloading from s3://cheeko-audio-files/music/ to local_media\music
Downloading: music/English/song1.mp3 (3.45 MB)
Downloading: music/English/song2.mp3 (4.21 MB)
...
✅ Downloaded 50 files (180.23 MB) from music/

------------------------------------------------------------
Downloading from s3://cheeko-audio-files/stories/ to local_media\stories
Downloading: stories/English/story1.mp3 (2.15 MB)
...
✅ Downloaded 30 files (95.67 MB) from stories/

============================================================
✅ Download Complete!
Total files downloaded: 80
Local media directory: D:\...\local_media
============================================================
```

### Verify Download

```bash
# Check files exist
dir local_media\music\English
dir local_media\stories\English

# Check media server works
curl http://localhost:8080/
```

### Troubleshooting

**Error: Invalid AWS credentials**
- Credentials in `.env` may be expired
- Contact admin for new credentials

**Error: Permission denied**
- Check AWS IAM permissions
- Verify S3 bucket access

**Files already exist**
- Script skips already downloaded files
- Safe to re-run

**Disk space issues**
```bash
# Check available space
dir

# Media files are typically:
# - Music: 50-100 files, 200-500 MB
# - Stories: 30-50 files, 100-200 MB
# - Total: ~500-700 MB needed
```

---

## Post-Migration Steps

### 1. Verify Local Services

```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test Qdrant
curl http://localhost:6333/collections

# Test Media Server
curl http://localhost:8080/music/

# Test all together
docker-compose ps
```

### 2. Update Configuration

Configuration should already be set in `.env`:

```env
# Qdrant (Local)
QDRANT_URL=http://localhost:6333

# Media (Local)
USE_CDN=false
LOCAL_MEDIA_URL=http://192.168.1.2:8080

# LLM (Local)
LLM_PROVIDER=ollama
LLM_MODEL=gemma3:1b
```

### 3. Start LiveKit Server

```bash
cd d:\cheekofinal\xiaozhi-esp32-server\main\livekit-server

# Start in dev mode
python main.py dev
```

### 4. Test Everything

1. Start a conversation
2. Ask to play music
3. Ask to play a story
4. Verify everything works offline

---

## Common Issues

### Issue: Qdrant migration fails

**Solution 1: Check connectivity**
```bash
# Test cloud connection
curl -I https://a2482b9f-2c29-476e-9ff0-741aaaaf632e.eu-west-1-0.aws.cloud.qdrant.io

# Test local connection
curl http://localhost:6333/collections
```

**Solution 2: Restart Qdrant**
```bash
docker-compose restart qdrant
sleep 5
python scripts/migrate_qdrant_collections.py
```

### Issue: S3 download fails

**Solution 1: Check internet**
```bash
ping s3.amazonaws.com
```

**Solution 2: Use AWS CLI**
```bash
# Install AWS CLI if needed
pip install awscli

# Configure credentials
aws configure

# Manual download
aws s3 sync s3://cheeko-audio-files/music/ local_media/music/
aws s3 sync s3://cheeko-audio-files/stories/ local_media/stories/
```

### Issue: Out of disk space

**Solution: Clean up space**
```bash
# Check disk space
dir

# Clean Docker
docker system prune -a

# Clean old files
# (Be careful!)
```

---

## Success Checklist

After running both scripts, verify:

- [ ] Qdrant local has music_collection
- [ ] Qdrant local has story_collection
- [ ] local_media/music/ has audio files
- [ ] local_media/stories/ has audio files
- [ ] Media server serves files at http://localhost:8080
- [ ] Ollama has gemma3:1b model
- [ ] All Docker services are running
- [ ] Configuration updated in `.env`

---

## Next Steps

Once migrations are complete:

1. **Test offline mode**
   ```bash
   # Disconnect from internet
   # Start LiveKit server
   python main.py dev
   ```

2. **Monitor performance**
   ```bash
   docker stats
   ```

3. **Review logs**
   ```bash
   docker-compose logs -f
   ```

4. **Enjoy offline operation!** 🎉

---

## Summary

```bash
# Complete migration in 3 commands:

# 1. Start services
docker-compose up -d

# 2. Migrate Qdrant
python scripts/migrate_qdrant_collections.py

# 3. Download media
python scripts/download_media_from_s3.py

# Done! Now start server:
python main.py dev
```

---

**Questions?** See [OFFLINE_SETUP_GUIDE.md](OFFLINE_SETUP_GUIDE.md) for more help!

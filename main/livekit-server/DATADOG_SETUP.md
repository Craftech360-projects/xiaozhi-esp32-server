# Datadog Integration Setup Guide

This guide explains how to integrate Datadog logging with your LiveKit server for comprehensive log monitoring.

## Overview

The LiveKit server uses **Direct Log Streaming** to send logs to Datadog without requiring the Datadog Agent. This approach is lightweight and perfect for local development and production environments.

## Features

- ✅ Real-time log streaming to Datadog
- ✅ Structured JSON logging with context
- ✅ Automatic error tracking with stack traces
- ✅ Session-specific context (room_name, device_mac, session_id)
- ✅ Configurable log levels and tags
- ✅ Works in local and production environments
- ✅ No agent installation required

## Prerequisites

1. **Datadog Account**: Sign up at [datadoghq.com](https://www.datadoghq.com) (free trial available)
2. **API Key**: Obtain from Datadog Dashboard → Organization Settings → API Keys

## Installation

### 1. Install Dependencies

The required packages are already in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Packages installed:
- `datadog-api-client` - Direct API communication
- `ddtrace` - APM and tracing support (optional)

### 2. Configure Environment Variables

Add the following to your `.env` file:

```env
# Datadog Configuration
DATADOG_ENABLED=true
DATADOG_API_KEY=your_datadog_api_key_here
DATADOG_APP_KEY=your_datadog_app_key_here  # Optional, for dashboards/monitors

# Service Configuration
DD_SERVICE=livekit-server
DD_ENV=local  # local, staging, production
DD_VERSION=1.0.0
DD_SITE=datadoghq.com  # or datadoghq.eu for EU region

# Optional: Custom tags (comma-separated)
DD_TAGS=team:ai,project:xiaozhi
```

### 3. Get Your Datadog API Key

**Step-by-step:**

1. Log in to [Datadog](https://app.datadoghq.com)
2. Navigate to **Organization Settings** (bottom left)
3. Click **API Keys** tab
4. Click **+ New Key** or copy an existing key
5. Paste the key into your `.env` file

**For EU region:** Use `DD_SITE=datadoghq.eu`

## Configuration

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATADOG_ENABLED` | Yes | `false` | Enable/disable Datadog logging |
| `DATADOG_API_KEY` | Yes | - | Your Datadog API key |
| `DATADOG_APP_KEY` | No | - | App key for dashboards (optional) |
| `DD_SERVICE` | No | `livekit-server` | Service name in Datadog |
| `DD_ENV` | No | `local` | Environment (local/staging/production) |
| `DD_VERSION` | No | `1.0.0` | Application version |
| `DD_SITE` | No | `datadoghq.com` | Datadog site (US: .com, EU: .eu) |
| `DD_TAGS` | No | - | Custom tags (comma-separated) |

### Log Levels

Logs are sent to Datadog at the following levels:

- `DEBUG` - Detailed debugging (not sent by default)
- `INFO` - Normal operations (sent to Datadog)
- `WARNING` - Non-critical issues (sent to Datadog)
- `ERROR` - Application errors (sent to Datadog)
- `CRITICAL` - System failures (sent to Datadog)

## Usage

### Basic Usage

Once configured, all logs are automatically sent to Datadog:

```python
import logging

logger = logging.getLogger("agent")
logger.info("Session started")  # → Sent to Datadog
logger.error("Connection failed", exc_info=True)  # → Includes stack trace
```

### Context-Aware Logging

Logs automatically include context when available:

```python
# Logs will include room_name, device_mac, session_id
logger.info(f"Starting agent in room: {room_name}")
```

Context fields added automatically:
- `room_name` - LiveKit room identifier
- `device_mac` - Device MAC address
- `session_id` - Session identifier
- `hostname` - Server hostname
- `service` - Service name (livekit-server)
- `env` - Environment (local/staging/production)

### Example Log in Datadog

```json
{
  "timestamp": "2025-10-28T10:30:45Z",
  "status": "info",
  "service": "livekit-server",
  "env": "local",
  "hostname": "localhost",
  "message": "Starting agent in room: abc123_00163eacb538",
  "room_name": "abc123_00163eacb538",
  "device_mac": "00:16:3e:ac:b5:38",
  "ddsource": "python",
  "ddtags": "env:local,service:livekit-server,version:1.0.0"
}
```

## Testing the Integration

### 1. Start the Server

```bash
python main.py start
```

**Expected output:**
```
✅ Datadog logging enabled: service=livekit-server, env=local, site=datadoghq.com
Starting agent...
```

If Datadog is disabled:
```
ℹ️ Datadog logging is disabled (set DATADOG_ENABLED=true to enable)
```

### 2. Verify Logs in Datadog

1. Go to [Datadog Logs](https://app.datadoghq.com/logs)
2. Use the search query: `service:livekit-server`
3. You should see logs appearing in real-time

**Filter examples:**
- By environment: `env:local`
- By room: `room_name:abc123*`
- By device: `device_mac:00:16:3e:*`
- Errors only: `status:error`

### 3. Test Log Streaming

Run this Python script to test:

```bash
python -c "
from src.config.datadog_config import DatadogConfig
import logging

# Setup Datadog
DatadogConfig.setup_logging()

# Test logging
logger = logging.getLogger('test')
logger.info('🧪 Datadog test log from livekit-server')
logger.warning('⚠️ This is a warning test')
logger.error('❌ This is an error test')

print('✅ Test logs sent! Check Datadog in 10-30 seconds.')
"
```

## Viewing Logs in Datadog

### Log Explorer

Navigate to **Logs → Explorer** to view all logs:

1. **Search by service**: `service:livekit-server`
2. **Filter by environment**: Add facet `env:local`
3. **Filter by device**: Add facet `device_mac:*`
4. **View errors only**: `status:error`

### Creating Dashboards

1. Go to **Dashboards → New Dashboard**
2. Add widgets:
   - **Timeseries**: Log volume over time
   - **Top List**: Most active rooms
   - **Table**: Recent errors

**Example queries:**
```
# Total logs per minute
service:livekit-server | group by status

# Errors by room
service:livekit-server status:error | group by room_name

# Device activity
service:livekit-server | group by device_mac
```

### Setting Up Alerts

Create monitors to get notified of issues:

1. Go to **Monitors → New Monitor → Logs**
2. Define query: `service:livekit-server status:error`
3. Set threshold: Alert when error count > 10 in 5 minutes
4. Configure notifications (email, Slack, etc.)

## Advanced Features

### APM (Application Performance Monitoring)

For detailed performance tracking, use `ddtrace`:

```python
# In your code
from ddtrace import tracer

with tracer.trace("music_service.initialize"):
    await music_service.initialize()
```

### Custom Metrics

Track custom metrics:

```python
from datadog import statsd

statsd.increment('livekit.sessions.started')
statsd.histogram('livekit.session.duration', session_duration)
```

### Log Sampling

For high-volume logs, configure sampling in `datadog_config.py`:

```python
# Only send 10% of INFO logs
if record.levelno == logging.INFO and random.random() > 0.1:
    return
```

## Troubleshooting

### Logs Not Appearing in Datadog

1. **Check API key**: Verify in .env file
2. **Check enabled status**: `DATADOG_ENABLED=true`
3. **Check site**: Use `.eu` for EU accounts
4. **Wait 10-30 seconds**: Logs are sent in batches
5. **Check console output**: Look for error messages

**Common errors:**

```
⚠️ Datadog API key not configured or invalid
→ Solution: Set valid DATADOG_API_KEY in .env

⚠️ Failed to initialize Datadog logging: API key invalid
→ Solution: Check API key format and permissions

⚠️ Datadog API client not installed
→ Solution: pip install datadog-api-client ddtrace
```

### High Log Volume

If you're sending too many logs:

1. Increase log level: Set handler level to `WARNING` or `ERROR`
2. Use log sampling (see Advanced Features)
3. Filter out verbose loggers:

```python
logging.getLogger('livekit').setLevel(logging.WARNING)
```

### Performance Impact

Direct log streaming has minimal performance impact:
- Logs sent asynchronously (non-blocking)
- Failed log sends don't crash the application
- Approximately 1-5ms overhead per log message

## Production Deployment

### Recommended Settings

For production environments:

```env
# Production .env
DATADOG_ENABLED=true
DATADOG_API_KEY=your_production_api_key
DD_SERVICE=livekit-server
DD_ENV=production
DD_VERSION=1.0.0
DD_TAGS=region:us-east,team:ai
```

### Log Retention

Datadog log retention depends on your plan:
- **Free**: 3 days
- **Pro**: 15 days (default)
- **Enterprise**: Custom retention

### Cost Optimization

To reduce Datadog costs:
1. Filter out verbose logs (DEBUG level)
2. Use log sampling for high-volume logs
3. Set up log exclusion filters in Datadog UI
4. Archive logs to S3 for long-term storage

## Local Development

For local development, Datadog is optional:

```env
# Disable Datadog for local development
DATADOG_ENABLED=false
```

Logs will still appear in console output.

## Summary

✅ **Installed**: Dependencies added to requirements.txt
✅ **Configured**: datadog_config.py module created
✅ **Integrated**: main.py updated to initialize Datadog
✅ **Ready**: Set DATADOG_ENABLED=true and add your API key

**Next Steps:**
1. Get your Datadog API key
2. Update `.env` with your credentials
3. Restart the server
4. View logs in Datadog dashboard

## Support

- **Datadog Docs**: https://docs.datadoghq.com/logs/
- **API Reference**: https://docs.datadoghq.com/api/latest/logs/
- **Python Integration**: https://docs.datadoghq.com/logs/log_collection/python/

For issues, check the console output for Datadog-specific warnings and errors.

# Memory Management Guide

## Overview

The Xiaozhi server supports three different memory management systems to handle conversation history and provide personalized AI interactions. This guide explains how to configure and use each memory option.

## Memory Options

### 1. No Memory (nomem) - Default
**Use Case**: Testing, privacy-focused deployments, or when you want each conversation to be independent.

**Configuration:**
```yaml
selected_module:
  Memory: nomem

Memory:
  nomem:
    type: nomem
```

**Behavior:**
- No conversation history is saved
- Each interaction starts fresh
- No memory files created
- Fastest response times
- Complete privacy (no data persistence)

---

### 2. Local Short-term Memory (mem_local_short) - Recommended
**Use Case**: Privacy-focused deployments with conversation continuity, local data control.

**Configuration:**
```yaml
selected_module:
  Memory: mem_local_short

Memory:
  mem_local_short:
    type: mem_local_short
    llm: GroqLLM  # Uses your existing LLM for memory processing
```

**Features:**
- **Local Storage**: Memory files saved in `data/` directory
- **AI-Powered Compression**: Uses LLM to intelligently summarize conversations
- **Privacy-First**: All data stays on your server
- **Smart Retention**: Keeps important information, removes outdated content
- **File Format**: YAML files for easy inspection and backup

**How It Works:**
1. Conversations are stored locally in YAML format
2. When memory gets large, the system uses your configured LLM to summarize
3. Important information is retained while old/irrelevant data is compressed
4. Memory is organized by user/device ID for multi-user support

**Storage Location:**
```
data/
├── memory_short_term.yaml  # Main memory file
└── .config.yaml           # Your configuration
```

---

### 3. Cloud Memory (mem0ai) - Advanced
**Use Case**: Advanced memory features, when you want sophisticated memory management.

**Configuration:**
```yaml
selected_module:
  Memory: mem0ai

Memory:
  mem0ai:
    type: mem0ai
    api_key: your_mem0ai_api_key_here  # Get from https://app.mem0.ai/dashboard/api-keys
```

**Features:**
- **Advanced AI Memory**: Uses Mem0.ai's sophisticated memory algorithms
- **Free Tier**: 1000 API calls per month
- **Cloud-Based**: Memory stored externally
- **Enhanced Context**: Better long-term memory management

**Requirements:**
- Mem0.ai API key (free tier available)
- Internet connection for API calls
- External data storage (consider privacy implications)

---

## Configuration Steps

### Step 1: Choose Your Memory Type
Decide which memory system fits your needs:
- **nomem**: No memory, maximum privacy
- **mem_local_short**: Local memory, good balance
- **mem0ai**: Cloud memory, advanced features

### Step 2: Update selected_module
Add the Memory module to your `selected_module` section:

```yaml
selected_module:
  LLM: GroqLLM
  TTS: elevenlabs
  VAD: SileroVAD
  ASR: SherpaASR
  Memory: mem_local_short  # Add this line
```

### Step 3: Configure Memory Settings
Add the corresponding Memory configuration section:

```yaml
Memory:
  mem_local_short:
    type: mem_local_short
    llm: GroqLLM  # Uses your existing LLM
```

### Step 4: Restart the Server
Restart your Xiaozhi server to apply the new memory configuration.

---

## Memory File Management

### Local Memory Files
When using `mem_local_short`, memory files are stored in:
```
data/memory_short_term.yaml
```

### Backup and Restore
To backup your memory:
```bash
# Backup
cp data/memory_short_term.yaml data/memory_backup_$(date +%Y%m%d).yaml

# Restore
cp data/memory_backup_20241201.yaml data/memory_short_term.yaml
```

### Clear Memory
To reset all memory:
```bash
# Stop the server first
rm data/memory_short_term.yaml
# Restart the server
```

---

## Troubleshooting

### Memory Not Working
1. **Check Configuration**: Ensure `Memory` is in `selected_module`
2. **Check File Permissions**: Ensure the server can write to `data/` directory
3. **Check Logs**: Look for memory-related errors in server logs

### Memory Files Too Large
The `mem_local_short` system automatically compresses memory when it gets large. If you're still having issues:
1. Check available disk space
2. Consider clearing old memory files
3. Verify your LLM is working for memory compression

### API Errors (mem0ai)
1. **Check API Key**: Verify your Mem0.ai API key is correct
2. **Check Quota**: Ensure you haven't exceeded your API limits
3. **Check Internet**: Verify internet connectivity

---

## Best Practices

### For Privacy-Focused Deployments
- Use `mem_local_short` for local data control
- Regularly backup memory files
- Monitor disk usage

### For Development/Testing
- Use `nomem` for clean testing environments
- Switch to `mem_local_short` for integration testing

### For Production
- Use `mem_local_short` for most deployments
- Consider `mem0ai` only if you need advanced features and accept external data storage
- Set up regular memory file backups
- Monitor memory file sizes and server performance

---

## Security Considerations

### Local Memory (mem_local_short)
- ✅ Data stays on your server
- ✅ Full control over memory files
- ✅ No external API dependencies
- ⚠️ Ensure proper file system permissions

### Cloud Memory (mem0ai)
- ⚠️ Data sent to external service
- ⚠️ Requires API key management
- ⚠️ Subject to external service terms
- ⚠️ Internet dependency

### No Memory (nomem)
- ✅ Maximum privacy
- ✅ No data persistence
- ✅ No external dependencies
- ❌ No conversation continuity

---

## Example Configurations

### Complete Local Setup
```yaml
selected_module:
  LLM: GroqLLM
  TTS: elevenlabs
  VAD: SileroVAD
  ASR: SherpaASR
  Memory: mem_local_short

Memory:
  mem_local_short:
    type: mem_local_short
    llm: GroqLLM
```

### Privacy-First Setup
```yaml
selected_module:
  LLM: GroqLLM
  TTS: elevenlabs
  VAD: SileroVAD
  ASR: SherpaASR
  Memory: nomem

Memory:
  nomem:
    type: nomem
```

### Cloud-Enhanced Setup
```yaml
selected_module:
  LLM: GroqLLM
  TTS: elevenlabs
  VAD: SileroVAD
  ASR: SherpaASR
  Memory: mem0ai

Memory:
  mem0ai:
    type: mem0ai
    api_key: sk_your_mem0ai_key_here
```
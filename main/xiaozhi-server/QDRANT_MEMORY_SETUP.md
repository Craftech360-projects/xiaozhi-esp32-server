# Qdrant Vector Database Memory Provider Setup Guide

## Overview

This guide shows you how to implement a **FREE** memory system using Qdrant vector database instead of mem0ai. This approach gives you full control over your data with no API limits.

## Architecture Comparison

### Current: Mem0ai Approach
```
Conversation → Mem0 API → Processing → Vector Storage → Results
             (Costs $$)
```

### New: Direct Qdrant Approach
```
Conversation → Your Code → Embeddings → Qdrant → Results
             (FREE!)
```

## Prerequisites

1. **Qdrant Account** (Choose one):
   - Qdrant Cloud: https://cloud.qdrant.io (Free tier: 1GB, 1M vectors)
   - Self-hosted: Docker container (Unlimited, local)

2. **Python Dependencies**:
   ```bash
   pip install qdrant-client sentence-transformers
   ```

## Implementation Steps

### Step 1: Create Qdrant Memory Provider

Create file: `/core/providers/memory/qdrant/qdrant_memory.py`

```python
import traceback
import uuid
from datetime import datetime
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from ..base import MemoryProviderBase, logger
from core.utils.util import check_model_key

TAG = __name__

class MemoryProvider(MemoryProviderBase):
    """Direct Qdrant memory provider - no mem0ai needed!"""
    
    def __init__(self, config, summary_memory=None):
        super().__init__(config)
        
        # Qdrant configuration
        self.url = config.get("url", "http://localhost:6333")  # Local or cloud URL
        self.api_key = config.get("api_key", None)  # Only needed for cloud
        self.collection_name = config.get("collection_name", "xiaozhi_memories")
        self.embedding_model_name = config.get("embedding_model", "all-MiniLM-L6-v2")
        self.embedding_size = config.get("embedding_size", 384)
        self.use_qdrant = True
        
        try:
            # Initialize Qdrant client
            if self.api_key:
                # Cloud Qdrant
                self.client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key,
                )
            else:
                # Local Qdrant
                self.client = QdrantClient(url=self.url)
            
            # Create collection if not exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_size,
                        distance=Distance.COSINE
                    )
                )
                logger.bind(tag=TAG).info(f"Created collection: {self.collection_name}")
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
            logger.bind(tag=TAG).info("Successfully connected to Qdrant")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to initialize Qdrant: {str(e)}")
            self.use_qdrant = False
    
    def _format_conversation(self, msgs) -> str:
        """Convert messages to searchable text"""
        parts = []
        for msg in msgs[-10:]:  # Last 10 messages for context
            if msg.role != "system":
                parts.append(f"{msg.role}: {msg.content}")
        return "\n".join(parts)
    
    def _extract_key_points(self, conversation: str) -> str:
        """Extract important information from conversation"""
        # Simple extraction - you can enhance this
        lines = conversation.split('\n')
        key_points = []
        
        for line in lines:
            # Look for user preferences, names, facts
            if any(keyword in line.lower() for keyword in [
                'my name is', 'i like', 'i prefer', 'i am', 
                'remember', 'don\'t forget', 'important'
            ]):
                key_points.append(line)
        
        return '\n'.join(key_points) if key_points else conversation
    
    async def save_memory(self, msgs):
        """Save conversation memory to Qdrant"""
        if not self.use_qdrant or len(msgs) < 2:
            return None
        
        try:
            # Format conversation
            full_conversation = self._format_conversation(msgs)
            key_points = self._extract_key_points(full_conversation)
            
            # Generate embedding from key points
            embedding = self.embedding_model.encode(key_points).tolist()
            
            # Create point
            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "user_id": self.role_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "conversation": full_conversation[:2000],  # Store up to 2000 chars
                    "key_points": key_points[:1000],
                    "message_count": len(msgs)
                }
            )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.bind(tag=TAG).debug(f"Saved memory: {point_id}")
            return point_id
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to save memory: {str(e)}")
            return None
    
    async def query_memory(self, query: str) -> str:
        """Search memories based on query"""
        if not self.use_qdrant:
            return ""
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search with user filter
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=self.role_id)
                        )
                    ]
                ),
                limit=5
            )
            
            if not results:
                return ""
            
            # Format memories
            memories = []
            for hit in results:
                payload = hit.payload
                timestamp = payload.get("timestamp", "")
                key_points = payload.get("key_points", "")
                score = hit.score
                
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_time = timestamp
                    
                    memory_text = f"[{formatted_time}] (Relevance: {score:.2f}) {key_points}"
                    memories.append((timestamp, memory_text))
            
            # Sort by time (newest first)
            memories.sort(key=lambda x: x[0], reverse=True)
            
            return "\n".join(f"- {m[1]}" for m in memories)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to query memory: {str(e)}")
            return ""
```

### Step 2: Update Configuration

Add to `config.yaml`:

```yaml
Memory:
  # Direct Qdrant - completely free!
  qdrant_direct:
    type: qdrant
    # For Qdrant Cloud (free tier)
    url: "https://YOUR-CLUSTER-URL.qdrant.io"
    api_key: "YOUR-QDRANT-API-KEY"
    collection_name: "xiaozhi_memories"
    embedding_model: "all-MiniLM-L6-v2"  # Or "paraphrase-multilingual-MiniLM-L12-v2" for multilingual
    embedding_size: 384  # Must match model output
    
  # For local Qdrant (Docker)
  qdrant_local:
    type: qdrant
    url: "http://localhost:6333"
    # No API key needed for local
    collection_name: "xiaozhi_memories"
    embedding_model: "all-MiniLM-L6-v2"
    embedding_size: 384
```

### Step 3: Set Up Qdrant

#### Option A: Qdrant Cloud (Recommended for beginners)
1. Sign up at https://cloud.qdrant.io
2. Create a free cluster
3. Get your URL and API key
4. Add to config.yaml

#### Option B: Local Qdrant with Docker
```bash
# Run Qdrant locally
docker run -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### Step 4: Update selected_modules

In `config.yaml`, change:
```yaml
selected_modules:
  Memory: qdrant_direct  # or qdrant_local
```

## Cost Comparison

| Solution | Monthly Cost | API Limits | Data Control |
|----------|-------------|------------|--------------|
| mem0ai + their storage | $0-20 | 1000 calls | No |
| mem0ai + your Qdrant | $0-20 | 1000 calls | Yes |
| **Direct Qdrant (This guide)** | **$0** | **Unlimited** | **Yes** |
| Direct Pinecone | $0 | 1M vectors | Yes |

## Features Comparison

| Feature | mem0ai | Direct Qdrant |
|---------|--------|---------------|
| Automatic memory extraction | ✅ Advanced | ⚠️ Basic (customizable) |
| Setup complexity | ✅ Easy | ⚠️ Moderate |
| Cost | ❌ Paid | ✅ Free |
| API limits | ❌ Yes | ✅ No |
| Customization | ❌ Limited | ✅ Full control |
| Privacy | ❌ External API | ✅ Your infrastructure |

## Advanced Features

### 1. Enhanced Memory Extraction
```python
def _extract_key_points(self, conversation: str) -> str:
    """Enhanced extraction with categories"""
    key_info = {
        "personal": [],  # Names, age, location
        "preferences": [],  # Likes, dislikes
        "facts": [],  # Important information
        "context": []  # Current topics
    }
    
    # Add your extraction logic here
    # Can even use a small local LLM for extraction
    
    return format_key_info(key_info)
```

### 2. Memory Summarization
```python
async def summarize_old_memories(self):
    """Periodically summarize old memories to save space"""
    # Get old memories
    # Use LLM to summarize
    # Replace with summary
```

### 3. Memory Categories
```python
# Store different types of memories
payload = {
    "category": "preference",  # or "fact", "event", "emotion"
    "importance": 0.8,  # 0-1 scale
    "expires_at": "2024-12-31"  # Optional expiry
}
```

## Testing Your Implementation

```python
# Test script: test_qdrant_memory.py
import asyncio
from core.providers.memory.qdrant.qdrant_memory import MemoryProvider

async def test():
    config = {
        "url": "http://localhost:6333",
        "collection_name": "test_memories"
    }
    
    memory = MemoryProvider(config)
    memory.role_id = "test_user"
    
    # Test save
    class Message:
        def __init__(self, role, content):
            self.role = role
            self.content = content
    
    msgs = [
        Message("user", "My name is John"),
        Message("assistant", "Nice to meet you, John!"),
        Message("user", "I love pizza and hate mushrooms")
    ]
    
    await memory.save_memory(msgs)
    
    # Test query
    result = await memory.query_memory("What food does the user like?")
    print(f"Memory result: {result}")

asyncio.run(test())
```

## Troubleshooting

### Issue: "Connection refused"
- Ensure Qdrant is running
- Check URL and port
- For Docker: `docker ps` to verify

### Issue: "Embedding size mismatch"
- Verify embedding_size matches your model
- all-MiniLM-L6-v2: 384
- all-mpnet-base-v2: 768

### Issue: "No memories returned"
- Check user_id (role_id) is consistent
- Verify embeddings are being created
- Check Qdrant dashboard for data

## Migration from mem0ai

1. Export existing memories (if possible)
2. Install this Qdrant provider
3. Update config.yaml
4. Restart service
5. New memories will use Qdrant

## Conclusion

This implementation gives you:
- ✅ **FREE unlimited memory storage**
- ✅ **Full control over your data**
- ✅ **No API rate limits**
- ✅ **Customizable memory extraction**
- ✅ **Works with local or cloud Qdrant**

The only trade-off is slightly simpler memory extraction compared to mem0ai's advanced AI, but you can enhance this as needed!
import json
import asyncio
import aiohttp
import hashlib
from typing import List, Dict, Any, Optional
from core.providers.memory.base import MemoryProviderBase
from config.logger import setup_logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

TAG = __name__
logger = setup_logging()


class MemoryProvider(MemoryProviderBase):
    """
    RAG Memory Provider for Mathematics Education
    Integrates with manager-api's RAG system for educational query processing
    """
    
    def __init__(self, config, summary_memory=None):
        super().__init__(config)
        self.manager_api_base_url = config.get("manager-api", {}).get("base_url", "")
        self.api_timeout = config.get("rag", {}).get("timeout", 30)
        
        # Redis caching configuration
        self.redis_config = config.get("redis", {})
        self.redis_enabled = self.redis_config.get("enabled", False) and REDIS_AVAILABLE
        self.redis_client = None
        self.cache_ttl = self.redis_config.get("ttl", 3600)  # 1 hour default
        self.cache_key_prefix = self.redis_config.get("key_prefix", "rag_math:")
        
        self.educational_keywords = {
            "math", "mathematics", "number", "addition", "subtraction", "multiplication", 
            "division", "fraction", "decimal", "geometry", "angle", "perimeter", "area",
            "prime", "factor", "pattern", "data", "graph", "symmetry", "integer",
            "exercise", "problem", "solve", "calculate", "find", "what is", "how to",
            "explain", "definition", "formula", "equation"
        }
        
        # Initialize Redis connection if enabled
        if self.redis_enabled:
            asyncio.create_task(self._init_redis())
        else:
            if not REDIS_AVAILABLE:
                logger.bind(tag=TAG).warning("Redis caching disabled: aioredis not installed")
            else:
                logger.bind(tag=TAG).info("Redis caching disabled in configuration")
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_host = self.redis_config.get("host", "localhost")
            redis_port = self.redis_config.get("port", 6379)
            redis_password = self.redis_config.get("password", "")
            redis_db = self.redis_config.get("db", 0)
            
            if redis_password:
                self.redis_client = redis.Redis(
                    host=redis_host, port=redis_port, password=redis_password, db=redis_db,
                    decode_responses=True
                )
            else:
                self.redis_client = redis.Redis(
                    host=redis_host, port=redis_port, db=redis_db,
                    decode_responses=True
                )
                
            # Test the connection
            await self.redis_client.ping()
            logger.bind(tag=TAG).info(f"Redis caching initialized: {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to initialize Redis: {str(e)}")
            self.redis_enabled = False
            self.redis_client = None

    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
        return f"{self.cache_key_prefix}query:{query_hash}"

    async def _get_cached_result(self, query: str) -> Optional[str]:
        """Get cached result for query"""
        if not self.redis_enabled or not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_cache_key(query)
            cached_result = await self.redis_client.get(cache_key)
            
            if cached_result:
                logger.bind(tag=TAG).info(f"Cache hit for query: {query[:50]}...")
                return cached_result
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Redis get error: {str(e)}")
            
        return None

    async def _cache_result(self, query: str, result: str):
        """Cache query result"""
        if not self.redis_enabled or not self.redis_client:
            return
            
        try:
            cache_key = self._generate_cache_key(query)
            await self.redis_client.setex(cache_key, self.cache_ttl, result)
            logger.bind(tag=TAG).debug(f"Cached result for query: {query[:50]}...")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Redis set error: {str(e)}")

    async def save_memory(self, msgs):
        """
        Save conversation context - for RAG, this is mainly for conversation continuity
        """
        try:
            # For educational RAG, we don't need to save every message
            # Just maintain conversation context
            logger.bind(tag=TAG).debug("RAG Math memory save called")
            return "rag_math_context"
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error saving RAG math memory: {str(e)}")
            return None
    
    async def query_memory(self, query: str) -> str:
        """
        Main RAG query processing - searches educational content and returns enhanced response
        """
        try:
            logger.bind(tag=TAG).info(f"Processing RAG math query: {query[:100]}...")
            
            # Check if this is an educational query
            if not self._is_educational_query(query):
                logger.bind(tag=TAG).debug("Non-educational query, skipping RAG")
                return ""
            
            # Try to get cached result first
            cached_result = await self._get_cached_result(query)
            if cached_result:
                return cached_result
            
            # Call manager-api RAG search endpoint
            search_results = await self._search_educational_content(query)
            
            if not search_results or "relevant_chunks" not in search_results:
                logger.bind(tag=TAG).info("No relevant educational content found")
                return ""
            
            # Process search results into enhanced context
            enhanced_context = self._build_educational_context(query, search_results)
            
            # Cache the result for future queries
            if enhanced_context:
                await self._cache_result(query, enhanced_context)
            
            logger.bind(tag=TAG).info(f"RAG enhanced context generated: {len(enhanced_context)} chars")
            return enhanced_context
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in RAG math query processing: {str(e)}")
            return ""
    
    def _is_educational_query(self, query: str) -> bool:
        """
        Detect if query is educational/mathematical in nature
        """
        query_lower = query.lower()
        
        # Check for educational keywords
        for keyword in self.educational_keywords:
            if keyword in query_lower:
                return True
        
        # Check for mathematical patterns
        import re
        if re.search(r'\d+\s*[\+\-\*\/\=]\s*\d+', query):  # Mathematical expressions
            return True
        if re.search(r'\b(chapter|exercise|problem|question|lesson)\b', query_lower):
            return True
            
        return False
    
    async def _search_educational_content(self, query: str) -> Dict[str, Any]:
        """
        Call manager-api RAG search endpoint
        """
        try:
            search_endpoint = f"{self.manager_api_base_url}/api/rag/search"
            
            search_payload = {
                "query": query,
                "subject": "mathematics",
                "standard": 6,
                "limit": 5,
                "include_metadata": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    search_endpoint, 
                    json=search_payload,
                    timeout=aiohttp.ClientTimeout(total=self.api_timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.bind(tag=TAG).debug(f"RAG search successful: {len(result.get('relevant_chunks', []))} chunks found")
                        return result
                    else:
                        logger.bind(tag=TAG).warning(f"RAG search failed: {response.status}")
                        return {}
        
        except asyncio.TimeoutError:
            logger.bind(tag=TAG).error("RAG search timeout")
            return {}
        except Exception as e:
            logger.bind(tag=TAG).error(f"RAG search error: {str(e)}")
            return {}
    
    def _build_educational_context(self, query: str, search_results: Dict[str, Any]) -> str:
        """
        Build enhanced educational context from search results
        """
        try:
            chunks = search_results.get("relevant_chunks", [])
            if not chunks:
                return ""
            
            # Build structured context
            context_parts = []
            context_parts.append("=== EDUCATIONAL CONTEXT (NCERT Mathematics Standard 6) ===")
            context_parts.append(f"Query: {query}")
            context_parts.append("")
            
            for i, chunk in enumerate(chunks[:3], 1):  # Limit to top 3 results
                content = chunk.get("content", "")
                metadata = chunk.get("metadata", {})
                
                context_parts.append(f"--- Relevant Content {i} ---")
                
                # Add source information
                if metadata:
                    chapter = metadata.get("chapter_title", "")
                    content_type = metadata.get("content_type", "")
                    if chapter:
                        context_parts.append(f"Source: {chapter}")
                    if content_type:
                        context_parts.append(f"Type: {content_type}")
                
                # Add content
                context_parts.append(f"Content: {content[:500]}...")  # Limit content length
                context_parts.append("")
            
            # Add instruction for LLM
            context_parts.append("=== INSTRUCTION ===")
            context_parts.append("Use the above educational content to provide accurate, age-appropriate answers for a Standard 6 student.")
            context_parts.append("Include step-by-step explanations when needed.")
            context_parts.append("Reference the chapter/source when possible.")
            context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error building educational context: {str(e)}")
            return ""
    
    def init_memory(self, role_id, llm, **kwargs):
        """Initialize memory provider with role and LLM"""
        super().init_memory(role_id, llm, **kwargs)
        logger.bind(tag=TAG).info(f"RAG Math memory provider initialized for role: {role_id}")

    async def close(self):
        """Clean up Redis connection"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.bind(tag=TAG).info("Redis connection closed")
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error closing Redis connection: {str(e)}")
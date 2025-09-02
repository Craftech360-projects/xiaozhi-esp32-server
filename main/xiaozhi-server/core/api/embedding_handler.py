import asyncio
import json
import traceback
from typing import List, Dict, Any
from aiohttp import web
from sentence_transformers import SentenceTransformer
from config.logger import setup_logging

TAG = __name__

class EmbeddingHandler:
    """
    Embedding Handler for BAAI/bge-large-en-v1.5 model
    Provides embeddings API endpoint compatible with OpenAI format
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            self.logger.bind(tag=TAG).info("Loading BAAI/bge-large-en-v1.5 embedding model...")
            self.model = SentenceTransformer("BAAI/bge-large-en-v1.5")
            self.logger.bind(tag=TAG).info("Embedding model loaded successfully")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to load embedding model: {e}")
            traceback.print_exc()
    
    async def handle_embeddings(self, request: web.Request) -> web.Response:
        """Handle embedding generation requests"""
        try:
            if request.method == "OPTIONS":
                return self._cors_response()
            
            if request.method != "POST":
                return self._error_response("Method not allowed", 405)
            
            # Check if model is loaded
            if self.model is None:
                return self._error_response("Embedding model not loaded", 503)
            
            # Parse request body
            try:
                data = await request.json()
            except json.JSONDecodeError:
                return self._error_response("Invalid JSON in request body", 400)
            
            # Extract parameters
            input_texts = data.get("input", [])
            model_name = data.get("model", "BAAI/bge-large-en-v1.5")
            encoding_format = data.get("encoding_format", "float")
            
            # Validate input
            if not input_texts:
                return self._error_response("No input texts provided", 400)
            
            # Handle both string and list inputs
            if isinstance(input_texts, str):
                input_texts = [input_texts]
            elif not isinstance(input_texts, list):
                return self._error_response("Input must be string or list of strings", 400)
            
            # Validate text count
            if len(input_texts) > 100:
                return self._error_response("Too many input texts (max 100)", 400)
            
            self.logger.bind(tag=TAG).info(f"Generating embeddings for {len(input_texts)} texts")
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(input_texts)
            
            # Format response according to OpenAI format
            response_data = {
                "object": "list",
                "data": [],
                "model": model_name,
                "usage": {
                    "prompt_tokens": sum(len(text.split()) for text in input_texts),
                    "total_tokens": sum(len(text.split()) for text in input_texts)
                }
            }
            
            for i, embedding in enumerate(embeddings):
                response_data["data"].append({
                    "object": "embedding",
                    "index": i,
                    "embedding": embedding
                })
            
            return self._success_response(response_data)
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error processing embedding request: {e}")
            traceback.print_exc()
            return self._error_response(f"Internal server error: {str(e)}", 500)
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for input texts"""
        try:
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self.model.encode, texts
            )
            
            # Convert numpy arrays to lists and ensure float type
            embeddings_list = []
            for embedding in embeddings:
                embedding_list = [float(x) for x in embedding.tolist()]
                embeddings_list.append(embedding_list)
            
            self.logger.bind(tag=TAG).info(f"Generated {len(embeddings_list)} embeddings, dimension: {len(embeddings_list[0])}")
            return embeddings_list
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error generating embeddings: {e}")
            raise
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle health check requests"""
        try:
            if request.method == "OPTIONS":
                return self._cors_response()
            
            health_data = {
                "status": "healthy" if self.model is not None else "unhealthy",
                "model": "BAAI/bge-large-en-v1.5",
                "model_loaded": self.model is not None,
                "embedding_dimension": 1024 if self.model is not None else None
            }
            
            status_code = 200 if self.model is not None else 503
            return self._success_response(health_data, status_code)
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error in health check: {e}")
            return self._error_response("Health check failed", 500)
    
    def _success_response(self, data: Dict[str, Any], status_code: int = 200) -> web.Response:
        """Create success response with CORS headers"""
        response = web.json_response(data, status=status_code)
        self._add_cors_headers(response)
        return response
    
    def _error_response(self, message: str, status_code: int = 400) -> web.Response:
        """Create error response with CORS headers"""
        error_data = {
            "error": {
                "message": message,
                "type": "invalid_request_error",
                "code": status_code
            }
        }
        response = web.json_response(error_data, status=status_code)
        self._add_cors_headers(response)
        return response
    
    def _cors_response(self) -> web.Response:
        """Create CORS preflight response"""
        response = web.Response(status=200)
        self._add_cors_headers(response)
        return response
    
    def _add_cors_headers(self, response: web.Response):
        """Add CORS headers to response"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '86400'
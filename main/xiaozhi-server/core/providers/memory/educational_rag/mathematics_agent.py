"""
Mathematics Expert Agent
Specialized agent for handling Class 6 Mathematics questions using RAG
"""

import asyncio
from typing import Dict, Any, List, Optional
from config.logger import setup_logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from config.config_loader import load_config
from core.providers.llm.openai.openai import LLMProvider

TAG = __name__
logger = setup_logging()

class MathematicsAgent:
    """Expert agent specialized in Class 6 Mathematics using RAG database"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collection_name = 'class-6-mathematics'
        self.qdrant_client = None
        self.embedding_model = None
        self.llm_provider = None
        
        # Initialize components
        self._initialize_qdrant()
        self._initialize_embedding_model()
        self._initialize_llm_provider()
    
    def _initialize_qdrant(self):
        """Initialize Qdrant client"""
        try:
            qdrant_url = self.config.get('qdrant_url')
            qdrant_api_key = self.config.get('qdrant_api_key')
            
            if qdrant_url and qdrant_api_key:
                self.qdrant_client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key
                )
                logger.bind(tag=TAG).info("[MATH-AGENT] Qdrant client initialized")
            else:
                logger.bind(tag=TAG).error("[MATH-AGENT] Missing Qdrant configuration")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MATH-AGENT] Qdrant initialization error: {e}")
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer model"""
        try:
            model_name = self.config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
            self.embedding_model = SentenceTransformer(model_name)
            logger.bind(tag=TAG).info(f"[MATH-AGENT] Embedding model loaded: {model_name}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MATH-AGENT] Embedding model error: {e}")
    
    def _initialize_llm_provider(self):
        """Initialize LLM provider for generating responses"""
        try:
            full_config = load_config()
            selected_llm = full_config.get('selected_module', {}).get('LLM', 'openai')
            
            if ('LLM' in full_config and selected_llm in full_config['LLM']):
                provider_config = full_config['LLM'][selected_llm]
                self.llm_provider = LLMProvider(provider_config)
                logger.bind(tag=TAG).info(f"[MATH-AGENT] LLM provider initialized: {selected_llm}")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MATH-AGENT] LLM provider error: {e}")
    
    async def answer_question(self, query: str, routing_info: Dict[str, Any] = None) -> str:
        """
        Answer mathematics question using RAG
        
        Args:
            query (str): Mathematics question
            routing_info (Dict): Additional routing information
            
        Returns:
            str: Child-friendly mathematics answer
        """
        try:
            logger.bind(tag=TAG).info(f"[MATH-AGENT] Processing query: {query[:50]}...")
            
            # Retrieve relevant mathematics content
            context_chunks = await self._retrieve_context(query)
            
            if not context_chunks:
                return await self._generate_fallback_response(query)
            
            # Generate response using LLM with context
            response = await self._generate_response_with_context(query, context_chunks)
            
            return self._format_child_friendly_response(response, query)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MATH-AGENT] Error answering question: {e}")
            return self._get_error_response()
    
    async def _retrieve_context(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant context from mathematics RAG database"""
        try:
            if not self.qdrant_client or not self.embedding_model:
                return []
            
            # Generate query embedding
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Search in mathematics collection
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=self.config.get('max_results', 5),
                score_threshold=self.config.get('score_threshold', 0.2)
            )
            
            # Extract relevant chunks
            context_chunks = []
            for result in search_results:
                context_chunks.append({
                    'text': result.payload.get('text', ''),
                    'metadata': result.payload,
                    'score': result.score
                })
            
            logger.bind(tag=TAG).info(f"[MATH-AGENT] Retrieved {len(context_chunks)} context chunks")
            return context_chunks
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MATH-AGENT] Context retrieval error: {e}")
            return []
    
    async def _generate_response_with_context(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate response using LLM with retrieved context"""
        
        # Prepare context for LLM
        context_text = self._format_context_for_llm(context_chunks)
        
        system_prompt = """You are Cheeko, a helpful mathematics tutor for Class 6 students (age 11-12).

Your personality:
- Enthusiastic about mathematics and problem-solving
- Use clear, age-appropriate language for 11-12 year olds
- Explain concepts step-by-step when needed
- Make mathematics interesting and relatable
- Encourage learning and curiosity

When answering:
1. Give clear, accurate explanations
2. Use examples from daily life that Class 6 students can relate to
3. Break down complex concepts into simpler parts
4. Be encouraging and supportive
5. Keep responses concise but informative (50-100 words)

Make mathematics engaging and help students understand concepts clearly!"""

        user_prompt = f"""Based on this mathematics content from the Class 6 textbook:

{context_text}

Please answer this student's question in a child-friendly way:
{query}

Remember: Keep it simple, encouraging, and fun!"""

        try:
            if self.llm_provider:
                response = self.llm_provider.response_no_stream(system_prompt, user_prompt)
                return response.strip()
            else:
                return self._get_basic_response(query, context_chunks)
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MATH-AGENT] LLM generation error: {e}")
            return self._get_basic_response(query, context_chunks)
    
    def _format_context_for_llm(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved context for LLM prompt"""
        formatted_context = []
        
        for i, chunk in enumerate(context_chunks[:3], 1):  # Use top 3 chunks
            metadata = chunk.get('metadata', {})
            chapter = metadata.get('chapter_title', 'Unknown Chapter')
            content_type = metadata.get('content_category', 'content')
            
            formatted_context.append(
                f"[Context {i} from {chapter} - {content_type}]\n{chunk['text']}\n"
            )
        
        return "\n".join(formatted_context)
    
    def _get_basic_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate basic response when LLM is not available"""
        if context_chunks:
            # Use the best matching chunk
            best_chunk = context_chunks[0]
            text = best_chunk['text'][:300]  # Limit length
            
            return f"Great question! Based on our Class 6 mathematics textbook: {text}... Would you like to know more about this topic?"
        else:
            return self._get_fallback_response_sync(query)
    
    async def _generate_fallback_response(self, query: str) -> str:
        """Generate fallback response when no context is found"""
        return self._get_fallback_response_sync(query)
    
    def _get_fallback_response_sync(self, query: str) -> str:
        """Synchronous fallback response for Class 6 students"""
        math_keywords = {
            'fraction': "Fractions represent parts of a whole. For example, if you divide a pizza into 8 slices and eat 3, you've eaten 3/8 of the pizza.",
            'addition': "Addition means combining numbers to find their total. For example, 25 + 17 = 42. You can add from left to right or use column method.",
            'subtraction': "Subtraction means taking away one number from another. For example, 50 - 23 = 27. It's the opposite of addition.",
            'multiplication': "Multiplication is repeated addition. 6 × 4 means adding 6 four times: 6+6+6+6 = 24. It helps solve problems quickly.",
            'division': "Division means splitting into equal groups. 20 ÷ 4 = 5 means dividing 20 into 4 equal groups of 5 each."
        }
        
        query_lower = query.lower()
        for keyword, response in math_keywords.items():
            if keyword in query_lower:
                return response
        
        return "Mathematics helps us solve problems and understand patterns in our daily life. What specific math topic would you like to learn about?"
    
    def _format_child_friendly_response(self, response: str, query: str) -> str:
        """Ensure response is child-friendly and encouraging"""
        if not response.startswith(('Great', 'Wow', 'Awesome', 'Fantastic', 'I love')):
            response = f"Great question! {response}"
        
        if not response.endswith(('?', '!')):
            response += " What else would you like to learn about mathematics?"
        
        return response
    
    def _get_error_response(self) -> str:
        """Response when there's an error"""
        return "I'm having trouble with that question right now. Can you try asking about mathematics topics like numbers, shapes, or arithmetic? I'd love to help you learn!"
    
    async def get_topic_summary(self, topic: str) -> str:
        """Get summary of a specific mathematics topic"""
        try:
            summary_query = f"explain {topic} definition examples"
            context_chunks = await self._retrieve_context(summary_query)
            
            if context_chunks:
                return await self._generate_response_with_context(
                    f"Explain {topic} for a Class 6 student", 
                    context_chunks
                )
            else:
                return f"I'd love to explain {topic}! This is an important mathematics topic for Class 6. Can you ask a specific question about {topic}?"
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MATH-AGENT] Topic summary error: {e}")
            return f"Let me help you learn about {topic}! What specific question do you have about this topic?"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of mathematics agent"""
        return {
            'status': 'healthy' if all([self.qdrant_client, self.embedding_model, self.llm_provider]) else 'degraded',
            'qdrant_connected': self.qdrant_client is not None,
            'embedding_model_loaded': self.embedding_model is not None,
            'llm_provider_available': self.llm_provider is not None,
            'collection_name': self.collection_name
        }
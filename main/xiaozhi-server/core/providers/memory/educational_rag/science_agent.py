"""
Science Expert Agent
Specialized agent for handling Class 6 Science questions using RAG
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

class ScienceAgent:
    """Expert agent specialized in Class 6 Science using RAG database"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collection_name = 'class-6-science'
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
                logger.bind(tag=TAG).info("[SCIENCE-AGENT] Qdrant client initialized")
            else:
                logger.bind(tag=TAG).error("[SCIENCE-AGENT] Missing Qdrant configuration")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[SCIENCE-AGENT] Qdrant initialization error: {e}")
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer model"""
        try:
            model_name = self.config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
            self.embedding_model = SentenceTransformer(model_name)
            logger.bind(tag=TAG).info(f"[SCIENCE-AGENT] Embedding model loaded: {model_name}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"[SCIENCE-AGENT] Embedding model error: {e}")
    
    def _initialize_llm_provider(self):
        """Initialize LLM provider for generating responses"""
        try:
            full_config = load_config()
            selected_llm = full_config.get('selected_module', {}).get('LLM', 'openai')
            
            if ('LLM' in full_config and selected_llm in full_config['LLM']):
                provider_config = full_config['LLM'][selected_llm]
                self.llm_provider = LLMProvider(provider_config)
                logger.bind(tag=TAG).info(f"[SCIENCE-AGENT] LLM provider initialized: {selected_llm}")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[SCIENCE-AGENT] LLM provider error: {e}")
    
    async def answer_question(self, query: str, routing_info: Dict[str, Any] = None) -> str:
        """
        Answer science question using RAG
        
        Args:
            query (str): Science question
            routing_info (Dict): Additional routing information
            
        Returns:
            str: Child-friendly science answer
        """
        try:
            logger.bind(tag=TAG).info(f"[SCIENCE-AGENT] Processing query: {query[:50]}...")
            
            # Retrieve relevant science content
            context_chunks = await self._retrieve_context(query)
            
            if not context_chunks:
                return await self._generate_fallback_response(query)
            
            # Generate response using LLM with context
            response = await self._generate_response_with_context(query, context_chunks)
            
            return self._format_child_friendly_response(response, query)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[SCIENCE-AGENT] Error answering question: {e}")
            return self._get_error_response()
    
    async def _retrieve_context(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant context from science RAG database"""
        try:
            if not self.qdrant_client or not self.embedding_model:
                return []
            
            # Generate query embedding
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Search in science collection
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
            
            logger.bind(tag=TAG).info(f"[SCIENCE-AGENT] Retrieved {len(context_chunks)} context chunks")
            return context_chunks
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[SCIENCE-AGENT] Context retrieval error: {e}")
            return []
    
    async def _generate_response_with_context(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate response using LLM with retrieved context"""
        
        # Prepare context for LLM
        context_text = self._format_context_for_llm(context_chunks)
        
        system_prompt = """You are Cheeko, a knowledgeable science tutor for Class 6 students (age 11-12).

Your personality:
- Passionate about science and discovery
- Use clear, scientific language appropriate for 11-12 year olds
- Explain scientific concepts with real-world examples
- Encourage scientific thinking and observation
- Make learning exciting and engaging

When answering:
1. Provide accurate scientific explanations
2. Use examples from nature and daily life that students can observe
3. Explain the 'why' and 'how' behind phenomena
4. Be encouraging and foster curiosity
5. Keep responses informative but concise (50-100 words)

Help students develop a love for science and understand the world around them!"""

        user_prompt = f"""Based on this science content from the Class 6 textbook:

{context_text}

Please answer this student's question in a child-friendly way:
{query}

Remember: Make science exciting, use simple examples, and encourage their curiosity!"""

        try:
            if self.llm_provider:
                response = self.llm_provider.response_no_stream(system_prompt, user_prompt)
                return response.strip()
            else:
                return self._get_basic_response(query, context_chunks)
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[SCIENCE-AGENT] LLM generation error: {e}")
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
            
            return f"Great science question! Based on our Class 6 science textbook: {text}... Would you like to explore more about this fascinating topic?"
        else:
            return self._get_fallback_response_sync(query)
    
    async def _generate_fallback_response(self, query: str) -> str:
        """Generate fallback response when no context is found"""
        return self._get_fallback_response_sync(query)
    
    def _get_fallback_response_sync(self, query: str) -> str:
        """Synchronous fallback response for common science topics"""
        science_keywords = {
            'plant': "Plants are living organisms that make their own food through photosynthesis. They use sunlight, water, and carbon dioxide to produce glucose and oxygen. Plants have roots, stems, leaves, and often flowers or fruits.",
            'animal': "Animals are living organisms that cannot make their own food and must eat other organisms. They have different body systems for breathing, digestion, circulation, and reproduction. Animals are classified into groups like mammals, birds, reptiles, etc.",
            'food': "Food provides nutrients that our body needs for energy, growth, and staying healthy. We need carbohydrates for energy, proteins for growth and repair, fats for energy storage, vitamins and minerals for proper body functions.",
            'water': "Water is essential for all life. It exists in three states: solid (ice), liquid (water), and gas (water vapor). Water cycle includes evaporation, condensation, and precipitation. Our body is about 70% water.",
            'light': "Light is a form of energy that travels in straight lines. The sun is our main source of natural light. Light can be reflected, refracted, and absorbed. We see objects when light reflects off them and enters our eyes.",
            'air': "Air is a mixture of gases including nitrogen (78%), oxygen (21%), and other gases. We need oxygen for breathing. Air has weight and takes up space. Moving air creates wind."
        }
        
        query_lower = query.lower()
        for keyword, response in science_keywords.items():
            if keyword in query_lower:
                return f"Great science question! {response}"
        
        return "That's an interesting science question! Science helps us understand how things work in nature and our daily life. What specific science topic would you like to explore?"
    
    def _format_child_friendly_response(self, response: str, query: str) -> str:
        """Ensure response is child-friendly and encouraging"""
        if not response.startswith(('Wow', 'Amazing', 'Great', 'Fantastic', 'I love')):
            response = f"Wow, great science question! {response}"
        
        if not response.endswith(('?', '!')):
            response += " What other amazing things in nature are you curious about?"
        
        return response
    
    def _get_error_response(self) -> str:
        """Response when there's an error"""
        return "I'm having trouble with that question right now. Can you try asking about plants, animals, food, or other exciting things you see in nature? I'd love to explore science with you!"
    
    async def get_topic_summary(self, topic: str) -> str:
        """Get summary of a specific science topic"""
        try:
            summary_query = f"explain {topic} definition examples"
            context_chunks = await self._retrieve_context(summary_query)
            
            if context_chunks:
                return await self._generate_response_with_context(
                    f"Explain {topic} for a Class 6 student", 
                    context_chunks
                )
            else:
                return f"I'd love to explore {topic} with you! This is such an interesting science topic. What specific question do you have about {topic}?"
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[SCIENCE-AGENT] Topic summary error: {e}")
            return f"Let me help you discover the amazing world of {topic}! What specific question do you have about this topic?"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of science agent"""
        return {
            'status': 'healthy' if all([self.qdrant_client, self.embedding_model, self.llm_provider]) else 'degraded',
            'qdrant_connected': self.qdrant_client is not None,
            'embedding_model_loaded': self.embedding_model is not None,
            'llm_provider_available': self.llm_provider is not None,
            'collection_name': self.collection_name
        }
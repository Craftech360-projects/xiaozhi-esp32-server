"""
LLM Manager Agent - Routes queries to appropriate subject expert agents
Uses the xiaozhi-server's LLM provider to make intelligent routing decisions
"""

import json
import asyncio
from typing import Dict, Any, Optional, Tuple
from config.logger import setup_logging
from config.config_loader import load_config
from core.providers.llm.openai.openai import LLMProvider

TAG = __name__
logger = setup_logging()

class LLMManagerAgent:
    """Manager agent that uses LLM to route queries to appropriate subject experts"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.subjects = config.get('subjects', {})
        self.llm_provider = None
        
        # Initialize LLM provider
        self._initialize_llm_provider()
    
    def _initialize_llm_provider(self):
        """Initialize LLM provider using xiaozhi-server's config"""
        try:
            full_config = load_config()
            selected_llm = full_config.get('selected_module', {}).get('LLM', 'openai')
            
            if ('LLM' in full_config and selected_llm in full_config['LLM']):
                provider_config = full_config['LLM'][selected_llm]
                self.llm_provider = LLMProvider(provider_config)
                logger.bind(tag=TAG).info(f"[MANAGER] LLM provider initialized: {selected_llm}")
            else:
                logger.bind(tag=TAG).error(f"[MANAGER] LLM provider not found: {selected_llm}")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MANAGER] Failed to initialize LLM provider: {e}")
    
    async def route_query(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Route query to appropriate subject expert agent
        
        Args:
            query (str): Student's question
            
        Returns:
            Tuple[str, Dict[str, Any]]: (subject, routing_info)
        """
        try:
            logger.bind(tag=TAG).info(f"[MANAGER] Routing query: {query[:50]}...")
            
            # Use LLM to determine the subject
            subject = await self._classify_subject_with_llm(query)
            
            # Get routing information
            routing_info = self._get_routing_info(subject, query)
            
            logger.bind(tag=TAG).info(f"[MANAGER] Query routed to: {subject}")
            return subject, routing_info
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MANAGER] Routing error: {e}")
            # Default to mathematics if routing fails
            return 'mathematics', {'confidence': 0.5, 'reason': 'fallback'}
    
    async def _classify_subject_with_llm(self, query: str) -> str:
        """Use LLM to classify query into subject categories"""
        
        system_prompt = """You are an educational subject classifier for Class 6 students (age 11-12).
Your task is to identify if a question is educational and which subject it belongs to.

Available categories:
- mathematics: Numbers, arithmetic, fractions, geometry, patterns, algebra, data handling, measurements, shapes, angles, area, perimeter
- science: Living organisms, food, plants, animals, human body, materials, changes, motion, light, electricity, magnets, environment
- non-educational: Music, games, stories, entertainment, or any non-academic topics

Respond with ONLY one word: mathematics, science, or non-educational.

Examples:
- "What are fractions?" → mathematics
- "How do plants grow?" → science  
- "What is 5 + 3?" → mathematics
- "Why do we need food?" → science
- "Play music" → non-educational
- "Tell me a story" → non-educational
- "What are nutrients?" → science
- "Draw a triangle" → mathematics

If the query is clearly about music, games, entertainment, or non-academic topics, respond with "non-educational"."""

        user_prompt = f"Classify this student question: {query}"
        
        try:
            if self.llm_provider:
                # Use the LLM provider's response_no_stream method
                response = self.llm_provider.response_no_stream(system_prompt, user_prompt)
                
                # Clean and validate response
                subject = response.strip().lower()
                
                # Check for non-educational classification
                if 'non-educational' in subject or 'non' in subject:
                    return 'non-educational'
                elif subject in self.subjects:
                    return subject
                elif 'mathematics' in subject or 'math' in subject:
                    return 'mathematics'
                elif 'science' in subject:
                    return 'science'
                    
            # Default to non-educational for unknown queries
            return 'non-educational'
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[MANAGER] LLM classification error: {e}")
            return 'mathematics'
    
    def _get_routing_info(self, subject: str, query: str) -> Dict[str, Any]:
        """Get additional routing information"""
        
        subject_info = self.subjects.get(subject, {})
        
        routing_info = {
            'subject': subject,
            'collection_name': subject_info.get('collection_name'),
            'agent_class': subject_info.get('agent_class'),
            'enabled': subject_info.get('enabled', True),
            'confidence': self._calculate_confidence(subject, query),
            'query_type': self._classify_query_type(query)
        }
        
        return routing_info
    
    def _calculate_confidence(self, subject: str, query: str) -> float:
        """Calculate confidence score for routing decision"""
        
        # Subject-specific keywords
        keywords = {
            'mathematics': [
                'number', 'add', 'subtract', 'multiply', 'divide', 'fraction', 
                'decimal', 'geometry', 'area', 'perimeter', 'angle', 'triangle',
                'rectangle', 'square', 'circle', 'pattern', 'algebra', 'equation',
                'calculate', 'solve', 'math', 'mathematics', 'sum', 'difference',
                'product', 'quotient', 'prime', 'factor', 'multiple', 'ratio'
            ],
            'science': [
                'plant', 'animal', 'food', 'nutrient', 'body', 'health', 'living',
                'organism', 'material', 'solid', 'liquid', 'gas', 'change',
                'motion', 'light', 'shadow', 'electricity', 'circuit', 'magnet',
                'environment', 'nature', 'grow', 'breathe', 'digest', 'science'
            ]
        }
        
        query_lower = query.lower()
        subject_keywords = keywords.get(subject, [])
        
        # Count keyword matches
        matches = sum(1 for keyword in subject_keywords if keyword in query_lower)
        
        # Calculate confidence based on matches
        if matches >= 3:
            return 0.9
        elif matches >= 2:
            return 0.8
        elif matches >= 1:
            return 0.7
        else:
            return 0.5
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of educational query"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what is', 'define', 'meaning', 'explain']):
            return 'definition'
        elif any(word in query_lower for word in ['how to', 'solve', 'calculate', 'find']):
            return 'problem_solving'
        elif any(word in query_lower for word in ['example', 'show me', 'demonstrate']):
            return 'example'
        elif any(word in query_lower for word in ['why', 'how', 'reason']):
            return 'explanation'
        else:
            return 'general'
    
    def get_available_subjects(self) -> Dict[str, bool]:
        """Get list of available subjects and their status"""
        return {
            subject: info.get('enabled', True) 
            for subject, info in self.subjects.items()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the manager agent"""
        try:
            health = {
                'status': 'healthy',
                'llm_provider': self.llm_provider is not None,
                'available_subjects': self.get_available_subjects(),
                'config_loaded': bool(self.config)
            }
            
            # Test LLM connectivity
            if self.llm_provider:
                try:
                    test_response = self.llm_provider.response_no_stream(
                        "You are a test.", "Say 'OK' if you can respond."
                    )
                    health['llm_test'] = 'OK' in test_response
                except:
                    health['llm_test'] = False
                    health['status'] = 'degraded'
            else:
                health['llm_test'] = False
                health['status'] = 'degraded'
                
            return health
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'llm_provider': False,
                'available_subjects': {},
                'config_loaded': False
            }
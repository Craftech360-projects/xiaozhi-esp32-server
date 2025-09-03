"""
Enhanced Educational RAG Memory Provider
Main orchestrator that integrates manager agent and subject expert agents
Compatible with xiaozhi-server's memory provider system
"""

import asyncio
from typing import Dict, Any, Optional
from config.logger import setup_logging
from core.providers.memory.base import MemoryProviderBase
from .config import EDUCATIONAL_RAG_CONFIG
from .llm_master_router import LLMManagerAgent
from .mathematics_agent import MathematicsAgent
from .science_agent import ScienceAgent

# Import nomem provider for fallback
from ..nomem.nomem import MemoryProvider as NoMemProvider

TAG = __name__
logger = setup_logging()

class MemoryProvider(MemoryProviderBase):
    """Enhanced Educational RAG Memory Provider with multi-agent system"""
    
    def __init__(self, config: Dict[str, Any] = None, summary_memory=None):
        final_config = config or EDUCATIONAL_RAG_CONFIG
        super().__init__(final_config)
        self.config = final_config
        self.summary_memory = summary_memory
        
        # Initialize fallback nomem provider for non-educational queries
        self.nomem_provider = NoMemProvider(final_config, summary_memory)
        
        # Initialize manager and expert agents
        self.manager_agent = None
        self.expert_agents = {}
        self._initialized = False
        
        # Initialize the system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize manager agent and subject expert agents"""
        try:
            logger.bind(tag=TAG).info("[EDU-RAG] Initializing Enhanced Educational RAG system")
            
            # Initialize manager agent
            self.manager_agent = LLMManagerAgent(self.config)
            logger.bind(tag=TAG).info("[EDU-RAG] Manager agent initialized")
            
            # Initialize subject expert agents
            subjects_config = self.config.get('subjects', {})
            
            for subject_name, subject_config in subjects_config.items():
                if subject_config.get('enabled', True):
                    try:
                        if subject_name == 'mathematics':
                            self.expert_agents[subject_name] = MathematicsAgent(self.config)
                        elif subject_name == 'science':
                            self.expert_agents[subject_name] = ScienceAgent(self.config)
                        
                        logger.bind(tag=TAG).info(f"[EDU-RAG] {subject_name} expert agent initialized")
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"[EDU-RAG] Failed to initialize {subject_name} agent: {e}")
            
            self._initialized = True
            logger.bind(tag=TAG).info(f"[EDU-RAG] System initialized with {len(self.expert_agents)} expert agents")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[EDU-RAG] System initialization failed: {e}")
            self._initialized = False
    
    async def query_memory(self, query: str) -> str:
        """
        Main query method for educational RAG system
        Only processes educational queries, returns empty for others
        
        Args:
            query (str): User's query
            
        Returns:
            str: Educational response or empty string for non-educational queries
        """
        try:
            # Quick pre-filter for obviously non-educational queries
            if self._is_obviously_non_educational(query):
                logger.bind(tag=TAG).debug(f"[EDU-RAG] Quick bypass for non-educational query: {query[:30]}...")
                return await self.nomem_provider.query_memory(query)  # Use nomem provider
            
            logger.bind(tag=TAG).info(f"[EDU-RAG] Processing educational query: {query[:50]}...")
            
            if not self._initialized:
                logger.bind(tag=TAG).warning("[EDU-RAG] System not properly initialized")
                return await self.nomem_provider.query_memory(query)  # Use nomem provider
            
            # Route query using manager agent
            subject, routing_info = await self.manager_agent.route_query(query)
            logger.bind(tag=TAG).info(f"[EDU-RAG] Query routed to: {subject}")
            
            # Check if query is non-educational
            if subject == 'non-educational':
                logger.bind(tag=TAG).info("[EDU-RAG] Query classified as non-educational, delegating to nomem provider")
                return await self.nomem_provider.query_memory(query)  # Use nomem provider for non-educational
            
            # Get expert agent for the subject
            expert_agent = self.expert_agents.get(subject)
            
            if expert_agent:
                # Get answer from expert agent
                response = await expert_agent.answer_question(query, routing_info)
                logger.bind(tag=TAG).info(f"[EDU-RAG] Response generated by {subject} expert")
                return response
            else:
                logger.bind(tag=TAG).warning(f"[EDU-RAG] No expert agent available for {subject}")
                return self._get_fallback_response(query)
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[EDU-RAG] Query processing error: {e}")
            return await self.nomem_provider.query_memory(query)  # Use nomem provider on error
    
    def _get_fallback_response(self, query: str) -> str:
        """Fallback response when routing or expert agents fail"""
        return ("I'm excited to help you learn! I can answer questions about mathematics "
                "and science for Class 6. Try asking me about numbers, shapes, plants, "
                "animals, or any topic from your textbooks!")
    
    def _is_obviously_non_educational(self, query: str) -> bool:
        """Quick filter for obviously non-educational queries to avoid LLM call"""
        query_lower = query.lower().strip()
        
        # Obvious non-educational keywords
        non_educational_phrases = [
            'play music', 'play song', 'music', 'song',
            'tell story', 'story', 'play story',
            'game', 'play game', 'fun', 'entertainment',
            'hello', 'hi', 'hey', 'good morning', 'good evening',
            'weather', 'news', 'time', 'date',
            'joke', 'funny', 'laugh',
            'sleep', 'wake up', 'tired',
            'food', 'eat', 'hungry', 'thirsty',
            'movie', 'video', 'youtube', 'tv'
        ]
        
        # Check for exact matches or phrases
        for phrase in non_educational_phrases:
            if phrase in query_lower:
                return True
                
        # Check for very short queries that are likely not educational
        if len(query_lower) <= 3:
            return True
            
        return False
    
    def _get_non_educational_response(self) -> str:
        """Response for non-educational queries - minimal response to not interfere"""
        return "I'm here to help with your studies! Feel free to ask me about mathematics or science topics."
    
    def _get_error_response(self) -> str:
        """Response when there's a system error"""
        return ("I'm having some trouble right now, but I still want to help you learn! "
                "Can you try asking your question in a different way?")
    
    # Memory Provider Interface Methods (required by xiaozhi-server)
    
    async def save_memory(self, msgs) -> str:
        """Save memory - not used in educational RAG system but required by interface"""
        logger.bind(tag=TAG).debug("[EDU-RAG] save_memory called (no-op for educational RAG)")
        return "educational_rag_no_save"
    
    async def add_memory(self, message: Dict[str, Any]) -> None:
        """Add memory - not used in RAG system but required by interface"""
        pass
    
    async def get_memory(self, query: str) -> str:
        """Get memory - routes to query_memory for educational RAG"""
        return await self.query_memory(query)
    
    async def delete_memory(self, memory_id: str) -> None:
        """Delete memory - not applicable to RAG system"""
        pass
    
    async def clear_memory(self) -> None:
        """Clear memory - not applicable to RAG system"""  
        pass
    
    # Enhanced Educational RAG specific methods
    
    async def get_subject_summary(self, subject: str) -> str:
        """Get summary of available content for a subject"""
        try:
            expert_agent = self.expert_agents.get(subject)
            if expert_agent:
                return await expert_agent.get_topic_summary(f"{subject} overview")
            else:
                return f"I'd love to help you learn about {subject}! What specific questions do you have?"
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[EDU-RAG] Subject summary error: {e}")
            return f"Let me help you explore {subject}! What would you like to learn?"
    
    async def get_available_subjects(self) -> Dict[str, bool]:
        """Get list of available subjects"""
        if self.manager_agent:
            return self.manager_agent.get_available_subjects()
        return {'mathematics': True, 'science': True}
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of the educational RAG system"""
        health_status = {
            'system_initialized': self._initialized,
            'manager_agent': self.manager_agent is not None,
            'expert_agents': {},
            'overall_status': 'unknown'
        }
        
        try:
            # Check manager agent
            if self.manager_agent:
                manager_health = await self.manager_agent.health_check()
                health_status['manager_health'] = manager_health
            
            # Check expert agents
            for subject, agent in self.expert_agents.items():
                if agent:
                    agent_health = await agent.health_check()
                    health_status['expert_agents'][subject] = agent_health
            
            # Determine overall status
            if (health_status['system_initialized'] and 
                health_status['manager_agent'] and 
                len(self.expert_agents) > 0):
                health_status['overall_status'] = 'healthy'
            elif health_status['system_initialized']:
                health_status['overall_status'] = 'degraded'
            else:
                health_status['overall_status'] = 'unhealthy'
            
            return health_status
            
        except Exception as e:
            health_status['error'] = str(e)
            health_status['overall_status'] = 'unhealthy'
            return health_status
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update configuration (requires restart for full effect)"""
        try:
            self.config.update(new_config)
            logger.bind(tag=TAG).info("[EDU-RAG] Configuration updated")
            return True
        except Exception as e:
            logger.bind(tag=TAG).error(f"[EDU-RAG] Configuration update failed: {e}")
            return False
    
    # Utility methods
    
    def is_educational_query(self, query: str) -> bool:
        """Check if query is educational in nature"""
        educational_keywords = [
            # Mathematics
            'math', 'mathematics', 'number', 'add', 'subtract', 'multiply', 'divide',
            'fraction', 'decimal', 'geometry', 'area', 'perimeter', 'angle', 'shape',
            
            # Science  
            'science', 'plant', 'animal', 'food', 'water', 'air', 'light', 'body',
            'living', 'organism', 'material', 'change', 'motion', 'electricity',
            
            # Learning keywords
            'what is', 'how to', 'explain', 'why', 'how', 'learn', 'understand'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in educational_keywords)
    
    def __str__(self) -> str:
        return (f"Educational RAG Memory Provider - "
                f"Initialized: {self._initialized}, "
                f"Agents: {list(self.expert_agents.keys())}")
    
    def __repr__(self) -> str:
        return (f"MemoryProvider(initialized={self._initialized}, "
                f"subjects={list(self.expert_agents.keys())})")

# Export for backward compatibility
__all__ = ['MemoryProvider']
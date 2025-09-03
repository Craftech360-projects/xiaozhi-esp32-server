"""
Enhanced Educational RAG Query Function
Integrates the Enhanced Educational RAG system with xiaozhi-server
Provides intelligent multi-subject assistance for Class 6 students with manager and expert agents
"""

import asyncio
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.providers.memory.educational_rag.educational_rag import MemoryProvider
from core.providers.memory.educational_rag.config import EDUCATIONAL_RAG_CONFIG

TAG = __name__
logger = setup_logging()

# Global RAG provider instance (initialized once)
rag_provider = None

def initialize_rag_provider():
    """Initialize the Enhanced Educational RAG provider"""
    global rag_provider
    try:
        if rag_provider is None:
            logger.bind(tag=TAG).info("[EDU-RAG-FUNC] Initializing Enhanced Educational RAG provider")
            rag_provider = MemoryProvider(EDUCATIONAL_RAG_CONFIG)
            logger.bind(tag=TAG).info("[EDU-RAG-FUNC] Enhanced Educational RAG provider initialized successfully")
        return rag_provider
    except Exception as e:
        logger.bind(tag=TAG).error(f"[EDU-RAG-FUNC] Failed to initialize RAG provider: {str(e)}")
        return None

def educational_rag_query_sync(query: str, **kwargs):
    """
    Synchronous Enhanced Educational RAG Query Function
    
    Args:
        query (str): The mathematics question or query from the student
        **kwargs: Additional parameters (conn, etc.)
        
    Returns:
        ActionResponse: Response containing educational answer
    """
    import asyncio
    import threading
    
    try:
        logger.bind(tag=TAG).info(f"[EDU-RAG-FUNC] Received query: {query[:50]}...")
        
        # Initialize RAG provider if needed
        provider = initialize_rag_provider()
        if not provider:
            error_msg = "Educational system is currently unavailable. Please try again later."
            logger.bind(tag=TAG).error("[EDU-RAG-FUNC] RAG provider initialization failed")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        # Handle async query in current event loop context
        result = None
        
        try:
            # More robust async handling
            result_container = []
            exception_container = []
            
            def run_in_thread():
                try:
                    # Create new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    
                    async def query_async():
                        return await provider.query_memory(query)
                    
                    result = new_loop.run_until_complete(query_async())
                    result_container.append(result)
                    new_loop.close()
                    
                except Exception as e:
                    exception_container.append(e)
            
            # Always run in a separate thread to avoid event loop conflicts
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
            if exception_container:
                raise exception_container[0]
            
            result = result_container[0] if result_container else None
                
        except Exception as async_error:
            logger.bind(tag=TAG).error(f"[EDU-RAG-FUNC] Async query error: {str(async_error)}")
            # Fallback to a simple response
            result = "I found some information, but I'm having trouble processing it right now."
        
        if result and result.strip():
            logger.bind(tag=TAG).info(f"[EDU-RAG-FUNC] Generated response length: {len(result)}")
            
            # Format the response for child-friendly delivery
            formatted_response = format_educational_response(result, query)
            
            return ActionResponse(Action.RESPONSE, response=formatted_response)
        else:
            # Fallback response when no educational content is found
            fallback_msg = "I don't have information about that topic right now. Let's try asking about mathematics topics like numbers, shapes, or arithmetic!"
            logger.bind(tag=TAG).warning("[EDU-RAG-FUNC] No relevant educational content found")
            return ActionResponse(Action.RESPONSE, response=fallback_msg)
            
    except Exception as e:
        error_msg = "I'm having trouble with that question. Can you try asking in a different way?"
        logger.bind(tag=TAG).error(f"[EDU-RAG-FUNC] Error processing query: {str(e)}")
        return ActionResponse(Action.RESPONSE, response=error_msg)

def format_educational_response(rag_response: str, original_query: str) -> str:
    """
    Format the RAG response for child-friendly delivery
    
    Args:
        rag_response (str): Response from Enhanced Educational RAG
        original_query (str): Original question asked
        
    Returns:
        str: Formatted response suitable for children
    """
    # Keep the educational content but make it more conversational
    if len(rag_response) > 200:
        # For longer responses, add encouraging phrases
        formatted = f"Great question! {rag_response}"
        
        # Add encouragement at the end
        if "example" in rag_response.lower() or "step" in rag_response.lower():
            formatted += "\n\nTry practicing this! Do you want to solve another problem like this?"
        else:
            formatted += "\n\nDoes this help you understand? What else would you like to know?"
    else:
        # For shorter responses, keep them simple
        formatted = rag_response
        if not formatted.endswith(('?', '!', '.')):
            formatted += ". What else can I help you learn?"
    
    return formatted

def is_educational_query(query: str) -> bool:
    """
    Determine if a query is educational/mathematical in nature
    
    Args:
        query (str): The user query
        
    Returns:
        bool: True if query seems educational
    """
    educational_keywords = [
        # Mathematics topics
        'math', 'mathematics', 'number', 'add', 'subtract', 'multiply', 'divide',
        'fraction', 'decimal', 'geometry', 'area', 'perimeter', 'angle', 'triangle',
        'rectangle', 'square', 'circle', 'pattern', 'algebra', 'equation',
        
        # Learning keywords
        'how to', 'what is', 'explain', 'solve', 'calculate', 'find', 'formula',
        'example', 'practice', 'learn', 'understand', 'help with',
        
        # Class 6 specific topics
        'whole number', 'integer', 'prime', 'factor', 'multiple', 'ratio',
        'proportion', 'percentage', 'symmetry', 'construction', 'data', 'graph'
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in educational_keywords)

# Function description for registration
EDUCATIONAL_RAG_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "educational_rag_query",
        "description": (
            "Enhanced Multi-Subject Educational RAG system for Class 6 students - PRIMARY EDUCATIONAL FUNCTION. "
            "Uses intelligent manager agent and subject expert agents to provide child-friendly answers. "
            "Covers MATHEMATICS (numbers, fractions, geometry, arithmetic, patterns, algebra, data handling) "
            "and SCIENCE (plants, animals, food, body, materials, changes, motion, light, electricity). "
            "Use this for ALL educational, learning, mathematics, or science-related queries. "
            "Automatically routes questions to appropriate subject experts using LLM-based classification."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The educational question from the student (mathematics, science, or general learning query)",
                }
            },
            "required": ["query"],
        },
    },
}

# Register the function with the xiaozhi-server system
@register_function("educational_rag_query", EDUCATIONAL_RAG_FUNCTION_DESC, ToolType.WAIT)
def educational_rag_query_registered(query: str, conn=None, **kwargs):
    """Registered wrapper for educational_rag_query function"""
    return educational_rag_query_sync(query, conn=conn, **kwargs)

logger.bind(tag=TAG).info("[EDU-RAG-FUNC] Enhanced Educational RAG function registered successfully")
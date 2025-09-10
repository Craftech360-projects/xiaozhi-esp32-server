"""
Educational Collection Info Function
Provides information about available educational document collections
and their contents in the RAG system
"""

import asyncio
from typing import Dict, Any, List
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.providers.memory.educational_rag.educational_rag import MemoryProvider
from core.providers.memory.educational_rag.config import EDUCATIONAL_RAG_CONFIG

TAG = __name__
logger = setup_logging()

# Global RAG provider instance
rag_provider = None

def initialize_rag_provider():
    """Initialize the Enhanced Educational RAG provider"""
    global rag_provider
    try:
        if rag_provider is None:
            logger.bind(tag=TAG).info("[EDU-COLLECTION-INFO] Initializing Educational RAG provider")
            rag_provider = MemoryProvider(EDUCATIONAL_RAG_CONFIG)
            logger.bind(tag=TAG).info("[EDU-COLLECTION-INFO] Educational RAG provider initialized successfully")
        return rag_provider
    except Exception as e:
        logger.bind(tag=TAG).error(f"[EDU-COLLECTION-INFO] Failed to initialize RAG provider: {str(e)}")
        return None

def educational_collection_info_sync(action: str = "list", grade: str = "class-6", 
                                   subject: str = "mathematics", **kwargs):
    """
    Synchronous Educational Collection Info Function
    
    Args:
        action (str): Action to perform - "list" (all collections) or "info" (specific collection)
        grade (str): Educational grade level (for "info" action)
        subject (str): Subject area (for "info" action)
        **kwargs: Additional parameters (conn, etc.)
        
    Returns:
        ActionResponse: Response containing collection information
    """
    import threading
    
    try:
        logger.bind(tag=TAG).info(f"[EDU-COLLECTION-INFO] Getting collection info - action: {action}")
        
        # Initialize RAG provider
        provider = initialize_rag_provider()
        if not provider:
            error_msg = "Educational document system is currently unavailable. Please try again later."
            logger.bind(tag=TAG).error("[EDU-COLLECTION-INFO] RAG provider initialization failed")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        # Handle async operations in thread
        result = None
        exception_container = []
        
        def run_in_thread():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                async def get_info_async():
                    if action.lower() == "list":
                        return await provider.list_available_collections()
                    else:
                        return await provider.get_collection_info(grade, subject)
                
                result_container.append(new_loop.run_until_complete(get_info_async()))
                new_loop.close()
                
            except Exception as e:
                exception_container.append(e)
        
        result_container = []
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()
        
        if exception_container:
            raise exception_container[0]
        
        result = result_container[0] if result_container else None
        
        if action.lower() == "list":
            # Handle list all collections
            if isinstance(result, list) and result:
                response_msg = "📚 Available Educational Collections:\n\n"
                
                for i, collection in enumerate(result, 1):
                    name = collection.get('name', 'Unknown')
                    status = collection.get('status', 'unknown')
                    points_count = collection.get('points_count', 0)
                    vector_size = collection.get('vector_size', 0)
                    
                    # Parse collection name to extract grade and subject
                    if '-' in name:
                        parts = name.split('-')
                        if len(parts) >= 2:
                            grade_part = parts[0]
                            subject_part = '-'.join(parts[1:])
                        else:
                            grade_part, subject_part = name, "unknown"
                    else:
                        grade_part, subject_part = name, "unknown"
                    
                    response_msg += f"{i}. 📖 {name}\n"
                    response_msg += f"   • Grade: {grade_part.title()}\n"
                    response_msg += f"   • Subject: {subject_part.replace('-', ' ').title()}\n"
                    response_msg += f"   • Content chunks: {points_count:,}\n"
                    response_msg += f"   • Status: {status.title()}\n"
                    
                    if vector_size > 0:
                        response_msg += f"   • Vector size: {vector_size}\n"
                    
                    response_msg += "\n"
                
                response_msg += f"🎓 Total collections: {len(result)}\n"
                response_msg += f"💡 Use 'educational_collection_info' with action='info' to get detailed information about a specific collection."
                
            elif isinstance(result, list) and not result:
                response_msg = "📚 No educational collections found.\n\n"
                response_msg += "💡 Use 'educational_document_upload' to add documents to the knowledge base."
            else:
                response_msg = "❌ Could not retrieve collection list. Please try again later."
            
        else:
            # Handle specific collection info
            if isinstance(result, dict) and 'error' not in result:
                collection_name = result.get('collection_name', 'Unknown')
                points_count = result.get('points_count', 0)
                vector_size = result.get('vector_size', 0)
                distance_metric = result.get('distance_metric', 'unknown')
                status = result.get('status', 'unknown')
                
                response_msg = f"📖 Collection Details: {grade.title()} {subject.title()}\n\n"
                response_msg += f"🆔 Collection Name: {collection_name}\n"
                response_msg += f"📊 Content Chunks: {points_count:,}\n"
                response_msg += f"🔢 Vector Dimensions: {vector_size}\n"
                response_msg += f"📏 Distance Metric: {distance_metric.title()}\n"
                response_msg += f"⚡ Status: {status.title()}\n\n"
                
                if points_count > 0:
                    response_msg += f"✅ This collection contains educational content and is ready for queries!\n"
                    response_msg += f"🎓 You can now ask questions about {grade} {subject} topics."
                else:
                    response_msg += f"⚠️ This collection is empty. Use 'educational_document_upload' to add content."
                    
            elif isinstance(result, dict) and 'error' in result:
                error_msg = result['error']
                if 'not found' in error_msg.lower():
                    response_msg = f"📚 Collection Not Found: {grade.title()} {subject.title()}\n\n"
                    response_msg += f"This collection doesn't exist yet. You can create it by uploading documents:\n"
                    response_msg += f"💡 Use 'educational_document_upload' with grade='{grade}' and subject='{subject}'"
                else:
                    response_msg = f"❌ Error getting collection info: {error_msg}"
            else:
                response_msg = f"❌ Could not retrieve information for {grade} {subject} collection."
        
        logger.bind(tag=TAG).info(f"[EDU-COLLECTION-INFO] Collection info retrieved successfully")
        return ActionResponse(Action.RESPONSE, response=response_msg)
        
    except Exception as e:
        error_msg = f"Error getting collection information: {str(e)}"
        logger.bind(tag=TAG).error(f"[EDU-COLLECTION-INFO] {error_msg}")
        return ActionResponse(Action.RESPONSE, response=f"❌ {error_msg}")

# Function description for registration
EDUCATIONAL_COLLECTION_INFO_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "educational_collection_info",
        "description": (
            "Get information about educational document collections in the RAG system. "
            "Can list all available collections or get detailed information about a specific grade/subject collection. "
            "Shows statistics like number of content chunks, collection status, and vector dimensions. "
            "Use this to check what educational content is available and monitor collection health."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'list' to show all collections, 'info' for specific collection details",
                    "enum": ["list", "info"],
                    "default": "list"
                },
                "grade": {
                    "type": "string",
                    "description": "Educational grade level (required for 'info' action)",
                    "default": "class-6"
                },
                "subject": {
                    "type": "string",
                    "description": "Subject area (required for 'info' action)",
                    "default": "mathematics"
                }
            },
            "required": [],
        },
    },
}

# Register the function
@register_function("educational_collection_info", EDUCATIONAL_COLLECTION_INFO_FUNCTION_DESC, ToolType.WAIT)
def educational_collection_info_registered(action: str = "list", grade: str = "class-6", 
                                         subject: str = "mathematics", conn=None, **kwargs):
    """Registered wrapper for educational_collection_info function"""
    return educational_collection_info_sync(action, grade, subject, conn=conn, **kwargs)

logger.bind(tag=TAG).info("[EDU-COLLECTION-INFO] Educational collection info function registered successfully")
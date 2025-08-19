"""
Textbook search plugin for RAG-based educational Q&A
"""

from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.providers.rag.simple_rag import SimpleRAGProvider
from config.logger import setup_logging

logger = setup_logging()
TAG = __name__

# Initialize RAG provider
rag_config = {
    'db_path': './rag_db',
    'collection_name': 'textbooks'
}

try:
    rag_provider = SimpleRAGProvider(rag_config)
    rag_enabled = True
    logger.bind(tag=TAG).info("RAG provider initialized successfully")
except Exception as e:
    rag_provider = None
    rag_enabled = False
    logger.bind(tag=TAG).error(f"Failed to initialize RAG provider: {str(e)}")

# Function description for LLM
function_desc = {
    "type": "function",
    "function": {
        "name": "search_textbook",
        "description": "Search textbook content to answer study questions. Use when users ask about textbook knowledge, learning content, or need educational explanations",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Question or keywords to search"
                },
                "subject": {
                    "type": "string",
                    "description": "Subject (optional): Physics, Chemistry, Mathematics, Biology, etc."
                },
                "grade": {
                    "type": "string",
                    "description": "Grade (optional): Class 1, Class 2, Class 3, etc. or just the number like 1, 2, 3, 12"
                }
            },
            "required": ["query"]
        }
    }
}


@register_function("search_textbook", function_desc, ToolType.WAIT)
def search_textbook(query: str, subject: str = None, grade: str = None):
    """
    Search textbook content using RAG
    
    Args:
        query: Search query
        subject: Optional subject filter
        grade: Optional grade filter
    
    Returns:
        ActionResponse with search results or error message
    """
    if not rag_enabled or not rag_provider:
        error_msg = "Textbook search is temporarily unavailable, please try again later"
        logger.bind(tag=TAG).error("RAG provider not available")
        return ActionResponse(Action.REQLLM, error_msg, None)
    
    try:
        # Build filters if provided
        filters = {}
        if subject:
            filters['subject'] = subject
        if grade:
            # Convert grade formats (e.g., "5" -> "Class-5", "12" -> "Class-12")
            if grade.isdigit():
                grade = f"Class-{grade}"
            filters['grade'] = grade
        
        # Log the search request
        logger.bind(tag=TAG).info(f"Searching for: '{query}' with filters: {filters}")
        
        # Search in RAG database
        results = rag_provider.search(query, top_k=3, filters=filters if filters else None)
        
        # If no results with filters, try without filters
        if not results['documents'] and filters:
            logger.bind(tag=TAG).info("No results with filters, trying without filters")
            results = rag_provider.search(query, top_k=3, filters=None)
        
        if not results['documents']:
            no_result_msg = f"No textbook content found for '{query}'. Try different keywords or check if relevant textbooks are imported."
            logger.bind(tag=TAG).info("No results found")
            return ActionResponse(Action.REQLLM, no_result_msg, None)
        
        # Format results
        formatted_results = []
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            # Extract metadata
            subject_info = metadata.get('subject', 'Unknown Subject')
            grade_info = metadata.get('grade', 'Unknown Grade')
            page_info = metadata.get('page', '?')
            source_info = metadata.get('source', 'Unknown Source')
            
            # Format each result
            result_text = f"[{subject_info} {grade_info} - {source_info} Page {page_info}]\n{doc}"
            formatted_results.append(result_text)
        
        # Join all results
        context = "\n\n---\n\n".join(formatted_results)
        
        # Create prompt for LLM
        prompt = f"""Based on the following textbook content, answer the student's question. Please explain clearly and accurately using language appropriate for the student's grade level:

Textbook Content:
{context}

Student Question: {query}

Please note:
1. Use simple and easy-to-understand language
2. If the content involves mathematical or scientific concepts, provide examples
3. Encourage understanding rather than rote memorization"""
        
        logger.bind(tag=TAG).info(f"Found {len(results['documents'])} relevant results")
        
        return ActionResponse(Action.REQLLM, prompt, None)
        
    except Exception as e:
        error_msg = f"Search error occurred: {str(e)}"
        logger.bind(tag=TAG).error(f"Search error: {str(e)}")
        return ActionResponse(Action.REQLLM, error_msg, None)


# Additional helper function to get textbook info (not exposed to LLM)
def get_textbook_info():
    """Get information about indexed textbooks"""
    if not rag_enabled or not rag_provider:
        return None
    
    try:
        info = rag_provider.get_collection_info()
        return info
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to get textbook info: {str(e)}")
        return None
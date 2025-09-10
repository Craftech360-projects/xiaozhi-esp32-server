"""
Educational Document Upload Function
Allows uploading and processing of educational documents (PDFs, textbooks) 
into the enhanced Educational RAG system with metadata extraction
"""

import asyncio
import os
from pathlib import Path
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
            logger.bind(tag=TAG).info("[EDU-DOC-UPLOAD] Initializing Educational RAG provider")
            rag_provider = MemoryProvider(EDUCATIONAL_RAG_CONFIG)
            logger.bind(tag=TAG).info("[EDU-DOC-UPLOAD] Educational RAG provider initialized successfully")
        return rag_provider
    except Exception as e:
        logger.bind(tag=TAG).error(f"[EDU-DOC-UPLOAD] Failed to initialize RAG provider: {str(e)}")
        return None

def educational_document_upload_sync(file_path: str, grade: str = "class-6", 
                                   subject: str = "mathematics", 
                                   document_name: str = None, **kwargs):
    """
    Synchronous Educational Document Upload Function
    
    Args:
        file_path (str): Path to the document file (PDF, TXT, etc.)
        grade (str): Educational grade level (default: "class-6")
        subject (str): Subject area (default: "mathematics")
        document_name (str): Optional custom name for the document
        **kwargs: Additional parameters (conn, etc.)
        
    Returns:
        ActionResponse: Response containing upload status and statistics
    """
    import threading
    
    try:
        logger.bind(tag=TAG).info(f"[EDU-DOC-UPLOAD] Uploading document: {file_path}")
        
        # Validate file path
        if not file_path or not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.bind(tag=TAG).error(f"[EDU-DOC-UPLOAD] {error_msg}")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        # Validate file extension
        supported_extensions = ['.pdf', '.txt', '.md']
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in supported_extensions:
            error_msg = f"Unsupported file format: {file_ext}. Supported formats: {', '.join(supported_extensions)}"
            logger.bind(tag=TAG).error(f"[EDU-DOC-UPLOAD] {error_msg}")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        # Initialize RAG provider
        provider = initialize_rag_provider()
        if not provider:
            error_msg = "Educational document system is currently unavailable. Please try again later."
            logger.bind(tag=TAG).error("[EDU-DOC-UPLOAD] RAG provider initialization failed")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        # Handle async document ingestion in thread
        result = None
        exception_container = []
        
        def run_in_thread():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                async def ingest_async():
                    return await provider.ingest_document(file_path, grade, subject, document_name)
                
                result_container.append(new_loop.run_until_complete(ingest_async()))
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
        
        if result and result.get('success'):
            stats = result.get('statistics', {})
            
            response_msg = f"✅ Document uploaded successfully!\n\n"
            response_msg += f"📄 Document: {stats.get('document_name', 'Unknown')}\n"
            response_msg += f"📚 Grade: {grade}, Subject: {subject}\n"
            response_msg += f"📊 Processing Results:\n"
            response_msg += f"  • Total chunks: {stats.get('total_chunks', 0)}\n"
            
            # Add chunk type breakdown if available
            chunk_types = stats.get('chunk_types', {})
            if chunk_types:
                response_msg += f"  • Content types:\n"
                for chunk_type, count in chunk_types.items():
                    response_msg += f"    - {chunk_type.title()}: {count}\n"
            
            # Add content category breakdown if available
            content_categories = stats.get('content_categories', {})
            if content_categories:
                response_msg += f"  • Content categories:\n"
                for category, count in content_categories.items():
                    response_msg += f"    - {category.title()}: {count}\n"
            
            response_msg += f"\n🎓 The document has been processed and is now available for educational queries!"
            
            logger.bind(tag=TAG).info(f"[EDU-DOC-UPLOAD] Successfully uploaded document: {file_path}")
            return ActionResponse(Action.RESPONSE, response=response_msg)
            
        else:
            error_msg = result.get('error', 'Unknown error occurred during document processing')
            logger.bind(tag=TAG).error(f"[EDU-DOC-UPLOAD] Document upload failed: {error_msg}")
            return ActionResponse(Action.RESPONSE, response=f"❌ Document upload failed: {error_msg}")
            
    except Exception as e:
        error_msg = f"Error processing document upload: {str(e)}"
        logger.bind(tag=TAG).error(f"[EDU-DOC-UPLOAD] {error_msg}")
        return ActionResponse(Action.RESPONSE, response=f"❌ {error_msg}")

# Function description for registration
EDUCATIONAL_DOCUMENT_UPLOAD_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "educational_document_upload",
        "description": (
            "Upload and process educational documents (PDFs, textbooks) into the RAG system. "
            "Supports multi-format content extraction including text, tables, and images with OCR. "
            "Automatically extracts educational metadata like chapters, topics, content types, and difficulty levels. "
            "Use this to add new textbooks or educational materials to the knowledge base for student queries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Full path to the document file (PDF, TXT, MD)"
                },
                "grade": {
                    "type": "string",
                    "description": "Educational grade level (e.g., 'class-6', 'class-7', etc.)",
                    "default": "class-6"
                },
                "subject": {
                    "type": "string", 
                    "description": "Subject area (e.g., 'mathematics', 'science', 'english', etc.)",
                    "default": "mathematics"
                },
                "document_name": {
                    "type": "string",
                    "description": "Optional custom name for the document (defaults to filename)"
                }
            },
            "required": ["file_path"],
        },
    },
}

# Register the function
@register_function("educational_document_upload", EDUCATIONAL_DOCUMENT_UPLOAD_FUNCTION_DESC, ToolType.WAIT)
def educational_document_upload_registered(file_path: str, grade: str = "class-6", 
                                         subject: str = "mathematics", 
                                         document_name: str = None, conn=None, **kwargs):
    """Registered wrapper for educational_document_upload function"""
    return educational_document_upload_sync(file_path, grade, subject, document_name, conn=conn, **kwargs)

logger.bind(tag=TAG).info("[EDU-DOC-UPLOAD] Educational document upload function registered successfully")
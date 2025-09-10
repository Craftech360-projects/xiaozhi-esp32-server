"""
Educational Document Batch Upload Function
Allows batch uploading and processing of multiple educational documents
into the enhanced Educational RAG system
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
            logger.bind(tag=TAG).info("[EDU-BATCH-UPLOAD] Initializing Educational RAG provider")
            rag_provider = MemoryProvider(EDUCATIONAL_RAG_CONFIG)
            logger.bind(tag=TAG).info("[EDU-BATCH-UPLOAD] Educational RAG provider initialized successfully")
        return rag_provider
    except Exception as e:
        logger.bind(tag=TAG).error(f"[EDU-BATCH-UPLOAD] Failed to initialize RAG provider: {str(e)}")
        return None

def educational_document_batch_upload_sync(directory_path: str, grade: str = "class-6", 
                                         subject: str = "mathematics", 
                                         file_pattern: str = "*.pdf", **kwargs):
    """
    Synchronous Educational Document Batch Upload Function
    
    Args:
        directory_path (str): Path to directory containing documents
        grade (str): Educational grade level (default: "class-6")
        subject (str): Subject area (default: "mathematics") 
        file_pattern (str): File pattern to match (default: "*.pdf")
        **kwargs: Additional parameters (conn, etc.)
        
    Returns:
        ActionResponse: Response containing batch upload status and statistics
    """
    import threading
    import glob
    
    try:
        logger.bind(tag=TAG).info(f"[EDU-BATCH-UPLOAD] Starting batch upload from: {directory_path}")
        
        # Validate directory path
        if not directory_path or not os.path.exists(directory_path):
            error_msg = f"Directory not found: {directory_path}"
            logger.bind(tag=TAG).error(f"[EDU-BATCH-UPLOAD] {error_msg}")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        # Find files matching pattern
        search_pattern = os.path.join(directory_path, file_pattern)
        file_paths = glob.glob(search_pattern)
        
        if not file_paths:
            error_msg = f"No files found matching pattern '{file_pattern}' in directory: {directory_path}"
            logger.bind(tag=TAG).warning(f"[EDU-BATCH-UPLOAD] {error_msg}")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        # Filter supported file types
        supported_extensions = ['.pdf', '.txt', '.md']
        valid_files = []
        skipped_files = []
        
        for file_path in file_paths:
            file_ext = Path(file_path).suffix.lower()
            if file_ext in supported_extensions:
                valid_files.append(file_path)
            else:
                skipped_files.append(file_path)
        
        if not valid_files:
            error_msg = f"No supported files found. Supported formats: {', '.join(supported_extensions)}"
            logger.bind(tag=TAG).error(f"[EDU-BATCH-UPLOAD] {error_msg}")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        logger.bind(tag=TAG).info(f"[EDU-BATCH-UPLOAD] Found {len(valid_files)} valid files, {len(skipped_files)} skipped")
        
        # Initialize RAG provider
        provider = initialize_rag_provider()
        if not provider:
            error_msg = "Educational document system is currently unavailable. Please try again later."
            logger.bind(tag=TAG).error("[EDU-BATCH-UPLOAD] RAG provider initialization failed")
            return ActionResponse(Action.RESPONSE, response=error_msg)
        
        # Handle async batch processing in thread
        result = None
        exception_container = []
        
        def run_in_thread():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                async def batch_ingest_async():
                    return await provider.ingest_documents_batch(valid_files, grade, subject)
                
                result_container.append(new_loop.run_until_complete(batch_ingest_async()))
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
        
        if result:
            # Format response message
            total_docs = result.get('total_documents', 0)
            successful = result.get('successful_ingestions', 0)
            failed = result.get('failed_ingestions', 0)
            total_chunks = result.get('total_chunks', 0)
            errors = result.get('errors', [])
            
            response_msg = f"📚 Batch Document Upload Results\n\n"
            response_msg += f"📊 Summary:\n"
            response_msg += f"  • Total files processed: {total_docs}\n"
            response_msg += f"  • Successfully uploaded: {successful}\n"
            response_msg += f"  • Failed uploads: {failed}\n"
            response_msg += f"  • Total content chunks: {total_chunks}\n"
            
            if skipped_files:
                response_msg += f"  • Skipped files: {len(skipped_files)}\n"
            
            response_msg += f"\n📚 Grade: {grade}, Subject: {subject}\n"
            
            if successful > 0:
                response_msg += f"\n✅ {successful} document(s) successfully uploaded and processed!\n"
                response_msg += f"🎓 The documents are now available for educational queries."
            
            if failed > 0:
                response_msg += f"\n❌ {failed} document(s) failed to upload:\n"
                for error in errors[:3]:  # Show first 3 errors
                    file_name = Path(error.get('file_path', 'Unknown')).name
                    error_msg = error.get('error', 'Unknown error')
                    response_msg += f"  • {file_name}: {error_msg}\n"
                
                if len(errors) > 3:
                    response_msg += f"  • ... and {len(errors) - 3} more errors"
            
            if skipped_files:
                response_msg += f"\n⚠️ Skipped unsupported files:\n"
                for skipped in skipped_files[:3]:  # Show first 3 skipped
                    response_msg += f"  • {Path(skipped).name}\n"
                
                if len(skipped_files) > 3:
                    response_msg += f"  • ... and {len(skipped_files) - 3} more files"
            
            success_rate = successful / total_docs if total_docs > 0 else 0
            if success_rate >= 0.8:
                status_emoji = "🎉"
            elif success_rate >= 0.5:
                status_emoji = "⚠️"
            else:
                status_emoji = "❌"
            
            response_msg = f"{status_emoji} " + response_msg
            
            logger.bind(tag=TAG).info(f"[EDU-BATCH-UPLOAD] Batch upload completed: {successful}/{total_docs} successful")
            return ActionResponse(Action.RESPONSE, response=response_msg)
            
        else:
            error_msg = "No result returned from batch processing"
            logger.bind(tag=TAG).error(f"[EDU-BATCH-UPLOAD] {error_msg}")
            return ActionResponse(Action.RESPONSE, response=f"❌ Batch upload failed: {error_msg}")
            
    except Exception as e:
        error_msg = f"Error processing batch document upload: {str(e)}"
        logger.bind(tag=TAG).error(f"[EDU-BATCH-UPLOAD] {error_msg}")
        return ActionResponse(Action.RESPONSE, response=f"❌ {error_msg}")

# Function description for registration
EDUCATIONAL_DOCUMENT_BATCH_UPLOAD_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "educational_document_batch_upload",
        "description": (
            "Upload and process multiple educational documents from a directory in batch. "
            "Supports PDF, TXT, and MD files with advanced content extraction including text, tables, and images with OCR. "
            "Automatically processes all matching files and provides detailed statistics. "
            "Use this to quickly add entire textbook collections or course materials to the knowledge base."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to directory containing documents to upload"
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
                "file_pattern": {
                    "type": "string",
                    "description": "File pattern to match (e.g., '*.pdf', '*.txt', '*math*.pdf')",
                    "default": "*.pdf"
                }
            },
            "required": ["directory_path"],
        },
    },
}

# Register the function
@register_function("educational_document_batch_upload", EDUCATIONAL_DOCUMENT_BATCH_UPLOAD_FUNCTION_DESC, ToolType.WAIT)
def educational_document_batch_upload_registered(directory_path: str, grade: str = "class-6", 
                                               subject: str = "mathematics", 
                                               file_pattern: str = "*.pdf", conn=None, **kwargs):
    """Registered wrapper for educational_document_batch_upload function"""
    return educational_document_batch_upload_sync(directory_path, grade, subject, file_pattern, conn=conn, **kwargs)

logger.bind(tag=TAG).info("[EDU-BATCH-UPLOAD] Educational document batch upload function registered successfully")
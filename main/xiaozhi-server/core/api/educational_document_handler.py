import os
import json
import asyncio
from pathlib import Path
from aiohttp import web, web_request
from config.logger import setup_logging
from core.providers.memory.educational_rag.document_ingestion_service import DocumentIngestionService
from core.providers.memory.educational_rag.educational_rag import MemoryProvider as EducationalRAGProvider
from core.providers.memory.educational_rag.config import EDUCATIONAL_RAG_CONFIG

TAG = __name__


class EducationalDocumentHandler:
    """Handler for educational document processing endpoints"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        
        # Get educational_rag config from Memory section
        educational_config = {}
        if 'Memory' in config and 'educational_rag' in config['Memory']:
            educational_config = config['Memory']['educational_rag']
        else:
            # Fallback to direct educational_rag config
            educational_config = config.get('educational_rag', {})
        
        # If still empty, try to get from EDUCATIONAL_RAG_CONFIG
        if not educational_config:
            educational_config = EDUCATIONAL_RAG_CONFIG
        
        # Validate Qdrant configuration from .config.yaml
        if not educational_config.get('qdrant_url'):
            self.logger.bind(tag=TAG).warning("qdrant_url not found, using default local Qdrant")
            educational_config['qdrant_url'] = 'http://localhost:6333'
        
        # qdrant_api_key is optional for local instances
        if not educational_config.get('qdrant_api_key'):
            self.logger.bind(tag=TAG).info("qdrant_api_key not found, assuming local Qdrant instance")
            educational_config['qdrant_api_key'] = None
        
        self.logger.bind(tag=TAG).info(f"Educational config loaded - Qdrant URL: {educational_config.get('qdrant_url')}")
        
        # Initialize document ingestion service
        self.ingestion_service = DocumentIngestionService(config=educational_config)
        
        # Initialize educational RAG provider  
        self.rag_provider = EducationalRAGProvider(config=educational_config)
        
    async def handle_options(self, request: web_request.Request) -> web.Response:
        """Handle CORS preflight requests"""
        return web.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400'
            }
        )
    
    async def upload_document(self, request: web_request.Request) -> web.Response:
        """Handle single document upload and processing"""
        try:
            self.logger.bind(tag=TAG).info("Processing document upload request")
            
            # Parse multipart form data
            reader = await request.multipart()
            
            file_data = None
            grade = None
            subject = None
            document_name = None
            
            # Read form fields
            while True:
                field = await reader.next()
                if field is None:
                    break
                    
                if field.name == 'file':
                    file_data = await field.read()
                    filename = field.filename
                elif field.name == 'grade':
                    grade = await field.text()
                elif field.name == 'subject':
                    subject = await field.text()  
                elif field.name == 'documentName':
                    document_name = await field.text()
            
            if not file_data or not filename:
                return web.json_response(
                    {'error': 'No file provided'},
                    status=400,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            if not grade or not subject:
                return web.json_response(
                    {'error': 'Grade and subject are required'},
                    status=400,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            # Create temporary directory for upload
            upload_dir = Path("tmp/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Save uploaded file
            file_path = upload_dir / filename
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            self.logger.bind(tag=TAG).info(f"File saved to {file_path}")
            
            # Process document synchronously to return full statistics
            self.logger.bind(tag=TAG).info(f"Starting synchronous processing of {document_name or filename}")
            
            try:
                # Use the document ingestion service to process the document
                result = await self.ingestion_service.ingest_document(
                    file_path=str(file_path),
                    grade=grade,
                    subject=subject,
                    document_name=document_name or filename
                )
                
                self.logger.bind(tag=TAG).info(f"Document processing completed: {result}")
                
                # Clean up temporary file
                try:
                    os.unlink(file_path)
                except:
                    pass
                
                # Return full processing results
                return web.json_response(
                    result,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
                
            except Exception as processing_error:
                self.logger.bind(tag=TAG).error(f"Error processing document: {str(processing_error)}")
                
                # Clean up temporary file on error
                try:
                    os.unlink(file_path)
                except:
                    pass
                    
                return web.json_response(
                    {
                        'success': False,
                        'error': str(processing_error),
                        'filename': filename,
                        'grade': grade,
                        'subject': subject
                    },
                    status=500,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error uploading document: {str(e)}")
            return web.json_response(
                {'error': f'Upload failed: {str(e)}'},
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
    
    async def upload_documents_batch(self, request: web_request.Request) -> web.Response:
        """Handle batch document upload and processing"""
        try:
            self.logger.bind(tag=TAG).info("Processing batch document upload request")
            
            # Parse multipart form data
            reader = await request.multipart()
            
            files_data = []
            grade = None
            subject = None
            
            # Read form fields
            while True:
                field = await reader.next()
                if field is None:
                    break
                    
                if field.name == 'files':
                    file_data = await field.read()
                    files_data.append({
                        'data': file_data,
                        'filename': field.filename
                    })
                elif field.name == 'grade':
                    grade = await field.text()
                elif field.name == 'subject':
                    subject = await field.text()
            
            if not files_data:
                return web.json_response(
                    {'error': 'No files provided'},
                    status=400,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            if not grade or not subject:
                return web.json_response(
                    {'error': 'Grade and subject are required'},
                    status=400,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            # Create temporary directory for upload
            upload_dir = Path("tmp/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            file_paths = []
            for file_info in files_data:
                file_path = upload_dir / file_info['filename']
                with open(file_path, 'wb') as f:
                    f.write(file_info['data'])
                file_paths.append(str(file_path))
            
            self.logger.bind(tag=TAG).info(f"Batch files saved: {[Path(p).name for p in file_paths]}")
            
            # Process documents asynchronously
            asyncio.create_task(self._process_documents_batch_async(
                file_paths, grade, subject
            ))
            
            return web.json_response(
                {
                    'message': f'Batch upload successful, processing {len(file_paths)} documents',
                    'file_count': len(file_paths),
                    'grade': grade,
                    'subject': subject
                },
                headers={'Access-Control-Allow-Origin': '*'}
            )
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error in batch upload: {str(e)}")
            return web.json_response(
                {'error': f'Batch upload failed: {str(e)}'},
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
    
    async def get_collection_info(self, request: web_request.Request) -> web.Response:
        """Get collection information"""
        try:
            grade = request.query.get('grade')
            subject = request.query.get('subject')
            
            if not grade or not subject:
                return web.json_response(
                    {'error': 'Grade and subject are required'},
                    status=400,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            # Get collection info from educational RAG
            info = await self.rag_provider.get_collection_info(grade, subject)
            
            return web.json_response(
                info,
                headers={'Access-Control-Allow-Origin': '*'}
            )
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error getting collection info: {str(e)}")
            return web.json_response(
                {'error': f'Failed to get collection info: {str(e)}'},
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
    
    async def list_collections(self, request: web_request.Request) -> web.Response:
        """List all collections"""
        try:
            # Get all collections from educational RAG
            collections = await self.rag_provider.list_available_collections()
            
            return web.json_response(
                {'collections': collections},
                headers={'Access-Control-Allow-Origin': '*'}
            )
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error listing collections: {str(e)}")
            return web.json_response(
                {'error': f'Failed to list collections: {str(e)}'},
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
    
    async def delete_collection(self, request: web_request.Request) -> web.Response:
        """Delete a collection"""
        try:
            grade = request.query.get('grade')
            subject = request.query.get('subject')
            
            if not grade or not subject:
                return web.json_response(
                    {'error': 'Grade and subject are required'},
                    status=400,
                    headers={'Access-Control-Allow-Origin': '*'}
                )
            
            # Delete collection from educational RAG
            await self.rag_provider.delete_collection(grade, subject)
            
            return web.json_response(
                {'message': f'Collection {grade}-{subject} deleted successfully'},
                headers={'Access-Control-Allow-Origin': '*'}
            )
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error deleting collection: {str(e)}")
            return web.json_response(
                {'error': f'Failed to delete collection: {str(e)}'},
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )
    
    async def _process_document_async(self, file_path: str, grade: str, subject: str, document_name: str):
        """Process document asynchronously"""
        try:
            self.logger.bind(tag=TAG).info(f"Starting async processing of {document_name}")
            
            # Use the document ingestion service to process the document
            result = await self.ingestion_service.ingest_document(
                file_path=file_path,
                grade=grade,
                subject=subject,
                document_name=document_name
            )
            
            self.logger.bind(tag=TAG).info(f"Document processing completed: {result}")
            
            # Clean up temporary file
            try:
                os.unlink(file_path)
            except:
                pass
                
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error in async document processing: {str(e)}")
    
    async def _process_documents_batch_async(self, file_paths: list, grade: str, subject: str):
        """Process documents in batch asynchronously"""
        try:
            self.logger.bind(tag=TAG).info(f"Starting async batch processing of {len(file_paths)} documents")
            
            # Use the document ingestion service to process documents in batch
            result = await self.ingestion_service.ingest_documents_batch(
                file_paths=file_paths,
                grade=grade,
                subject=subject
            )
            
            self.logger.bind(tag=TAG).info(f"Batch document processing completed: {result}")
            
            # Clean up temporary files
            for file_path in file_paths:
                try:
                    os.unlink(file_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Error in async batch processing: {str(e)}")
    
    async def get_content_by_type(self, request):
        """Get content items by type from a specific collection"""
        try:
            # Parse query parameters
            grade = request.query.get('grade', 'class-6')
            subject = request.query.get('subject', 'mathematics')
            content_type = request.query.get('content_type', 'concept')
            limit = int(request.query.get('limit', '100'))
            
            self.logger.bind(tag=TAG).info(f"Getting {content_type} content for {grade}-{subject} (limit: {limit})")
            
            # Query content by type
            content_items = await self.rag_provider.query_content_by_type(
                grade=grade,
                subject=subject,
                content_type=content_type,
                limit=limit
            )
            
            self.logger.bind(tag=TAG).info(f"Found {len(content_items)} {content_type} items")
            
            return web.json_response({
                'success': True,
                'data': content_items,
                'total': len(content_items),
                'grade': grade,
                'subject': subject,
                'content_type': content_type
            }, status=200)
            
        except Exception as e:
            error_msg = f"Error getting content by type: {str(e)}"
            self.logger.bind(tag=TAG).error(error_msg)
            return web.json_response({
                'success': False,
                'error': error_msg
            }, status=500)
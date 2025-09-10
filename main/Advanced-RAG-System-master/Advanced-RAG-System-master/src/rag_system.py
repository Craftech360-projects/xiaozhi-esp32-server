# src/rag_system.py
import os
import logging
from typing import List, Dict, Any
from .pdf_processor import PDFProcessor
# src/rag_system.py - Change this import line
from .vector_store_windows_safe import VectorStore
from .retriever import SmartRetriever
from .llm_handler import LLMHandler


class RAGSystem:
    def __init__(self, config):
        self.config = config
        self.logger = self._setup_logging()

        # Initialize components
        self.pdf_processor = PDFProcessor(config)
        self.vector_store = VectorStore(config)
        self.retriever = SmartRetriever(self.vector_store, config)
        self.llm_handler = LLMHandler(config)

        self.logger.info("RAG System initialized successfully")

    def add_document(self, pdf_path: str) -> Dict[str, Any]:
        """Add a PDF document to the knowledge base"""
        try:
            # Extract document name
            doc_name = os.path.basename(pdf_path).replace('.pdf', '')

            self.logger.info(f"Processing document: {doc_name}")

            # Process PDF
            chunks = self.pdf_processor.extract_content(pdf_path)

            if not chunks:
                return {'success': False, 'message': 'No content extracted from PDF'}

            # Add to vector store
            self.vector_store.add_documents(chunks, doc_name)

            # Get statistics
            stats = {
                'total_chunks': len(chunks),
                'text_chunks': len([c for c in chunks if c.chunk_type == 'text']),
                'table_chunks': len([c for c in chunks if c.chunk_type == 'table']),
                'image_chunks': len([c for c in chunks if c.chunk_type == 'image'])
            }

            self.logger.info(f"Successfully added {doc_name}: {stats}")

            return {
                'success': True,
                'document_name': doc_name,
                'statistics': stats
            }

        except Exception as e:
            self.logger.error(f"Error processing document {pdf_path}: {e}")
            return {'success': False, 'message': str(e)}

    def query(self, question: str, conversation_history: List[str] = None) -> Dict[str, Any]:
        """Query the RAG system"""
        try:
            self.logger.info(f"Processing query: {question}")

            # Retrieve relevant documents
            retrieval_results = self.retriever.retrieve(
                question, conversation_history)

            if not retrieval_results['results']:
                return {
                    'answer': "I couldn't find relevant information in the documents to answer your question.",
                    'sources_used': 0,
                    'query_type': retrieval_results['query_type'],
                    'confidence': 0.0
                }

            # Generate response
            response = self.llm_handler.generate_response(
                question,
                retrieval_results['results'],
                conversation_history
            )

            # Add retrieval info
            response['query_type'] = retrieval_results['query_type']
            response['retrieval_stats'] = {
                'total_found': retrieval_results['total_found'],
                'used_for_generation': len(retrieval_results['results'])
            }

            return response

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                'answer': "I encountered an error while processing your question. Please try again.",
                'sources_used': 0,
                'query_type': 'error',
                'confidence': 0.0
            }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            return {
                'vector_store': vector_stats,
                'models': {
                    'embedding_model': self.config.EMBEDDING_MODEL,
                    'llm_model': self.config.LLM_MODEL
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}

    def clear_conversation_history(self):
        """Clear conversation history"""
        self.llm_handler.clear_history()

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

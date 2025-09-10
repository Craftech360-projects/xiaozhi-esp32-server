"""
Test Script for Enhanced Educational RAG System
Tests the integrated PDF processing pipeline with document upload functionality
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.logger import setup_logging
from core.utils.enhanced_document_processor import EnhancedDocumentProcessor
from core.providers.memory.educational_rag.educational_rag import MemoryProvider
from core.providers.memory.educational_rag.config import EDUCATIONAL_RAG_CONFIG

TAG = __name__
logger = setup_logging()


class EnhancedEducationalRAGTest:
    """Test suite for the Enhanced Educational RAG System"""
    
    def __init__(self):
        """Initialize the test suite"""
        self.document_processor = None
        self.memory_provider = None
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': []
        }
        
        logger.bind(tag=TAG).info("[TEST] Enhanced Educational RAG Test Suite initialized")
    
    def run_all_tests(self):
        """Run all tests in the suite"""
        logger.bind(tag=TAG).info("[TEST] Starting Enhanced Educational RAG Test Suite")
        
        # Test 1: Document Processor Initialization
        self.test_document_processor_initialization()
        
        # Test 2: Memory Provider Initialization  
        self.test_memory_provider_initialization()
        
        # Test 3: Configuration Loading
        self.test_configuration_loading()
        
        # Test 4: Dependencies Check
        self.test_dependencies_check()
        
        # Test 5: Document Processing (if test file available)
        self.test_document_processing()
        
        # Test 6: Function Call Registration
        self.test_function_call_registration()
        
        # Print results
        self.print_test_results()
        
        return self.test_results
    
    def test_document_processor_initialization(self):
        """Test 1: Document processor initialization"""
        self.test_results['tests_run'] += 1
        
        try:
            logger.bind(tag=TAG).info("[TEST] Testing document processor initialization")
            
            self.document_processor = EnhancedDocumentProcessor(
                chunk_size=800,
                chunk_overlap=100
            )
            
            # Check if processor was created successfully
            if self.document_processor is not None:
                logger.bind(tag=TAG).info("[TEST] ✅ Document processor initialized successfully")
                self.test_results['tests_passed'] += 1
            else:
                raise Exception("Document processor is None after initialization")
                
        except Exception as e:
            error_msg = f"Document processor initialization failed: {str(e)}"
            logger.bind(tag=TAG).error(f"[TEST] ❌ {error_msg}")
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(error_msg)
    
    def test_memory_provider_initialization(self):
        """Test 2: Memory provider initialization"""
        self.test_results['tests_run'] += 1
        
        try:
            logger.bind(tag=TAG).info("[TEST] Testing memory provider initialization")
            
            self.memory_provider = MemoryProvider(EDUCATIONAL_RAG_CONFIG)
            
            # Check if provider was created successfully
            if self.memory_provider is not None and self.memory_provider._initialized:
                logger.bind(tag=TAG).info("[TEST] ✅ Memory provider initialized successfully")
                self.test_results['tests_passed'] += 1
            else:
                raise Exception("Memory provider initialization failed or not initialized")
                
        except Exception as e:
            error_msg = f"Memory provider initialization failed: {str(e)}"
            logger.bind(tag=TAG).error(f"[TEST] ❌ {error_msg}")
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(error_msg)
    
    def test_configuration_loading(self):
        """Test 3: Configuration loading"""
        self.test_results['tests_run'] += 1
        
        try:
            logger.bind(tag=TAG).info("[TEST] Testing configuration loading")
            
            # Check if configuration has required fields
            required_fields = ['type', 'qdrant_url', 'qdrant_api_key', 'subjects']
            
            for field in required_fields:
                if field not in EDUCATIONAL_RAG_CONFIG:
                    raise Exception(f"Required configuration field '{field}' missing")
            
            # Check subjects configuration
            subjects = EDUCATIONAL_RAG_CONFIG.get('subjects', {})
            if 'mathematics' not in subjects or 'science' not in subjects:
                raise Exception("Required subjects (mathematics, science) not configured")
            
            logger.bind(tag=TAG).info("[TEST] ✅ Configuration loaded successfully")
            self.test_results['tests_passed'] += 1
            
        except Exception as e:
            error_msg = f"Configuration loading failed: {str(e)}"
            logger.bind(tag=TAG).error(f"[TEST] ❌ {error_msg}")
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(error_msg)
    
    def test_dependencies_check(self):
        """Test 4: Dependencies check"""
        self.test_results['tests_run'] += 1
        
        try:
            logger.bind(tag=TAG).info("[TEST] Testing dependencies availability")
            
            dependencies_status = {
                'langchain': False,
                'qdrant_client': False,
                'sentence_transformers': False,
                'fitz': False,
                'pdfplumber': False,
                'pytesseract': False
            }
            
            # Check core dependencies
            try:
                from langchain_core.documents import Document
                dependencies_status['langchain'] = True
            except ImportError:
                pass
            
            try:
                from qdrant_client import QdrantClient
                dependencies_status['qdrant_client'] = True
            except ImportError:
                pass
            
            try:
                from sentence_transformers import SentenceTransformer
                dependencies_status['sentence_transformers'] = True
            except ImportError:
                pass
            
            # Check PDF processing dependencies
            try:
                import fitz
                dependencies_status['fitz'] = True
            except ImportError:
                pass
            
            try:
                import pdfplumber
                dependencies_status['pdfplumber'] = True
            except ImportError:
                pass
            
            try:
                import pytesseract
                dependencies_status['pytesseract'] = True
            except ImportError:
                pass
            
            # Log dependency status
            logger.bind(tag=TAG).info(f"[TEST] Dependencies status: {dependencies_status}")
            
            # Core dependencies are required
            core_deps = ['langchain', 'qdrant_client']
            missing_core = [dep for dep in core_deps if not dependencies_status[dep]]
            
            if missing_core:
                raise Exception(f"Missing core dependencies: {missing_core}")
            
            logger.bind(tag=TAG).info("[TEST] ✅ Core dependencies available")
            self.test_results['tests_passed'] += 1
            
        except Exception as e:
            error_msg = f"Dependencies check failed: {str(e)}"
            logger.bind(tag=TAG).error(f"[TEST] ❌ {error_msg}")
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(error_msg)
    
    def test_document_processing(self):
        """Test 5: Document processing (if test file available)"""
        self.test_results['tests_run'] += 1
        
        try:
            logger.bind(tag=TAG).info("[TEST] Testing document processing")
            
            # Create a simple test text file if no PDF available
            test_file_path = os.path.join(os.path.dirname(__file__), 'test_document.txt')
            test_content = """
            Chapter 1: Introduction to Numbers
            
            Numbers are fundamental in mathematics. They help us count and measure.
            
            Example: The number 5 represents five objects.
            
            Exercise: Count from 1 to 10.
            
            Definition: A whole number is a number without fractions or decimals.
            
            Formula: Addition formula is a + b = c
            """
            
            # Write test file
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Test document processing
            if self.document_processor:
                chunks = self.document_processor.process_document(
                    test_file_path,
                    grade="class-6",
                    subject="mathematics",
                    document_name="Test Document"
                )
                
                if chunks and len(chunks) > 0:
                    logger.bind(tag=TAG).info(f"[TEST] ✅ Document processed successfully: {len(chunks)} chunks")
                    
                    # Check chunk metadata
                    sample_chunk = chunks[0]
                    required_metadata = ['grade', 'subject', 'content_category', 'chunk_type']
                    
                    for field in required_metadata:
                        if field not in sample_chunk.metadata:
                            raise Exception(f"Missing metadata field: {field}")
                    
                    # Clean up test file
                    os.remove(test_file_path)
                    
                    self.test_results['tests_passed'] += 1
                else:
                    raise Exception("No chunks generated from test document")
            else:
                raise Exception("Document processor not available")
                
        except Exception as e:
            error_msg = f"Document processing test failed: {str(e)}"
            logger.bind(tag=TAG).error(f"[TEST] ❌ {error_msg}")
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(error_msg)
            
            # Clean up test file on error
            test_file_path = os.path.join(os.path.dirname(__file__), 'test_document.txt')
            if os.path.exists(test_file_path):
                try:
                    os.remove(test_file_path)
                except:
                    pass
    
    def test_function_call_registration(self):
        """Test 6: Function call registration"""
        self.test_results['tests_run'] += 1
        
        try:
            logger.bind(tag=TAG).info("[TEST] Testing function call registration")
            
            # Check if function files exist
            functions_dir = os.path.join(os.path.dirname(__file__), 'plugins_func', 'functions')
            required_functions = [
                'educational_document_upload.py',
                'educational_document_batch_upload.py',
                'educational_collection_info.py'
            ]
            
            missing_functions = []
            for func_file in required_functions:
                func_path = os.path.join(functions_dir, func_file)
                if not os.path.exists(func_path):
                    missing_functions.append(func_file)
            
            if missing_functions:
                raise Exception(f"Missing function files: {missing_functions}")
            
            logger.bind(tag=TAG).info("[TEST] ✅ Function call files exist")
            self.test_results['tests_passed'] += 1
            
        except Exception as e:
            error_msg = f"Function call registration test failed: {str(e)}"
            logger.bind(tag=TAG).error(f"[TEST] ❌ {error_msg}")
            self.test_results['tests_failed'] += 1
            self.test_results['errors'].append(error_msg)
    
    def print_test_results(self):
        """Print comprehensive test results"""
        logger.bind(tag=TAG).info("[TEST] " + "="*60)
        logger.bind(tag=TAG).info("[TEST] Enhanced Educational RAG Test Results")
        logger.bind(tag=TAG).info("[TEST] " + "="*60)
        logger.bind(tag=TAG).info(f"[TEST] Tests Run: {self.test_results['tests_run']}")
        logger.bind(tag=TAG).info(f"[TEST] Tests Passed: {self.test_results['tests_passed']}")
        logger.bind(tag=TAG).info(f"[TEST] Tests Failed: {self.test_results['tests_failed']}")
        
        if self.test_results['tests_failed'] > 0:
            logger.bind(tag=TAG).info("[TEST] " + "-"*40)
            logger.bind(tag=TAG).info("[TEST] Errors encountered:")
            for i, error in enumerate(self.test_results['errors'], 1):
                logger.bind(tag=TAG).info(f"[TEST] {i}. {error}")
        
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100
        logger.bind(tag=TAG).info(f"[TEST] Success Rate: {success_rate:.1f}%")
        
        if self.test_results['tests_failed'] == 0:
            logger.bind(tag=TAG).info("[TEST] 🎉 All tests passed! Enhanced Educational RAG system is ready.")
        else:
            logger.bind(tag=TAG).info("[TEST] ⚠️ Some tests failed. Check errors above and install missing dependencies.")
        
        logger.bind(tag=TAG).info("[TEST] " + "="*60)


def main():
    """Main test function"""
    try:
        # Initialize and run tests
        test_suite = EnhancedEducationalRAGTest()
        results = test_suite.run_all_tests()
        
        # Return appropriate exit code
        return 0 if results['tests_failed'] == 0 else 1
        
    except Exception as e:
        logger.bind(tag=TAG).error(f"[TEST] Fatal error in test suite: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
"""
Document Loader Manager for Educational RAG System
Adapted from RAG sample project for xiaozhi-server integration
Handles PDF and other document formats for educational content ingestion
"""

import os
import logging
from typing import List, Dict, Any
from pathlib import Path

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    DirectoryLoader,
    UnstructuredFileLoader,
    CSVLoader,
    JSONLoader
)
from langchain_core.documents import Document

from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class DocumentLoaderManager:
    """Document loader manager for educational content processing"""
    
    def __init__(self):
        """Initialize the document loader manager"""
        logger.bind(tag=TAG).info("[DOC-LOADER] Initializing document loader manager")
    
    def load_text_file(self, file_path: str) -> List[Document]:
        """Load documents from a text file"""
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            logger.bind(tag=TAG).info(f"[DOC-LOADER] Loaded {len(documents)} documents from {file_path}")
            return documents
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-LOADER] Failed to load text file {file_path}: {e}")
            return []
    
    def load_pdf_file(self, file_path: str) -> List[Document]:
        """Load documents from a PDF file"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            logger.bind(tag=TAG).info(f"[DOC-LOADER] Loaded {len(documents)} pages from PDF {file_path}")
            return documents
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-LOADER] Failed to load PDF file {file_path}: {e}")
            return []
    
    def load_csv_file(self, file_path: str, source_column: str = None) -> List[Document]:
        """Load documents from a CSV file"""
        try:
            loader = CSVLoader(file_path, source_column=source_column)
            documents = loader.load()
            logger.bind(tag=TAG).info(f"[DOC-LOADER] Loaded {len(documents)} rows from CSV {file_path}")
            return documents
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-LOADER] Failed to load CSV file {file_path}: {e}")
            return []
    
    def load_json_file(self, file_path: str, jq_schema: str = '.', text_content: bool = False) -> List[Document]:
        """Load documents from a JSON file"""
        try:
            loader = JSONLoader(
                file_path=file_path,
                jq_schema=jq_schema,
                text_content=text_content
            )
            documents = loader.load()
            logger.bind(tag=TAG).info(f"[DOC-LOADER] Loaded {len(documents)} documents from JSON {file_path}")
            return documents
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-LOADER] Failed to load JSON file {file_path}: {e}")
            return []
    
    def load_directory(self, directory_path: str, glob_pattern: str = "**/*.pdf", 
                      loader_cls: Any = PyPDFLoader, recursive: bool = True) -> List[Document]:
        """Load documents from a directory"""
        try:
            loader = DirectoryLoader(
                directory_path,
                glob=glob_pattern,
                loader_cls=loader_cls,
                recursive=recursive,
                show_progress=True
            )
            documents = loader.load()
            logger.bind(tag=TAG).info(f"[DOC-LOADER] Loaded {len(documents)} documents from directory {directory_path}")
            return documents
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-LOADER] Failed to load directory {directory_path}: {e}")
            return []
    
    def load_unstructured(self, file_path: str) -> List[Document]:
        """Load documents using unstructured loader"""
        try:
            loader = UnstructuredFileLoader(file_path)
            documents = loader.load()
            logger.bind(tag=TAG).info(f"[DOC-LOADER] Loaded {len(documents)} documents from unstructured file {file_path}")
            return documents
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-LOADER] Failed to load unstructured file {file_path}: {e}")
            return []
    
    def load_multiple_files(self, file_paths: List[str]) -> List[Document]:
        """Load documents from multiple files"""
        all_documents = []
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if not path.exists():
                logger.bind(tag=TAG).warning(f"[DOC-LOADER] File {file_path} does not exist")
                continue
            
            if path.suffix.lower() == '.txt':
                documents = self.load_text_file(file_path)
            elif path.suffix.lower() == '.pdf':
                documents = self.load_pdf_file(file_path)
            elif path.suffix.lower() == '.csv':
                documents = self.load_csv_file(file_path)
            elif path.suffix.lower() == '.json':
                documents = self.load_json_file(file_path)
            else:
                documents = self.load_unstructured(file_path)
            
            all_documents.extend(documents)
        
        logger.bind(tag=TAG).info(f"[DOC-LOADER] Loaded total of {len(all_documents)} documents from {len(file_paths)} files")
        return all_documents
    
    def add_metadata_to_documents(self, documents: List[Document], 
                                 metadata: Dict[str, Any]) -> List[Document]:
        """Add metadata to documents"""
        for doc in documents:
            doc.metadata.update(metadata)
        
        logger.bind(tag=TAG).debug(f"[DOC-LOADER] Added metadata to {len(documents)} documents")
        return documents
    
    def filter_documents_by_content(self, documents: List[Document], 
                                   min_length: int = 50) -> List[Document]:
        """Filter documents by content length"""
        filtered_docs = [doc for doc in documents if len(doc.page_content.strip()) >= min_length]
        
        logger.bind(tag=TAG).info(f"[DOC-LOADER] Filtered {len(documents)} documents to {len(filtered_docs)} (min_length={min_length})")
        return filtered_docs
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return ['.pdf', '.txt', '.csv', '.json', '.docx', '.doc', '.rtf', '.odt']


if __name__ == "__main__":
    # Test the document loader
    loader_manager = DocumentLoaderManager()
    logger.info("Document loader manager initialized successfully")
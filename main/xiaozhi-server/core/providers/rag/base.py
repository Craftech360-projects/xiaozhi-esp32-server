from abc import ABC, abstractmethod
from typing import List, Dict, Any
from config.logger import setup_logging

logger = setup_logging()


class RAGProviderBase(ABC):
    """Base class for RAG (Retrieval-Augmented Generation) providers"""
    
    def __init__(self, config: dict = None):
        """
        Initialize the RAG provider
        
        Args:
            config: Configuration dictionary for the provider
        """
        self.config = config or {}
        logger.info(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    def add_document(self, text: str, metadata: Dict[str, Any]) -> bool:
        """
        Add a document to the RAG database
        
        Args:
            text: The text content to index
            metadata: Metadata associated with the document (page, chapter, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> bool:
        """
        Add multiple documents to the RAG database
        
        Args:
            texts: List of text contents to index
            metadatas: List of metadata dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search for relevant documents
        
        Args:
            query: The search query
            top_k: Number of top results to return
            filters: Optional filters (subject, grade, etc.)
            
        Returns:
            Dict containing search results with documents and metadata
        """
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str = None) -> bool:
        """
        Delete a collection or all documents
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the current collection
        
        Returns:
            Dict containing collection statistics
        """
        pass
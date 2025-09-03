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
from langchain_community.document_loaders import S3DirectoryLoader
from langchain_core.documents import Document
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class DocumentLoaderManager:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
    
    def load_text_file(self, file_path: str) -> List[Document]:
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load text file {file_path}: {e}")
            return []
    
    def load_pdf_file(self, file_path: str) -> List[Document]:
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from PDF {file_path}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load PDF file {file_path}: {e}")
            return []
    
    def load_csv_file(self, file_path: str, source_column: str = None) -> List[Document]:
        try:
            loader = CSVLoader(file_path, source_column=source_column)
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} rows from CSV {file_path}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load CSV file {file_path}: {e}")
            return []
    
    def load_json_file(self, file_path: str, jq_schema: str = '.', text_content: bool = False) -> List[Document]:
        try:
            loader = JSONLoader(
                file_path=file_path,
                jq_schema=jq_schema,
                text_content=text_content
            )
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents from JSON {file_path}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load JSON file {file_path}: {e}")
            return []
    
    def load_directory(self, directory_path: str, glob_pattern: str = "**/*.txt", 
                      loader_cls: Any = TextLoader, recursive: bool = True) -> List[Document]:
        try:
            loader = DirectoryLoader(
                directory_path,
                glob=glob_pattern,
                loader_cls=loader_cls,
                recursive=recursive,
                show_progress=True
            )
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents from directory {directory_path}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load directory {directory_path}: {e}")
            return []
    
    def load_from_s3(self, bucket: str, prefix: str = "") -> List[Document]:
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            logger.error("AWS credentials not found in environment variables")
            return []
        
        try:
            loader = S3DirectoryLoader(
                bucket,
                prefix=prefix,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents from S3 bucket {bucket}/{prefix}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load from S3: {e}")
            return []
    
    def load_unstructured(self, file_path: str) -> List[Document]:
        try:
            loader = UnstructuredFileLoader(file_path)
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents from unstructured file {file_path}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load unstructured file {file_path}: {e}")
            return []
    
    def load_multiple_files(self, file_paths: List[str]) -> List[Document]:
        all_documents = []
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"File {file_path} does not exist")
                continue
            
            if path.suffix == '.txt':
                documents = self.load_text_file(file_path)
            elif path.suffix == '.pdf':
                documents = self.load_pdf_file(file_path)
            elif path.suffix == '.csv':
                documents = self.load_csv_file(file_path)
            elif path.suffix == '.json':
                documents = self.load_json_file(file_path)
            else:
                documents = self.load_unstructured(file_path)
            
            all_documents.extend(documents)
        
        logger.info(f"Loaded total of {len(all_documents)} documents from {len(file_paths)} files")
        return all_documents
    
    def add_metadata_to_documents(self, documents: List[Document], 
                                 metadata: Dict[str, Any]) -> List[Document]:
        for doc in documents:
            doc.metadata.update(metadata)
        return documents


if __name__ == "__main__":
    loader_manager = DocumentLoaderManager()
    
    sample_documents = loader_manager.load_text_file("sample.txt")
    
    pdf_documents = loader_manager.load_directory(
        "documents",
        glob_pattern="**/*.pdf",
        loader_cls=PyPDFLoader
    )
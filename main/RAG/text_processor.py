import os
import re
import logging
from typing import List, Optional
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter
)
from langchain_core.documents import Document
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class TextProcessor:
    def __init__(self):
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    def clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        text = text.strip()
        
        return text
    
    def recursive_split_documents(self, 
                                 documents: List[Document], 
                                 chunk_size: Optional[int] = None,
                                 chunk_overlap: Optional[int] = None,
                                 separators: Optional[List[str]] = None) -> List[Document]:
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        if separators is None:
            separators = ["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len
        )
        
        split_documents = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(split_documents)} chunks")
        
        return split_documents
    
    def character_split_documents(self,
                                documents: List[Document],
                                chunk_size: Optional[int] = None,
                                chunk_overlap: Optional[int] = None,
                                separator: str = "\n") -> List[Document]:
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=separator,
            length_function=len
        )
        
        split_documents = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(split_documents)} chunks")
        
        return split_documents
    
    def token_split_documents(self,
                            documents: List[Document],
                            chunk_size: Optional[int] = None,
                            chunk_overlap: Optional[int] = None,
                            encoding_name: str = "cl100k_base") -> List[Document]:
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        text_splitter = TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            encoding_name=encoding_name
        )
        
        split_documents = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(split_documents)} chunks using token splitter")
        
        return split_documents
    
    def markdown_split_documents(self,
                                documents: List[Document],
                                chunk_size: Optional[int] = None,
                                chunk_overlap: Optional[int] = None) -> List[Document]:
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        text_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        split_documents = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} markdown documents into {len(split_documents)} chunks")
        
        return split_documents
    
    def python_split_documents(self,
                             documents: List[Document],
                             chunk_size: Optional[int] = None,
                             chunk_overlap: Optional[int] = None) -> List[Document]:
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        text_splitter = PythonCodeTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        split_documents = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} Python documents into {len(split_documents)} chunks")
        
        return split_documents
    
    def process_documents(self,
                        documents: List[Document],
                        split_method: str = "recursive",
                        clean: bool = True,
                        chunk_size: Optional[int] = None,
                        chunk_overlap: Optional[int] = None) -> List[Document]:
        
        if clean:
            for doc in documents:
                doc.page_content = self.clean_text(doc.page_content)
        
        if split_method == "recursive":
            processed_docs = self.recursive_split_documents(documents, chunk_size, chunk_overlap)
        elif split_method == "character":
            processed_docs = self.character_split_documents(documents, chunk_size, chunk_overlap)
        elif split_method == "token":
            processed_docs = self.token_split_documents(documents, chunk_size, chunk_overlap)
        elif split_method == "markdown":
            processed_docs = self.markdown_split_documents(documents, chunk_size, chunk_overlap)
        elif split_method == "python":
            processed_docs = self.python_split_documents(documents, chunk_size, chunk_overlap)
        else:
            logger.warning(f"Unknown split method: {split_method}. Using recursive split.")
            processed_docs = self.recursive_split_documents(documents, chunk_size, chunk_overlap)
        
        for i, doc in enumerate(processed_docs):
            doc.metadata['chunk_id'] = i
            doc.metadata['chunk_size'] = len(doc.page_content)
        
        return processed_docs
    
    def deduplicate_documents(self, documents: List[Document]) -> List[Document]:
        seen_content = set()
        unique_documents = []
        
        for doc in documents:
            content_hash = hash(doc.page_content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_documents.append(doc)
        
        logger.info(f"Deduplicated {len(documents)} documents to {len(unique_documents)} unique documents")
        return unique_documents


if __name__ == "__main__":
    processor = TextProcessor()
    
    sample_docs = [
        Document(page_content="This is a sample document with some text content.", metadata={"source": "sample.txt"}),
        Document(page_content="Another document with different content for testing.", metadata={"source": "test.txt"})
    ]
    
    processed_docs = processor.process_documents(sample_docs)
    print(f"Processed {len(processed_docs)} document chunks")
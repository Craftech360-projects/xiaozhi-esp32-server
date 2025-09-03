import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

from ingestion_pipeline import IngestionPipeline
from rag_retriever import RAGRetriever, AdvancedRAGRetriever
from document_loader import DocumentLoaderManager
from groq_client import GroqClient, GroqRAGIntegration
from langchain_core.documents import Document

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class RAGPipeline:
    def __init__(self, 
                 collection_name: Optional[str] = None,
                 embedding_provider: str = "huggingface",
                 recreate_collection: bool = False):
        
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "rag_collection")
        self.embedding_provider = embedding_provider
        
        logger.info(f"Initializing RAG Pipeline with collection: {self.collection_name}")
        
        self.ingestion_pipeline = IngestionPipeline(
            collection_name=self.collection_name,
            embedding_provider=embedding_provider,
            recreate_collection=recreate_collection
        )
        
        self.retriever = AdvancedRAGRetriever(
            collection_name=self.collection_name,
            embedding_provider=embedding_provider
        )
    
    def ingest_data(self, 
                   source_type: str,
                   source_path: str,
                   **kwargs):
        
        logger.info(f"Starting data ingestion from {source_type}: {source_path}")
        
        if source_type == "file":
            result = self.ingestion_pipeline.ingest_from_file(source_path, **kwargs)
        elif source_type == "directory":
            result = self.ingestion_pipeline.ingest_from_directory(source_path, **kwargs)
        elif source_type == "s3":
            bucket, prefix = source_path.split("/", 1) if "/" in source_path else (source_path, "")
            result = self.ingestion_pipeline.ingest_from_s3(bucket, prefix, **kwargs)
        elif source_type == "text":
            documents = [Document(page_content=source_path, metadata={"source": "direct_input"})]
            result = self.ingestion_pipeline.ingest_documents(documents, **kwargs)
        else:
            logger.error(f"Unknown source type: {source_type}")
            return None
        
        logger.info(f"Ingestion completed: {result}")
        return result
    
    def query(self,
             query_text: str,
             mode: str = "similarity",
             k: int = 5,
             use_llm: bool = False):
        
        logger.info(f"Processing query: {query_text[:50]}...")
        
        if mode == "similarity":
            results = self.retriever.similarity_search(query_text, k=k)
            return self._format_search_results(results)
        
        elif mode == "hybrid":
            results = self.retriever.hybrid_search(query_text, k=k)
            return self._format_search_results(results)
        
        elif mode == "context":
            return self.retriever.retrieve_with_context(query_text, k=k)
        
        elif mode == "qa" or use_llm:
            return self.retriever.qa_with_retrieval(query_text, k=k)
        
        else:
            logger.error(f"Unknown query mode: {mode}")
            return None
    
    def _format_search_results(self, documents: List[Document]):
        results = []
        for i, doc in enumerate(documents, 1):
            results.append({
                "rank": i,
                "content": doc.page_content,
                "score": doc.metadata.get("score", 0),
                "source": doc.metadata.get("source", "unknown"),
                "metadata": {k: v for k, v in doc.metadata.items() if k not in ["score", "source"]}
            })
        return results
    
    def get_stats(self):
        return self.retriever.get_collection_stats()


def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline with Qdrant and LangChain")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    ingest_parser = subparsers.add_parser("ingest", help="Ingest data into Qdrant")
    ingest_parser.add_argument("--source-type", choices=["file", "directory", "s3", "text"], 
                              required=True, help="Type of data source")
    ingest_parser.add_argument("--source-path", required=True, 
                              help="Path to data source (file path, directory, S3 bucket, or text)")
    ingest_parser.add_argument("--collection", help="Collection name")
    ingest_parser.add_argument("--recreate", action="store_true", 
                              help="Recreate collection if it exists")
    ingest_parser.add_argument("--chunk-size", type=int, default=1000,
                              help="Chunk size for text splitting")
    ingest_parser.add_argument("--chunk-overlap", type=int, default=200,
                              help="Chunk overlap for text splitting")
    
    query_parser = subparsers.add_parser("query", help="Query the RAG system")
    query_parser.add_argument("--query", required=True, help="Query text")
    query_parser.add_argument("--mode", choices=["similarity", "hybrid", "context", "qa"],
                             default="similarity", help="Query mode")
    query_parser.add_argument("--k", type=int, default=5, 
                             help="Number of documents to retrieve")
    query_parser.add_argument("--use-llm", action="store_true",
                             help="Use LLM for answer generation")
    query_parser.add_argument("--llm-provider", choices=["openai", "groq", "auto"],
                             default="auto", help="LLM provider to use")
    query_parser.add_argument("--collection", help="Collection name")
    
    stats_parser = subparsers.add_parser("stats", help="Get collection statistics")
    stats_parser.add_argument("--collection", help="Collection name")
    
    demo_parser = subparsers.add_parser("demo", help="Run a demo with sample data")
    demo_parser.add_argument("--collection", help="Collection name")
    
    groq_parser = subparsers.add_parser("groq-demo", help="Run a Groq integration demo")
    groq_parser.add_argument("--collection", help="Collection name")
    groq_parser.add_argument("--stream", action="store_true", help="Use streaming response")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        pipeline = RAGPipeline(
            collection_name=args.collection,
            recreate_collection=args.recreate
        )
        
        result = pipeline.ingest_data(
            source_type=args.source_type,
            source_path=args.source_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
        
        if result:
            print("\nIngestion Results:")
            for key, value in result.items():
                print(f"  {key}: {value}")
    
    elif args.command == "query":
        pipeline = RAGPipeline(collection_name=args.collection)
        
        results = pipeline.query(
            query_text=args.query,
            mode=args.mode,
            k=args.k,
            use_llm=args.use_llm
        )
        
        if results:
            print("\nQuery Results:")
            if isinstance(results, list):
                for result in results:
                    print(f"\n--- Document {result['rank']} (Score: {result['score']:.4f}) ---")
                    print(f"Source: {result['source']}")
                    print(f"Content: {result['content'][:200]}...")
            elif isinstance(results, dict):
                if "answer" in results:
                    print(f"\nAnswer: {results['answer']}")
                    print("\nSource Documents:")
                    for doc in results.get("source_documents", []):
                        print(f"  - {doc['content'][:100]}...")
                else:
                    import json
                    print(json.dumps(results, indent=2))
    
    elif args.command == "stats":
        pipeline = RAGPipeline(collection_name=args.collection)
        stats = pipeline.get_stats()
        
        print("\nCollection Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    elif args.command == "demo":
        print("Running demo with sample data...")
        
        pipeline = RAGPipeline(
            collection_name=args.collection or "demo_collection",
            recreate_collection=True
        )
        
        sample_texts = [
            "Qdrant is a vector database & vector similarity search engine. It deploys as an API service providing search for the nearest high-dimensional vectors.",
            "LangChain is a framework for developing applications powered by language models. It provides tools for prompt management, chains, data augmented generation, agents, memory, and evaluation.",
            "RAG stands for Retrieval-Augmented Generation. It's a technique that combines information retrieval with text generation to produce more accurate and contextual responses.",
            "Vector databases are specialized databases designed to store and search high-dimensional vector embeddings efficiently.",
            "Embeddings are numerical representations of text, images, or other data that capture semantic meaning in a high-dimensional space."
        ]
        
        for text in sample_texts:
            pipeline.ingest_data("text", text)
        
        print("\nSample data ingested successfully!")
        
        test_queries = [
            "What is Qdrant?",
            "Explain RAG",
            "How do vector databases work?"
        ]
        
        for query in test_queries:
            print(f"\n\nQuery: {query}")
            results = pipeline.query(query, mode="similarity", k=2)
            
            for result in results[:2]:
                print(f"\n  Result {result['rank']} (Score: {result['score']:.4f}):")
                print(f"  {result['content'][:150]}...")
    
    elif args.command == "groq-demo":
        print("Running Groq integration demo...")
        
        try:
            # Initialize pipeline and Groq
            pipeline = RAGPipeline(
                collection_name=args.collection or "groq_demo_collection",
                recreate_collection=True
            )
            
            groq_client = GroqClient()
            groq_integration = GroqRAGIntegration(pipeline.retriever, groq_client)
            
            # Ingest sample data
            sample_texts = [
                "Groq is an AI infrastructure company that provides fast inference for large language models using their custom LPU (Language Processing Unit) chips.",
                "The Groq LPU is designed specifically for sequential workloads like language models, providing much faster inference than traditional GPUs.",
                "Groq supports popular open-source models like Llama, Mixtral, and Gemma with extremely low latency.",
                "Vector databases store high-dimensional embeddings and enable similarity search for RAG applications.",
                "RAG (Retrieval-Augmented Generation) combines document retrieval with language model generation for accurate, contextual responses."
            ]
            
            for text in sample_texts:
                pipeline.ingest_data("text", text)
            
            print("Sample data ingested successfully!")
            
            # Test queries with Groq
            test_queries = [
                "What is Groq and what makes it special?",
                "How does RAG work with vector databases?",
                "What are LPUs and how do they differ from GPUs?"
            ]
            
            for query in test_queries:
                print(f"\n{'='*60}")
                print(f"Query: {query}")
                print('='*60)
                
                if args.stream:
                    print("Streaming response:")
                    for chunk in groq_integration.answer_with_groq(query, k=3, stream=True):
                        print(chunk, end="")
                    print("\n")
                else:
                    answer = groq_integration.answer_with_groq(query, k=3)
                    print(f"Answer:\n{answer}")
        
        except Exception as e:
            print(f"Error running Groq demo: {e}")
            print("Make sure you have set your GROQ_API_KEY in the .env file")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
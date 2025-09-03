import os
import logging
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

from qdrant_client_setup import QdrantManager
from embedding_manager import EmbeddingManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class RAGRetriever:
    def __init__(self,
                 collection_name: Optional[str] = None,
                 embedding_provider: str = "huggingface"):
        
        self.qdrant_manager = QdrantManager()
        self.embedding_manager = EmbeddingManager(provider=embedding_provider)
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "rag_collection")
        
        self.vector_store = self._initialize_vector_store()
        self.llm = self._initialize_llm()
    
    def _initialize_vector_store(self):
        try:
            vector_store = QdrantVectorStore(
                client=self.qdrant_manager.client,
                collection_name=self.collection_name,
                embedding=self.embedding_manager.embeddings
            )
            logger.info(f"Initialized vector store with collection '{self.collection_name}'")
            return vector_store
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _initialize_llm(self):
        llm_provider = os.getenv("LLM_PROVIDER", "none").lower()
        
        if llm_provider == "openai":
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                llm = ChatOpenAI(
                    openai_api_key=openai_api_key,
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    temperature=0.7
                )
                logger.info("Initialized OpenAI LLM")
                return llm
            else:
                logger.warning("OpenAI API key not found.")
                return None
        
        elif llm_provider == "groq":
            groq_api_key = os.getenv("GROQ_API_KEY")
            if groq_api_key:
                llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    temperature=0.7,
                    max_tokens=2048
                )
                logger.info(f"Initialized Groq LLM with model: {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}")
                return llm
            else:
                logger.warning("Groq API key not found.")
                return None
        
        else:
            logger.info("No LLM provider configured. LLM-based QA will not be available.")
            return None
    
    def similarity_search(self, 
                         query: str,
                         k: int = 5,
                         score_threshold: Optional[float] = None) -> List[Document]:
        try:
            query_embedding = self.embedding_manager.embed_query(query)
            
            search_results = self.qdrant_manager.search(
                query_vector=query_embedding,
                collection_name=self.collection_name,
                limit=k,
                score_threshold=score_threshold
            )
            
            documents = []
            for result in search_results:
                doc = Document(
                    page_content=result.payload.get("text", ""),
                    metadata={
                        "score": result.score,
                        "source": result.payload.get("source", "unknown"),
                        "chunk_id": result.payload.get("chunk_id", 0),
                        **result.payload.get("metadata", {})
                    }
                )
                documents.append(doc)
            
            logger.info(f"Found {len(documents)} relevant documents for query")
            return documents
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            return []
    
    def hybrid_search(self,
                     query: str,
                     k: int = 5,
                     filter_dict: Optional[Dict[str, Any]] = None) -> List[Document]:
        try:
            if filter_dict:
                documents = self.vector_store.similarity_search(
                    query,
                    k=k,
                    filter=filter_dict
                )
            else:
                documents = self.vector_store.similarity_search(query, k=k)
            
            logger.info(f"Found {len(documents)} documents with hybrid search")
            return documents
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            return []
    
    def retrieve_with_context(self,
                            query: str,
                            k: int = 5,
                            include_metadata: bool = True) -> Dict[str, Any]:
        documents = self.similarity_search(query, k=k)
        
        result = {
            "query": query,
            "retrieved_documents": []
        }
        
        for doc in documents:
            doc_info = {
                "content": doc.page_content,
                "score": doc.metadata.get("score", 0)
            }
            
            if include_metadata:
                doc_info["metadata"] = {
                    k: v for k, v in doc.metadata.items() 
                    if k != "score"
                }
            
            result["retrieved_documents"].append(doc_info)
        
        return result
    
    def qa_with_retrieval(self,
                         query: str,
                         k: int = 5,
                         custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        
        if not self.llm:
            logger.error("LLM not initialized. Cannot perform QA.")
            return {
                "query": query,
                "answer": "LLM not available. Please provide OpenAI API key.",
                "source_documents": []
            }
        
        if custom_prompt:
            prompt_template = custom_prompt
        else:
            prompt_template = """Use the following pieces of context to answer the question at the end. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            Context: {context}
            
            Question: {question}
            
            Answer: """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": k}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        try:
            result = qa_chain({"query": query})
            
            response = {
                "query": query,
                "answer": result["result"],
                "source_documents": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    }
                    for doc in result.get("source_documents", [])
                ]
            }
            
            return response
        except Exception as e:
            logger.error(f"Failed to perform QA: {e}")
            return {
                "query": query,
                "answer": f"Error occurred: {str(e)}",
                "source_documents": []
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        try:
            collection_info = self.qdrant_manager.get_collection_info(self.collection_name)
            
            stats = {
                "collection_name": self.collection_name,
                "total_points": collection_info.points_count if collection_info else 0,
                "vector_dimension": collection_info.config.params.vectors.size if collection_info else 0,
                "status": "active" if collection_info else "not_found"
            }
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "error": str(e)
            }


class AdvancedRAGRetriever(RAGRetriever):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def rerank_results(self,
                      query: str,
                      documents: List[Document],
                      top_k: int = 3) -> List[Document]:
        
        query_embedding = self.embedding_manager.embed_query(query)
        
        scored_docs = []
        for doc in documents:
            doc_embedding = self.embedding_manager.embed_text(doc.page_content)[0]
            similarity = self.embedding_manager.compute_similarity(query_embedding, doc_embedding)
            scored_docs.append((doc, similarity))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        reranked_documents = [doc for doc, _ in scored_docs[:top_k]]
        logger.info(f"Reranked {len(documents)} documents to top {top_k}")
        
        return reranked_documents
    
    def multi_query_retrieval(self,
                            queries: List[str],
                            k_per_query: int = 3,
                            deduplicate: bool = True) -> List[Document]:
        all_documents = []
        seen_content = set()
        
        for query in queries:
            docs = self.similarity_search(query, k=k_per_query)
            
            for doc in docs:
                if deduplicate:
                    content_hash = hash(doc.page_content)
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        all_documents.append(doc)
                else:
                    all_documents.append(doc)
        
        logger.info(f"Retrieved {len(all_documents)} documents from {len(queries)} queries")
        return all_documents


if __name__ == "__main__":
    retriever = RAGRetriever()
    
    stats = retriever.get_collection_stats()
    print(f"Collection stats: {stats}")
    
    query = "What is Qdrant?"
    results = retriever.similarity_search(query, k=3)
    
    print(f"\nSearch results for '{query}':")
    for i, doc in enumerate(results, 1):
        print(f"{i}. Score: {doc.metadata.get('score', 'N/A')}")
        print(f"   Content: {doc.page_content[:100]}...")
        print(f"   Source: {doc.metadata.get('source', 'unknown')}")
    
    qa_result = retriever.qa_with_retrieval(query)
    print(f"\nQA Result:")
    print(f"Answer: {qa_result['answer']}")
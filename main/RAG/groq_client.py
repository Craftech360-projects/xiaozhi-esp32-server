import os
import logging
from typing import Dict, List, Any, Optional, Generator
from groq import Groq
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class GroqClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable or pass api_key parameter.")
        
        self.client = Groq(api_key=self.api_key)
        logger.info(f"Initialized Groq client with model: {self.model}")
    
    def chat_completion(self,
                       messages: List[Dict[str, str]],
                       model: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 2048,
                       top_p: float = 1.0,
                       stream: bool = False) -> Any:
        """
        Create a chat completion using Groq API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to instance model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            stream: Whether to stream the response
        
        Returns:
            Chat completion response or generator for streaming
        """
        try:
            completion = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                stop=None
            )
            return completion
        except Exception as e:
            logger.error(f"Failed to create chat completion: {e}")
            raise
    
    def simple_chat(self, 
                   user_message: str,
                   system_message: Optional[str] = None,
                   **kwargs) -> str:
        """
        Simple chat interface that returns just the text response
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            completion = self.chat_completion(messages, stream=False, **kwargs)
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to get simple chat response: {e}")
            return f"Error: {str(e)}"
    
    def stream_chat(self,
                   user_message: str,
                   system_message: Optional[str] = None,
                   **kwargs) -> Generator[str, None, None]:
        """
        Streaming chat interface that yields text chunks
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            completion = self.chat_completion(messages, stream=True, **kwargs)
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Failed to stream chat response: {e}")
            yield f"Error: {str(e)}"
    
    def rag_answer(self,
                  query: str,
                  retrieved_docs: List[Dict[str, Any]],
                  custom_prompt: Optional[str] = None) -> str:
        """
        Generate an answer using retrieved documents from RAG
        """
        context = "\n\n".join([
            f"Document {i+1}: {doc.get('content', doc.get('text', str(doc)))}"
            for i, doc in enumerate(retrieved_docs)
        ])
        
        if custom_prompt:
            system_message = custom_prompt.format(context=context, question=query)
        else:
            system_message = f"""You are a helpful AI assistant. Use the following context to answer the user's question accurately.
If the answer is not in the context, say so clearly.

Context:
{context}

Question: {query}

Provide a clear, concise answer based on the context provided."""
        
        return self.simple_chat(query, system_message=system_message)
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Groq models
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []


class GroqRAGIntegration:
    """
    Integration class for using Groq directly with RAG pipeline
    """
    
    def __init__(self, rag_retriever, groq_client: Optional[GroqClient] = None):
        self.rag_retriever = rag_retriever
        self.groq_client = groq_client or GroqClient()
    
    def answer_with_groq(self,
                        query: str,
                        k: int = 5,
                        custom_prompt: Optional[str] = None,
                        stream: bool = False) -> str:
        """
        Answer a query using RAG retrieval + Groq generation
        """
        # Retrieve relevant documents
        docs = self.rag_retriever.similarity_search(query, k=k)
        
        if not docs:
            return "No relevant documents found for your query."
        
        # Prepare documents for Groq
        doc_data = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": doc.metadata.get("score", 0)
            }
            for doc in docs
        ]
        
        if stream:
            return self.groq_client.stream_chat(
                query,
                system_message=self._build_rag_prompt(doc_data, custom_prompt)
            )
        else:
            return self.groq_client.rag_answer(query, doc_data, custom_prompt)
    
    def _build_rag_prompt(self, docs: List[Dict[str, Any]], custom_prompt: Optional[str] = None) -> str:
        if custom_prompt:
            return custom_prompt
        
        context = "\n\n".join([
            f"Document {i+1} (Score: {doc['score']:.3f}):\n{doc['content']}"
            for i, doc in enumerate(docs)
        ])
        
        return f"""You are a helpful AI assistant. Use the following retrieved documents to answer the user's question accurately.
Pay attention to the relevance scores - higher scores indicate more relevant content.

If the answer is not clearly supported by the provided documents, say so.
Always cite which document(s) support your answer when possible.

Retrieved Documents:
{context}

Instructions:
1. Answer based primarily on the provided documents
2. Be concise but comprehensive
3. If information is incomplete, acknowledge the limitations
4. Reference document numbers when citing sources"""


if __name__ == "__main__":
    # Example usage
    groq_client = GroqClient()
    
    # Simple chat
    response = groq_client.simple_chat(
        "What is machine learning?",
        system_message="You are a helpful AI assistant specialized in explaining technical concepts."
    )
    print("Response:", response)
    
    # Streaming example
    print("\nStreaming response:")
    for chunk in groq_client.stream_chat("Explain neural networks in simple terms"):
        print(chunk, end="")
    print("\n")
    
    # Available models
    models = groq_client.get_available_models()
    print(f"Available models: {models[:5]}...")  # Show first 5
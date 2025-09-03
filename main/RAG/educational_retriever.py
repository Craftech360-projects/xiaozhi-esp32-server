import os
import logging
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

from qdrant_client_setup import QdrantManager
from embedding_manager import EmbeddingManager
from groq_client import GroqClient
from educational_config import Grade, Subject, get_collection_name, EDUCATIONAL_PROMPTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class EducationalRAGRetriever:
    def __init__(self, 
                 grade: Grade,
                 subject: Subject,
                 embedding_provider: str = "huggingface"):
        
        self.grade = grade
        self.subject = subject
        self.collection_name = get_collection_name(grade, subject)
        
        self.qdrant_manager = QdrantManager()
        self.embedding_manager = EmbeddingManager(provider=embedding_provider)
        
        # Initialize LLM (prefer Groq for educational use due to speed and cost)
        self.llm = self._initialize_llm()
        
        # Educational-specific settings
        self.default_k = 5  # Number of relevant chunks to retrieve
        self.min_score_threshold = 0.3  # Minimum relevance score
        
    def _initialize_llm(self):
        """Initialize LLM with preference for Groq for educational responses"""
        llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()
        
        if llm_provider == "groq" and os.getenv("GROQ_API_KEY"):
            return GroqClient(model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
        elif llm_provider == "openai" and os.getenv("OPENAI_API_KEY"):
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-3.5-turbo",
                temperature=0.5  # Lower temperature for educational content
            )
        else:
            logger.warning("No LLM configured. Only similarity search will be available.")
            return None
    
    def search_concepts(self, 
                       query: str,
                       k: int = None,
                       content_type: Optional[str] = None,
                       chapter_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for educational concepts with optional filters"""
        
        k = k or self.default_k
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_manager.embed_query(query)
            
            # Build filter conditions
            filter_conditions = {}
            if content_type:
                filter_conditions['content_category'] = content_type
            if chapter_number:
                filter_conditions['chapter_number'] = chapter_number
            
            # Search in Qdrant
            search_results = self.qdrant_manager.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                score_threshold=self.min_score_threshold,
                query_filter=filter_conditions if filter_conditions else None,
                with_payload=True
            )
            
            # Format results for educational use
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    'content': result.payload['text'],
                    'score': result.score,
                    'grade': result.payload.get('grade'),
                    'subject': result.payload.get('subject'),
                    'chapter_number': result.payload.get('chapter_number'),
                    'chapter_title': result.payload.get('chapter_title'),
                    'page_number': result.payload.get('page_number'),
                    'content_category': result.payload.get('content_category'),
                    'topics': result.payload.get('topics', []),
                    'difficulty_level': result.payload.get('difficulty_level'),
                    'file_name': result.payload.get('file_name')
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Found {len(formatted_results)} relevant concepts for: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search concepts: {e}")
            return []
    
    def explain_concept(self, 
                       query: str,
                       context_type: str = "concept_explanation",
                       k: int = None) -> Dict[str, Any]:
        """Provide a student-friendly explanation of a concept"""
        
        if not self.llm:
            return {
                "error": "No LLM available for explanations",
                "query": query,
                "relevant_content": self.search_concepts(query, k)
            }
        
        # Get relevant content
        relevant_docs = self.search_concepts(query, k)
        
        if not relevant_docs:
            return {
                "answer": f"I couldn't find information about '{query}' in your {self.subject.value} textbook. Could you try rephrasing your question?",
                "query": query,
                "relevant_content": []
            }
        
        # Build context from relevant documents
        context = self._build_educational_context(relevant_docs)
        
        # Use educational prompt
        prompt = EDUCATIONAL_PROMPTS.get(context_type, EDUCATIONAL_PROMPTS["concept_explanation"])
        
        try:
            if hasattr(self.llm, 'simple_chat'):  # Groq client
                system_message = prompt.format(context=context, question=query)
                answer = self.llm.simple_chat(query, system_message=system_message)
            else:  # LangChain LLM
                prompt_template = PromptTemplate.from_template(prompt)
                formatted_prompt = prompt_template.format(context=context, question=query)
                answer = self.llm.invoke(formatted_prompt).content
            
            return {
                "answer": answer,
                "query": query,
                "relevant_content": relevant_docs[:3],  # Show top 3 sources
                "grade": self.grade.value,
                "subject": self.subject.value
            }
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return {
                "error": f"Failed to generate explanation: {str(e)}",
                "query": query,
                "relevant_content": relevant_docs
            }
    
    def solve_problem(self, problem: str, k: int = None) -> Dict[str, Any]:
        """Help solve a math problem step by step"""
        return self.explain_concept(problem, "problem_solving", k)
    
    def clarify_doubt(self, doubt: str, k: int = None) -> Dict[str, Any]:
        """Help clarify student doubts and misconceptions"""
        return self.explain_concept(doubt, "doubt_clarification", k)
    
    def get_chapter_summary(self, chapter_number: int) -> Dict[str, Any]:
        """Get a comprehensive summary of a chapter"""
        
        # Search for all content from the specific chapter
        chapter_docs = self.search_concepts(
            query=f"chapter {chapter_number} summary concepts",
            k=20,  # Get more content for comprehensive summary
            chapter_number=chapter_number
        )
        
        if not chapter_docs:
            return {
                "error": f"No content found for Chapter {chapter_number}",
                "chapter_number": chapter_number
            }
        
        # Get chapter title
        chapter_title = chapter_docs[0].get('chapter_title', f"Chapter {chapter_number}")
        
        # Generate summary
        query = f"Summarize Chapter {chapter_number}: {chapter_title}"
        context = self._build_educational_context(chapter_docs)
        
        if self.llm:
            prompt = EDUCATIONAL_PROMPTS["chapter_summary"]
            
            try:
                if hasattr(self.llm, 'simple_chat'):
                    system_message = prompt.format(context=context, question=query)
                    summary = self.llm.simple_chat(query, system_message=system_message)
                else:
                    prompt_template = PromptTemplate.from_template(prompt)
                    formatted_prompt = prompt_template.format(context=context, question=query)
                    summary = self.llm.invoke(formatted_prompt).content
                
                return {
                    "chapter_number": chapter_number,
                    "chapter_title": chapter_title,
                    "summary": summary,
                    "topics_covered": list(set([
                        topic for doc in chapter_docs 
                        for topic in doc.get('topics', [])
                    ])),
                    "content_types": list(set([
                        doc.get('content_category') for doc in chapter_docs
                    ]))
                }
                
            except Exception as e:
                logger.error(f"Failed to generate chapter summary: {e}")
        
        # Fallback: return structured information without LLM
        return {
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "content_snippets": [doc['content'][:200] + "..." for doc in chapter_docs[:5]],
            "topics_covered": list(set([
                topic for doc in chapter_docs 
                for topic in doc.get('topics', [])
            ])),
            "content_types": list(set([
                doc.get('content_category') for doc in chapter_docs
            ]))
        }
    
    def find_related_topics(self, topic: str, k: int = 8) -> List[Dict[str, Any]]:
        """Find topics related to the given topic"""
        
        related_docs = self.search_concepts(topic, k)
        
        # Extract unique related topics
        related_topics = set()
        for doc in related_docs:
            related_topics.update(doc.get('topics', []))
        
        # Remove the original topic if present
        related_topics.discard(topic)
        
        return {
            "original_topic": topic,
            "related_topics": list(related_topics),
            "related_content": related_docs
        }
    
    def search_by_difficulty(self, difficulty: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search content by difficulty level"""
        
        try:
            # Search with difficulty filter
            query_embedding = self.embedding_manager.embed_query(f"{difficulty} level content")
            
            search_results = self.qdrant_manager.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                query_filter={"difficulty_level": difficulty},
                with_payload=True
            )
            
            return [
                {
                    'content': result.payload['text'][:200] + "...",
                    'chapter_number': result.payload.get('chapter_number'),
                    'chapter_title': result.payload.get('chapter_title'),
                    'content_category': result.payload.get('content_category'),
                    'difficulty_level': result.payload.get('difficulty_level')
                }
                for result in search_results
            ]
            
        except Exception as e:
            logger.error(f"Failed to search by difficulty: {e}")
            return []
    
    def _build_educational_context(self, docs: List[Dict[str, Any]]) -> str:
        """Build context string from educational documents"""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            chapter_info = ""
            if doc.get('chapter_number') and doc.get('chapter_title'):
                chapter_info = f"Chapter {doc['chapter_number']}: {doc['chapter_title']}"
            
            content_type = doc.get('content_category', 'concept').title()
            
            context_part = f"[{content_type}] {chapter_info}\n{doc['content']}"
            context_parts.append(context_part)
        
        return "\n\n---\n\n".join(context_parts)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the educational collection"""
        try:
            collection_info = self.qdrant_manager.get_collection_info(self.collection_name)
            if not collection_info:
                return {"error": f"Collection {self.collection_name} not found"}
            
            return {
                "collection_name": self.collection_name,
                "grade": self.grade.value,
                "subject": self.subject.value,
                "total_content": collection_info.points_count,
                "vector_dimension": collection_info.config.params.vectors.size,
                "status": "ready"
            }
            
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    # Example usage
    retriever = EducationalRAGRetriever(Grade.CLASS_6, Subject.MATHEMATICS)
    
    # Get collection stats
    stats = retriever.get_collection_stats()
    print("Collection stats:", stats)
    
    # Search for concepts
    results = retriever.search_concepts("fractions", k=3)
    print(f"\nFound {len(results)} results for 'fractions'")
    
    # Get explanation
    explanation = retriever.explain_concept("What are equivalent fractions?")
    print(f"\nExplanation: {explanation.get('answer', 'No answer available')}")
    
    # Get chapter summary
    summary = retriever.get_chapter_summary(7)  # Chapter 7: Fractions
    print(f"\nChapter 7 Summary: {summary.get('summary', 'No summary available')[:200]}...")
# src/llm_handler.py
from groq import Groq
from typing import List, Dict, Any
import logging

class LLMHandler:
    def __init__(self, config):
        self.config = config
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.logger = logging.getLogger(__name__)
        self.conversation_history = []
        
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]], 
                         conversation_history: List[str] = None) -> Dict[str, Any]:
        """Generate response using retrieved context"""
        
        # Prepare context from retrieved documents
        context_text = self._prepare_context(context_docs)
        
        # Build conversation context
        conversation_context = self._build_conversation_context(conversation_history)
        
        # Create prompt
        prompt = self._create_prompt(query, context_text, conversation_context)
        
        try:
            # Generate response
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                top_p=1,
                stream=False
            )
            
            answer = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append(f"User: {query}")
            self.conversation_history.append(f"Assistant: {answer}")
            
            return {
                'answer': answer,
                'sources_used': len(context_docs),
                'context_types': list(set([doc['metadata']['chunk_type'] for doc in context_docs])),
                'confidence': self._calculate_confidence(context_docs)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return {
                'answer': "I apologize, but I encountered an error while generating a response. Please try again.",
                'sources_used': 0,
                'context_types': [],
                'confidence': 0.0
            }
    
    def _prepare_context(self, context_docs: List[Dict[str, Any]]) -> str:
        """Prepare context from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(context_docs, 1):
            content = doc['content']
            metadata = doc['metadata']
            
            context_part = f"""
            SOURCE {i} (Page {metadata['page_number']}, Type: {metadata['chunk_type']}):
            {content}
            """
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _build_conversation_context(self, conversation_history: List[str]) -> str:
        """Build conversation context"""
        if not conversation_history:
            return ""
        
        return "CONVERSATION HISTORY:\n" + "\n".join(conversation_history[-6:])  # Last 3 exchanges
    
    def _create_prompt(self, query: str, context_text: str, conversation_context: str) -> str:
        """Create the complete prompt"""
        prompt = f"""
        {conversation_context}
        
        CONTEXT FROM DOCUMENTS:
        {context_text}
        
        USER QUESTION: {query}
        
        Please provide a comprehensive and accurate answer based on the context provided. 
        If the context includes tables, present the data clearly. 
        If the context includes image content (OCR), mention that information was extracted from images.
        If you cannot find relevant information in the context, please say so clearly.
        """
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the LLM"""
        return """
        You are an intelligent document assistant that helps users find information from PDF documents. 
        You have access to content extracted from PDFs including text, tables, and images (via OCR).
        
        Guidelines:
        1. Always base your answers on the provided context
        2. If information is from a table, format it clearly
        3. If information is from an image (OCR), mention this
        4. Be precise and cite the page numbers when relevant
        5. If you don't have enough context, say so clearly
        6. Maintain a helpful and conversational tone
        7. For complex queries, break down your answer into clear sections
        """
    
    def _calculate_confidence(self, context_docs: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on retrieved context"""
        if not context_docs:
            return 0.0
        
        # Base confidence on similarity scores and number of sources
        avg_score = sum([doc['score'] for doc in context_docs]) / len(context_docs)
        source_bonus = min(len(context_docs) / 5, 1.0)  # Bonus for multiple sources
        
        return min(avg_score * (1 + source_bonus * 0.2), 1.0)
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

# src/retriever.py
from typing import List, Dict, Any, Tuple
import re
import numpy as np
from collections import defaultdict

class SmartRetriever:
    def __init__(self, vector_store, config):
        self.vector_store = vector_store
        self.config = config
        
    def retrieve(self, query: str, context_history: List[str] = None) -> Dict[str, Any]:
        """Intelligent retrieval with context awareness"""
        
        # Enhance query with context if available
        enhanced_query = self._enhance_query_with_context(query, context_history)
        
        # Detect query type
        query_type = self._detect_query_type(query)
        
        # Perform search
        search_results = self.vector_store.search(
            enhanced_query, 
            n_results=self.config.TOP_K_RESULTS * 2  # Get more for filtering
        )
        
        # Filter and rank results based on query type
        filtered_results = self._filter_by_query_type(search_results, query_type)
        
        # Re-rank results
        ranked_results = self._rerank_results(filtered_results, query, query_type)
        
        return {
            'query': query,
            'query_type': query_type,
            'results': ranked_results[:self.config.TOP_K_RESULTS],
            'total_found': len(search_results['documents'])
        }
    
    def _enhance_query_with_context(self, query: str, context_history: List[str]) -> str:
        """Enhance query with conversation context"""
        if not context_history:
            return query
            
        # Simple context enhancement - can be made more sophisticated
        recent_context = ' '.join(context_history[-2:])  # Last 2 exchanges
        return f"{recent_context} {query}"
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query to optimize retrieval"""
        query_lower = query.lower()
        
        # Table/data queries
        if any(word in query_lower for word in ['table', 'data', 'numbers', 'statistics', 'rows', 'columns']):
            return 'table'
        
        # Image/visual queries
        if any(word in query_lower for word in ['image', 'picture', 'visual', 'diagram', 'chart', 'figure']):
            return 'image'
        
        # Factual queries
        if any(word in query_lower for word in ['what', 'when', 'where', 'who', 'how many', 'which']):
            return 'factual'
        
        # Conceptual queries
        if any(word in query_lower for word in ['why', 'how', 'explain', 'describe', 'concept']):
            return 'conceptual'
        
        return 'general'
    
    def _filter_by_query_type(self, search_results: Dict[str, Any], query_type: str) -> Dict[str, Any]:
        """Filter results based on query type"""
        if query_type == 'general':
            return search_results
        
        filtered_docs = []
        filtered_metadata = []
        filtered_distances = []
        
        for doc, meta, dist in zip(search_results['documents'], 
                                  search_results['metadatas'], 
                                  search_results['distances']):
            
            # Boost relevance for matching content types
            if query_type == 'table' and meta['chunk_type'] == 'table':
                filtered_docs.append(doc)
                filtered_metadata.append(meta)
                filtered_distances.append(dist * 0.8)  # Boost relevance
            elif query_type == 'image' and meta['chunk_type'] == 'image':
                filtered_docs.append(doc)
                filtered_metadata.append(meta)
                filtered_distances.append(dist * 0.8)
            elif query_type in ['factual', 'conceptual'] and meta['chunk_type'] == 'text':
                filtered_docs.append(doc)
                filtered_metadata.append(meta)
                filtered_distances.append(dist)
            else:
                # Include all types but with original distance
                filtered_docs.append(doc)
                filtered_metadata.append(meta)
                filtered_distances.append(dist)
        
        return {
            'documents': filtered_docs,
            'metadatas': filtered_metadata,
            'distances': filtered_distances
        }
    
    def _rerank_results(self, results: Dict[str, Any], query: str, query_type: str) -> List[Dict[str, Any]]:
        """Re-rank results based on additional criteria"""
        ranked_results = []
        
        for doc, meta, dist in zip(results['documents'], results['metadatas'], results['distances']):
            score = 1 - dist  # Convert distance to similarity score
            
            # Boost score based on content relevance
            if query_type == 'table' and meta['chunk_type'] == 'table':
                score *= 1.2
            elif query_type == 'image' and meta['chunk_type'] == 'image':
                score *= 1.2
            
            # Boost based on content length for conceptual queries
            if query_type == 'conceptual' and meta.get('word_count', 0) > 100:
                score *= 1.1
            
            ranked_results.append({
                'content': doc,
                'metadata': meta,
                'score': score,
                'distance': dist
            })
        
        # Sort by score (descending)
        ranked_results.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked_results

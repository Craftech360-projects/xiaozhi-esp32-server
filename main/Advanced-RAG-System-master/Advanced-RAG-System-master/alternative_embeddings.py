# alternative_embeddings.py - Make sure this exists
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

class AlternativeEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=384,  # Same dimension as all-MiniLM-L6-v2
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.is_fitted = False
        
    def encode(self, texts):
        """Encode texts to embeddings"""
        if isinstance(texts, str):
            texts = [texts]
        
        if not self.is_fitted:
            # Fit on the first texts
            self.vectorizer.fit(texts + [
                "This is sample text for fitting the vectorizer",
                "Machine learning and artificial intelligence", 
                "Document processing and text analysis"
            ])
            self.is_fitted = True
        
        # Transform texts to vectors
        vectors = self.vectorizer.transform(texts).toarray()
        
        # Ensure exactly 384 dimensions
        if vectors.shape[11] < 384:
            padding = np.zeros((vectors.shape, 384 - vectors.shape[11]))
            vectors = np.hstack([vectors, padding])
        elif vectors.shape[11] > 384:
            vectors = vectors[:, :384]
            
        return vectors if len(texts) > 1 else vectors

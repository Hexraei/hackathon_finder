"""
Embedding Utilities for AI-Powered Search
==========================================
Uses Sentence-Transformers (MiniLM) for local, free embeddings.
"""
from typing import List, Optional
from functools import lru_cache
import os

# Force CPU to avoid CUDA errors
os.environ['CUDA_VISIBLE_DEVICES'] = ''

# Lazy load model
_model = None

def get_model():
    """Load embedding model (lazy initialization)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')  # Force CPU
    return _model

@lru_cache(maxsize=1000)  # Cache up to 1000 query embeddings
def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for a text string.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats (384 dimensions for MiniLM)
    """
    if not text or not text.strip():
        return []
    
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()

def generate_search_text(event: dict) -> str:
    """
    Combine event fields into searchable text for embedding.
    
    Args:
        event: Event dictionary with title, description, tags, etc.
        
    Returns:
        Combined text string
    """
    tags = event.get('tags', [])
    if isinstance(tags, list):
        tags = ' '.join(tags)
    
    parts = [
        tags, # Prioritize tags for better semantic matching
        event.get('title', ''),
        event.get('description', ''),
        event.get('location', ''),
        event.get('mode', '')
    ]
    return ' . '.join([p for p in parts if p and p.strip()])

def batch_generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently.
    
    Args:
        texts: List of text strings
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    return [emb.tolist() for emb in embeddings]

"""
Embedding Utilities for AI-Powered Search
==========================================
Uses Sentence-Transformers (MiniLM) for local, free embeddings.
"""
from typing import List, Optional
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
    parts = [
        event.get('title', ''),
        event.get('description', ''),
        ' '.join(event.get('tags', []) if isinstance(event.get('tags'), list) else []),
        event.get('location', ''),
        event.get('organizer', ''),
    ]
    return ' '.join(filter(None, parts))

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

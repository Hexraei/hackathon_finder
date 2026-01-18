"""
Vector Store using ChromaDB
============================
Local persistent vector database for semantic search.
"""
import os
from typing import List, Dict, Optional

# Lazy load ChromaDB
_client = None
_collection = None

def _get_collection():
    """Get or create the hackathons collection."""
    global _client, _collection
    if _collection is None:
        import chromadb
        from chromadb.config import Settings
        
        # Persistent storage in project directory
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
        _client = chromadb.PersistentClient(path=db_path)
        _collection = _client.get_or_create_collection(
            name="hackathons",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def upsert_event(event_id: str, embedding: List[float], metadata: dict):
    """
    Add or update an event in the vector store.
    
    Args:
        event_id: Unique event identifier
        embedding: Vector embedding (384 dims for MiniLM)
        metadata: Event metadata (title, source, url)
    """
    if not embedding:
        return
        
    collection = _get_collection()
    
    # Ensure metadata values are strings (ChromaDB requirement)
    clean_meta = {
        k: str(v) if v is not None else ""
        for k, v in metadata.items()
    }
    
    collection.upsert(
        ids=[event_id],
        embeddings=[embedding],
        metadatas=[clean_meta]
    )

def search_similar(query_embedding: List[float], top_k: int = 20) -> List[Dict]:
    """
    Find most similar events to the query embedding.
    
    Args:
        query_embedding: Vector embedding of search query
        top_k: Number of results to return
        
    Returns:
        List of dicts with id, score, and metadata
    """
    if not query_embedding:
        return []
        
    collection = _get_collection()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas", "distances"]
    )
    
    # Convert to list of dicts
    output = []
    if results['ids'] and results['ids'][0]:
        for i, event_id in enumerate(results['ids'][0]):
            output.append({
                "id": event_id,
                "score": round(1 - results['distances'][0][i], 4),  # Convert distance to similarity
                **results['metadatas'][0][i]
            })
    
    return output

def get_collection_count() -> int:
    """Get number of events in vector store."""
    try:
        collection = _get_collection()
        return collection.count()
    except:
        return 0

def clear_collection():
    """Clear all events from vector store (for testing)."""
    global _collection
    if _collection:
        _client.delete_collection("hackathons")
        _collection = None

"""
Vectorize Existing Events
=========================
One-time script to generate embeddings for all existing hackathons.
Run this after scraping to populate the vector store.
"""
import sys
sys.path.insert(0, '.')

from database.db_manager import DatabaseManager
from utils.embeddings import generate_embedding, generate_search_text
from database.vector_store import upsert_event, get_collection_count

def vectorize_all_events():
    """Generate embeddings for all events in the database."""
    print("=" * 50)
    print("  Vectorizing Hackathon Events")
    print("=" * 50)
    
    # Get all events from SQLite
    db = DatabaseManager('hackathons.db')
    events, total = db.query_events(page=1, page_size=50000)
    
    print(f"\nFound {total} events in database")
    print(f"Current vector store count: {get_collection_count()}")
    print("\nGenerating embeddings (this may take a few minutes)...\n")
    
    success = 0
    failed = 0
    
    for i, event in enumerate(events):
        try:
            # Create search text from event
            event_dict = event.to_dict()
            search_text = generate_search_text(event_dict)
            
            if not search_text.strip():
                failed += 1
                continue
            
            # Generate embedding
            embedding = generate_embedding(search_text)
            
            if not embedding:
                failed += 1
                continue
            
            # Store in ChromaDB
            upsert_event(
                event_id=event.id,
                embedding=embedding,
                metadata={
                    "title": event.title or "",
                    "source": event.source or "",
                    "url": event.url or "",
                    "mode": event.mode or "",
                }
            )
            success += 1
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{total} events...")
                
        except Exception as e:
            print(f"  Error on event {event.id}: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"  Vectorization Complete!")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Vector Store Count: {get_collection_count()}")
    print("=" * 50)

if __name__ == '__main__':
    vectorize_all_events()

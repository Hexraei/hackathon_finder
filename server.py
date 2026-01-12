"""
HackFind Server
===============
Flask server with API for hackathon data.
"""
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, send_file, jsonify, request

BASE_DIR = Path(__file__).parent.absolute()
UI_DIR = BASE_DIR / 'ui'
sys.path.insert(0, str(BASE_DIR))

app = Flask(__name__)

db = None

def get_db():
    global db
    if db is None:
        from database.db_manager import DatabaseManager
        db = DatabaseManager(str(BASE_DIR / "hackathons.db"))
    return db

def recalculate_status(event_dict):
    """Recalculate status based on current date (not scrape date)."""
    today = datetime.now().date()
    
    start_date = event_dict.get('start_date')
    end_date = event_dict.get('end_date')
    
    if not start_date:
        event_dict['status'] = 'unknown'
        return event_dict
    
    try:
        # Parse start date
        if isinstance(start_date, str):
            start = datetime.strptime(start_date[:10], "%Y-%m-%d").date()
        else:
            start = start_date
        
        # Parse end date (fall back to start if not available)
        if end_date:
            if isinstance(end_date, str):
                end = datetime.strptime(end_date[:10], "%Y-%m-%d").date()
            else:
                end = end_date
        else:
            end = start
        
        # Determine current status
        if today < start:
            event_dict['status'] = 'upcoming'
        elif start <= today <= end:
            event_dict['status'] = 'ongoing'
        else:
            event_dict['status'] = 'ended'
            
    except (ValueError, TypeError):
        event_dict['status'] = 'unknown'
    
    return event_dict

# === Serve UI ===
@app.route('/')
def home():
    return send_file(str(UI_DIR / 'index.html'))

@app.route('/styles.css')
def styles():
    return send_file(str(UI_DIR / 'styles.css'), mimetype='text/css')

@app.route('/app.js')
def appjs():
    return send_file(str(UI_DIR / 'app.js'), mimetype='application/javascript')

# === API ===
@app.route('/api/hackathons')
def api_hackathons():
    """Get ALL hackathons from database"""
    try:
        database = get_db()
        search = request.args.get('search', '')
        mode = request.args.get('mode', '')
        location = request.args.get('location', '')

        # Get ALL events - use large page_size to get everything
        events, total = database.query_events(
            search=search if search else None,
            page=1,
            page_size=50000  # Return all events
        )
        
        print(f"API: Returning {len(events)} hackathons (total in DB: {total})")
        
        # Filter by mode if specified
        if mode:
            events = [e for e in events if e.mode and mode.lower() in e.mode.lower()]
        
        # Filter by location if specified  
        if location:
            events = [e for e in events if e.location and location.lower() in e.location.lower()]
        
        # Recalculate status dynamically based on current date
        result = [recalculate_status(e.to_dict()) for e in events]
        return jsonify(result)
    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/api/search/ai')
def ai_search():
    """Semantic search using AI embeddings."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    
    # Limit query length for performance
    if len(query) > 500:
        query = query[:500]
    
    try:
        from utils.embeddings import generate_embedding
        from database.vector_store import search_similar, get_collection_count
        
        # Check if vector store has data
        count = get_collection_count()
        if count == 0:
            return jsonify({"error": "Vector store is empty. Run vectorize_events.py first."}), 503
        
        # Generate embedding for query (cached via lru_cache)
        query_embedding = generate_embedding(query)
        if not query_embedding:
            return jsonify({"error": "Failed to generate embedding"}), 500
        
        # 1. Vector Search (Semantic)
        vector_results = search_similar(query_embedding, top_k=20)
        
        # 2. Keyword Search (Lexical)
        database = get_db()
        keyword_events, _ = database.query_events(search=query, page_size=20)
        
        # 3. Merge and Rank (Hybrid)
        rank_map = {}
        
        # Process Vector Results
        for r in vector_results:
            rank_map[r['id']] = {
                'event': None, # Will fetch later to save DB hits? Actually db.get_event is fast
                'id': r['id'],
                'score': r['score'],
                'matches': ['semantic']
            }
            
        # Process Keyword Results
        keyword_base_score = 0.4 # Baseline for keyword-only match
        keyword_boost = 0.2 # Boost if it also matches vector
        
        for ke in keyword_events:
             # Convert DB event to dict immediately
             k_dict = recalculate_status(ke.to_dict())
             
             if ke.id in rank_map:
                 # It's in both! Boost it.
                 rank_map[ke.id]['score'] += keyword_boost
                 rank_map[ke.id]['matches'].append('keyword')
                 rank_map[ke.id]['event_dict'] = k_dict # Prefer object we already have
             else:
                 # Keyword only
                 rank_map[ke.id] = {
                     'event_dict': k_dict,
                     'id': ke.id,
                     'score': keyword_base_score,
                     'matches': ['keyword']
                 }
                 
        # Fetch missing vector event objects
        for vid, item in rank_map.items():
            if 'event_dict' not in item:
                event = database.get_event(vid)
                if event:
                    item['event_dict'] = recalculate_status(event.to_dict())
                else:
                    item['event_dict'] = None

        # Filter out None events and Sort
        final_list = []
        for item in rank_map.values():
            if item['event_dict']:
                ed = item['event_dict']
                ed['similarity_score'] = round(item['score'], 4)
                ed['match_types'] = item['matches'] # debug info
                final_list.append(ed)
                
        # Sort by score descending
        final_list.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        enriched = final_list[:30] # Return top 30 mixed
        
        print(f"AI Search (Hybrid): '{query[:50]}...' -> {len(enriched)} results")
        return jsonify(enriched)
        
    except ImportError as e:
        return jsonify({"error": f"AI dependencies not installed: {e}"}), 503
    except Exception as e:
        print(f"AI Search Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """Get database stats"""
    try:
        database = get_db()
        return jsonify(database.get_statistics())
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print(f"\n{'='*50}")
    print(f"  HackFind Server")
    print(f"  Port: 8000")
    print(f"  UI: {UI_DIR}")
    print(f"{'='*50}")
    print(f"  Open: http://localhost:8000")
    print(f"{'='*50}\n")
    app.run(port=8001, debug=False, host='127.0.0.1')

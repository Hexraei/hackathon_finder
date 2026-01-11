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
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    
    try:
        from utils.embeddings import generate_embedding
        from database.vector_store import search_similar, get_collection_count
        
        # Check if vector store has data
        count = get_collection_count()
        if count == 0:
            return jsonify({"error": "Vector store is empty. Run vectorize_events.py first."}), 503
        
        # Generate embedding for query
        query_embedding = generate_embedding(query)
        if not query_embedding:
            return jsonify({"error": "Failed to generate embedding"}), 500
        
        # Search vector store
        results = search_similar(query_embedding, top_k=50)
        
        # Enrich with full event data from SQLite
        database = get_db()
        enriched = []
        for r in results:
            event = database.get_event(r['id'])
            if event:
                event_dict = recalculate_status(event.to_dict())
                event_dict['ai_score'] = r['score']
                enriched.append(event_dict)
        
        print(f"AI Search: '{query}' -> {len(enriched)} results")
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

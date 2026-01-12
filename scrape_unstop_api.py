
"""
High-performance API scraper for Unstop.
Uses internal API: https://unstop.com/api/public/competition/{id}
No browser required.
"""
import requests
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')
from database.db_manager import DatabaseManager
from scrape_all import extract_tags_from_text

# Headers to mimic browser (optional but good practice)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://unstop.com/hackathons"
}

def clean_html(raw_html):
    """Simple cleaner to remove HTML tags for description storage."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', raw_html)
    return re.sub(r'\s+', ' ', cleantext).strip()

def fetch_details(event_id, event_url):
    """
    Fetch details for a single event ID from Unstop API.
    Returns parsed dict or None.
    """
    try:
        api_url = f"https://unstop.com/api/public/competition/{event_id}?round_lang=1"
        r = requests.get(api_url, headers=HEADERS, timeout=10)
        
        if r.status_code != 200:
            return None
        
        data = r.json()
        comp = data.get('data', {}).get('competition', {})
        if not comp:
             return None
             
        # Extract fields
        reg_req = comp.get('regnRequirements', {})
        
        # Deadlines
        reg_end_iso = reg_req.get('end_regn_dt') # "2025-11-30T23:59:00+05:30"
        reg_start_iso = reg_req.get('start_regn_dt')
        
        # Parse Dates
        end_date = None
        if reg_end_iso:
            try:
                # Keep ISO format or simplify to YYYY-MM-DD
                # DB expects YYYY-MM-DD usually for simplified checks, but we can store ISO string if column supports it.
                # Let's strip time for consistency with other scrapers usually returning YYYY-MM-DD
                end_date = reg_end_iso.split('T')[0]
            except: pass
            
        # Description
        raw_desc = comp.get('details', '')
        description = clean_html(raw_desc)[:3000] # Limit size
        
        return {
            'end_date': end_date,
            'description': description,
            'reg_start': reg_start_iso
        }
        
    except Exception as e:
        # print(f"Error {event_id}: {e}")
        return None

def extract_id_from_url(url):
    # https://unstop.com/hackathons/name-12345
    # or just 12345
    parts = url.strip('/').split('-')
    if parts[-1].isdigit():
        return parts[-1]
    return None

def main():
    db = DatabaseManager('hackathons.db')
    print("Querying Unstop events...")
    events, total = db.query_events(sources=['Unstop'], page_size=10000)
    
    print(f"Found {len(events)} events. Starting API fetch...")
    
    to_process = []
    for e in events:
        if e.url:
            eid = extract_id_from_url(e.url)
            if eid:
                to_process.append({'db_event': e, 'api_id': eid})
                
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_map = {executor.submit(fetch_details, item['api_id'], item['db_event'].url): item for item in to_process}
        
        for future in as_completed(future_map):
            item = future_map[future]
            try:
                res = future.result()
                if res:
                    # Update DB Object
                    e = item['db_event']
                    updated = False
                    
                    if res['description'] and len(res['description']) > 50:
                        e.description = res['description']
                        e.tags = extract_tags_from_text(res['description'])
                        updated = True
                        
                    if res['end_date']:
                        e.end_date = res['end_date'] # Override with Reg Deadline
                        updated = True
                    
                    if updated:
                        db.save_event(e)
                        success_count += 1
                        print(f"  ✓ {e.title[:20]}... (Date: {res['end_date']})")
                    else:
                        fail_count += 1
                else:
                    print(f"  ❌ No Data for {item['api_id']}")
                    fail_count += 1
            except Exception as e:
                print(f"  Example Error: {e}")
                fail_count += 1

    print("="*40)
    print(f"API Scrape Complete.")
    print(f"Updated: {success_count}")
    print(f"Failed/NoData: {fail_count}")

if __name__ == "__main__":
    main()

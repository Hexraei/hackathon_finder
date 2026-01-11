"""
Multi-Site Hackathon Scraper - Consolidated
===========================================
Single entry point for all hackathon scraping logic.
Combines API-based scraping (fast) and Browser-based scraping (robust).
"""
import sys
import re
import json
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

# Add local path
sys.path.insert(0, '.')

from database.db_manager import DatabaseManager
from utils.data_normalizer import DataNormalizer

# Initialize global objects
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0', 
    'Accept': 'application/json, text/html, */*'
}
db = DatabaseManager('hackathons.db')
normalizer = DataNormalizer()

# ==========================================
# Helpers
# ==========================================

def parse_epoch(timestamp):
    """Convert epoch timestamp to ISO date string."""
    if not timestamp: return None
    try:
        ts = int(timestamp)
        if ts > 9999999999: ts = ts / 1000
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    except: return None

def parse_iso_timestamp(ts):
    """Parse ISO timestamp to date string."""
    if not ts: return None
    try:
        if isinstance(ts, str): return ts[:10] if len(ts) >= 10 else None
        return None
    except: return None

def safe_get(url, timeout=30):
    try: return requests.get(url, headers=headers, timeout=timeout)
    except: return None

def _extract_jsonld_events(data, base_url):
    """Extract events from JSON-LD data."""
    items = []
    if isinstance(data, list): items = data
    elif isinstance(data, dict):
        items = data.get('@graph', [data])

    events = []
    for item in items:
        if not isinstance(item, dict): continue
        
        # Check type
        etype = item.get('@type')
        is_event = False
        if isinstance(etype, list): is_event = any(str(t).lower() == 'event' for t in etype)
        else: is_event = str(etype).lower() == 'event'
        if not is_event: continue

        title = item.get('name') or item.get('title')
        url = item.get('url') or item.get('@id')
        if url and isinstance(url, str) and url.startswith('/'):
            url = urljoin(base_url, url)

        start = item.get('startDate') or item.get('start_date')
        end = item.get('endDate') or item.get('end_date')
        
        # Location parsing
        loc_val = item.get('location')
        location = ''
        if isinstance(loc_val, dict):
            location = loc_val.get('name') or ''
        elif isinstance(loc_val, str):
            location = loc_val

        if title and url:
            events.append({
                'title': title, 'url': url, 'start_date': start, 'end_date': end, 
                'location': location, 'image': item.get('image')
            })
    return events

# ==========================================
# API Scrapers
# ==========================================

def scrape_devpost():
    print('\n📦 Devpost...')
    saved = 0
    # Regex patterns
    pat_full = re.compile(r'([A-Za-z]{3}\s+\d{1,2},\s+\d{4})')
    pat_same_month = re.compile(r'([A-Za-z]{3})\s+(\d{1,2})\s*-\s*(\d{1,2}),\s+(\d{4})')
    pat_diff_month = re.compile(r'([A-Za-z]{3})\s+(\d{1,2})\s*-\s*([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})')
    
    for page in range(1, 6):
        try:
            r = safe_get(f'https://devpost.com/api/hackathons?page={page}&per_page=50')
            if not r: break
            for h in r.json().get('hackathons', []):
                try:
                    dates = h.get('submission_period_dates', {})
                    start_date = None
                    end_date = None
                    
                    if isinstance(dates, dict):
                        start_date = parse_iso_timestamp(dates.get('starts_at'))
                        end_date = parse_iso_timestamp(dates.get('ends_at'))
                    elif isinstance(dates, str) and dates:
                        dates = dates.replace(u'\xa0', u' ').strip()
                        # Try Same Month
                        m2 = pat_same_month.search(dates)
                        if m2:
                            mon, d1, d2, y = m2.groups()
                            start_date = datetime.strptime(f"{mon} {d1}, {y}", '%b %d, %Y').strftime('%Y-%m-%d')
                            end_date = datetime.strptime(f"{mon} {d2}, {y}", '%b %d, %Y').strftime('%Y-%m-%d')
                        # Try Diff Month
                        if not start_date:
                            m3 = pat_diff_month.search(dates)
                            if m3:
                                mon1, d1, mon2, d2, y = m3.groups()
                                start_date = datetime.strptime(f"{mon1} {d1}, {y}", '%b %d, %Y').strftime('%Y-%m-%d')
                                end_date = datetime.strptime(f"{mon2} {d2}, {y}", '%b %d, %Y').strftime('%Y-%m-%d')
                        # Try Full
                        if not start_date:
                            matches = pat_full.findall(dates)
                            if matches:
                                try:
                                    start_date = datetime.strptime(matches[0], '%b %d, %Y').strftime('%Y-%m-%d')
                                    if len(matches) > 1:
                                        end_date = datetime.strptime(matches[1], '%b %d, %Y').strftime('%Y-%m-%d')
                                except: pass
                    
                    raw = {
                        'title': h.get('title'),
                        'url': h.get('url'),
                        'start_date': start_date,
                        'end_date': end_date,
                        'location': 'Online' if h.get('online_only') else h.get('displayed_location', ''),
                        'prize': h.get('prize_amount'),
                        'mode': 'online' if h.get('online_only') else 'in-person'
                    }
                    if raw['title']: db.save_event(normalizer.normalize(raw, 'Devpost')); saved += 1
                except: pass
        except: break
    print(f'  ✓ {saved}')
    return saved

def scrape_devfolio():
    print('\n🎯 Devfolio...')
    saved = 0
    try:
        for list_type in ['application_open', 'all']:
            r = requests.post('https://api.devfolio.co/api/search/hackathons', 
                             json={"type": list_type, "from": 0, "size": 100}, 
                             headers=headers, timeout=30)
            for h in r.json().get('hits', {}).get('hits', []):
                try:
                    src = h.get('_source', {})
                    s_at, e_at = src.get('starts_at'), src.get('ends_at')
                    
                    start_date = parse_epoch(s_at)
                    if not start_date and isinstance(s_at, str): start_date = parse_iso_timestamp(s_at)
                    end_date = parse_epoch(e_at)
                    if not end_date and isinstance(e_at, str): end_date = parse_iso_timestamp(e_at)
                    
                    raw = {
                        'title': src.get('name'),
                        'url': f"https://devfolio.co/{src.get('slug')}" if src.get('slug') else None,
                        'start_date': start_date, 'end_date': end_date,
                        'location': src.get('location') or ('Online' if src.get('is_online_event') else ''),
                        'prize': src.get('prize_amount'),
                        'mode': 'online' if src.get('is_online_event') else 'in-person'
                    }
                    if raw['title'] and raw['url']: db.save_event(normalizer.normalize(raw, 'Devfolio')); saved += 1
                except: pass
    except: pass
    print(f'  ✓ {saved}')
    return saved

def scrape_hackculture():
    print('\nHackCulture...')
    saved = 0
    try:
        r = safe_get('https://hackculture.io/')
        if r:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            events = []
            for script in soup.find_all('script', type='application/ld+json'):
                try: events.extend(_extract_jsonld_events(json.loads(script.string), 'https://hackculture.io/'))
                except: pass
            
            # Fallback
            if not events:
                for card in soup.select('.event-card, .hackathon-card'):
                    link = card.select_one('a[href]')
                    if link:
                        events.append({'title': link.get_text(strip=True), 'url': urljoin('https://hackculture.io/', link['href'])})
            
            for raw in events:
                if raw.get('title'): db.save_event(normalizer.normalize(raw, 'HackCulture')); saved += 1
    except: pass
    print(f'  ✓ {saved}')
    return saved

def scrape_unstop():
    print('\n🎪 Unstop...')
    saved = 0
    try:
        for page in range(1, 5):
            r = safe_get(f'https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&per_page=100&page={page}')
            if not r: break
            data = r.json().get('data', {}).get('data', [])
            if not data: break
            for h in data:
                try:
                    start = parse_iso_timestamp(h.get('start_date') or h.get('regnStartDate'))
                    end = parse_iso_timestamp(h.get('end_date') or h.get('regnEndDate'))
                    raw = {'title': h.get('title'), 'url': f"https://unstop.com/{h.get('public_url')}",
                           'start_date': start, 'end_date': end, 'location': h.get('city') or 'Online',
                           'mode': 'in-person' if h.get('city') else 'online'}
                    db.save_event(normalizer.normalize(raw, 'Unstop')); saved += 1
                except: pass
    except: pass
    print(f'  ✓ {saved}')
    return saved

def scrape_mlh():
    print('\n🏆 MLH...')
    saved = 0
    try:
        from bs4 import BeautifulSoup
        for year in ['2025', '2026']:
            r = safe_get(f'https://mlh.io/seasons/{year}/events')
            if r:
                soup = BeautifulSoup(r.text, 'html.parser')
                for link in soup.find_all('a', href=True):
                    if '/events/' not in link['href']: continue
                    try:
                        text = link.get_text(strip=True)
                        # Extract date: "Event NameJAN 09"
                        m = re.search(r'([A-Z]{3})\s*(\d{1,2})', text)
                        start = None
                        name = text
                        if m:
                            name = text.split(m.group(0))[0].strip()
                        raw = {'title': name, 'url': link['href'], 'mode': 'in-person'}
                        if not raw['url'].startswith('http'): raw['url'] = 'https://mlh.io' + raw['url']
                        db.save_event(normalizer.normalize(raw, 'MLH')); saved += 1
                    except: pass
    except: pass
    print(f'  ✓ {saved}')
    return saved

def scrape_superteam():
    print('\n☀️ Superteam...')
    saved = 0
    try:
        r = safe_get('https://earn.superteam.fun/api/listings/?type=hackathon')
        if r:
            for h in r.json()[:50]:
                raw = {'title': h.get('title'), 'url': h.get('link'), 'prize': h.get('rewardAmount'), 'mode': 'online'}
                db.save_event(normalizer.normalize(raw, 'Superteam')); saved += 1
    except: pass
    print(f'  ✓ {saved}')
    return saved

def scrape_kaggle():
    print('\n📊 Kaggle...')
    saved = 0
    try:
        r = safe_get('https://www.kaggle.com/competitions.json')
        if r:
            for h in r.json()[:50]:
                raw = {'title': h.get('competitionTitle'), 'url': f"https://www.kaggle.com/competitions/{h.get('competitionSlug')}",
                       'prize': h.get('reward'), 'mode': 'online'}
                db.save_event(normalizer.normalize(raw, 'Kaggle')); saved += 1
    except: pass
    print(f'  ✓ {saved}')
    return saved

def scrape_contra():
    print('\n🎨 Contra...')
    saved = 0
    try:
        r = safe_get('https://contra.com/api/hackathons')
        if r:
            for h in r.json()[:30]:
                raw = {'title': h.get('title'), 'url': h.get('url'), 'mode': 'online'}
                db.save_event(normalizer.normalize(raw, 'Contra')); saved += 1
    except: pass
    print(f'  ✓ {saved}')
    return saved

# ==========================================
# Browser Scrapers (Consolidated)
# ==========================================

def scrape_dorahacks():
    print('\n🚀 DoraHacks (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            page = context.new_page()
            page.goto('https://dorahacks.io/hackathon', wait_until='domcontentloaded', timeout=60000)
            try: page.wait_for_selector('.hackathon-list', timeout=20000)
            except: pass
            for _ in range(3): page.evaluate('window.scrollTo(0, document.body.scrollHeight)'); page.wait_for_timeout(1000)
            html = page.content()
            browser.close()
        
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        for card in soup.select('a[href*="/hackathon/"]'):
            href = card.get('href', '')
            if not href or href in seen: continue
            seen.add(href)
            if not href.startswith('http'): href = 'https://dorahacks.io' + href
            
            title_el = card.select_one('.font-semibold.line-clamp-2')
            title = title_el.get_text(strip=True) if title_el else ""
            if len(title) > 3:
                raw = {'title': title, 'url': href, 'mode': 'online', 'tags': ['Web3']}
                db.save_event(normalizer.normalize(raw, 'DoraHacks')); saved += 1
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved

def scrape_techgig():
    print('\n💻 TechGig (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.techgig.com/challenge/', wait_until='networkidle', timeout=45000)
            for _ in range(3): page.evaluate('window.scrollTo(0, document.body.scrollHeight)'); page.wait_for_timeout(1000)
            html = page.content()
            browser.close()
        
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        for link in soup.select('a[href*="/challenge/"]'):
            href = link.get('href', '')
            if not href or href in seen: continue
            seen.add(href)
            if not href.startswith('http'): href = 'https://www.techgig.com' + href
            
            title = link.get_text(strip=True)
            if not title or len(title) < 5 or 'Participate' in title: continue
            
            end_date = None
            if 'Ends On' in str(link.parent): end_date = datetime.now().strftime('%Y-12-31') # Simplified
            
            raw = {'title': title, 'url': href, 'end_date': end_date, 'mode': 'online'}
            db.save_event(normalizer.normalize(raw, 'TechGig')); saved += 1
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved

def scrape_geeksforgeeks():
    print('\n📗 GeeksforGeeks (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.geeksforgeeks.org/events/', wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            cards = page.query_selector_all('a[href^="/event/"]')
            seen = set()
            for card in cards:
                href = card.get_attribute('href')
                if not href or href in seen: continue
                seen.add(href)
                if not href.startswith('http'): href = 'https://www.geeksforgeeks.org' + href
                
                title_el = card.query_selector('p[class*="eventCardTitle"]')
                title = title_el.inner_text().strip() if title_el else ""
                
                if title:
                    raw = {'title': title, 'url': href, 'mode': 'online', 'tags': ['Coding']}
                    db.save_event(normalizer.normalize(raw, 'GeeksforGeeks')); saved += 1
            browser.close()
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved

def scrape_hackerearth():
    print('\n🧠 HackerEarth (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            page = context.new_page()
            page.goto('https://www.hackerearth.com/challenges/', wait_until='networkidle', timeout=60000)
            for _ in range(5): page.evaluate('window.scrollTo(0, document.body.scrollHeight)'); page.wait_for_timeout(1000)
            html = page.content()
            browser.close()
            
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        for card in soup.select('a[href*="/challenges/"]'):
            href = card.get('href', '')
            if not href or href in seen: continue
            seen.add(href)
            
            text = card.get_text()
            if len(text) > 10 and 'Live' in text or 'Upcoming' in text:
                title = card.get_text(separator='|').split('|')[0]
                raw = {'title': title[:100], 'url': href, 'mode': 'online'}
                db.save_event(normalizer.normalize(raw, 'HackerEarth')); saved += 1
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved

def scrape_hackquest():
    print('\n🎮 HackQuest (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.hackquest.io/hackathons', wait_until='networkidle', timeout=60000)
            for _ in range(3): page.evaluate('window.scrollTo(0, document.body.scrollHeight)'); page.wait_for_timeout(1000)
            html = page.content()
            browser.close()
            
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        for card in soup.select('a[href^="/hackathons/"]'):
            href = card.get('href', '')
            if not href or href in seen: continue
            seen.add(href)
            if not href.startswith('http'): href = 'https://www.hackquest.io' + href
            
            title = ""
            h2 = card.find('h2')
            if h2: title = h2.get_text(strip=True)
            if title:
                raw = {'title': title, 'url': href, 'mode': 'online'}
                db.save_event(normalizer.normalize(raw, 'HackQuest')); saved += 1
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved

def scrape_devdisplay():
    print('\n🖥️ DevDisplay (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.devdisplay.org/hackathons', wait_until='networkidle', timeout=60000)
            html = page.content()
            browser.close()
            
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        for link in soup.find_all('a'):
            if 'apply now' not in link.get_text(strip=True).lower(): continue
            href = link.get('href')
            if not href or href in seen: continue
            seen.add(href)
            
            card = link.find_parent('div').find_parent('div')
            if card:
                title_el = card.find('h2')
                title = title_el.get_text(strip=True) if title_el else (card.get('id') or '').title()
                if title:
                    raw = {'title': title, 'url': href, 'mode': 'online', 'source': 'DevDisplay'}
                    db.save_event(normalizer.normalize(raw, 'DevDisplay')); saved += 1
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved

def scrape_mycareernet():
    print('\n💼 MyCareerNet (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://mycareernet.in/mycareernet/contests', wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()
            
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        for card in soup.select('.hackathonCard'):
            link = card.find('a', href=True)
            if not link: continue
            href = link['href']
            if not href or href in seen: continue
            seen.add(href)
            if href.startswith('/'): href = 'https://mycareernet.in' + href
            
            title = card.get_text().split('\n')[0][:100] # Simplification
            if title:
                raw = {'title': title, 'url': href, 'mode': 'online'}
                db.save_event(normalizer.normalize(raw, 'MyCareerNet')); saved += 1
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved

def main():
    print('='*50)
    print('  HackFind - CONSOLIDATED Scraper')
    print('='*50)
    
    scrapers = [
        scrape_devpost, scrape_devfolio, scrape_hackculture, scrape_unstop,
        scrape_mlh, scrape_superteam, scrape_kaggle, scrape_contra,
        scrape_dorahacks, scrape_techgig, scrape_geeksforgeeks, 
        scrape_hackerearth, scrape_hackquest, scrape_devdisplay, scrape_mycareernet
    ]
    
    total = 0
    for s in scrapers:
        try: total += s()
        except Exception as e: print(f"  Error running scraper: {e}")
        time.sleep(0.5)
        
    print('\n' + '='*50)
    print(f'  Total this run: {total}')
    print(f'  Database total: {db.get_statistics()["total_events"]} hackathons')
    print('='*50)

if __name__ == '__main__':
    main()

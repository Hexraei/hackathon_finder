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
                        'mode': 'online' if h.get('online_only') else 'in-person',
                        'participants_count': h.get('registrations_count'),
                        'team_size_max': h.get('team_size')
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
                        'mode': 'online' if src.get('is_online_event') else 'in-person',
                        'participants_count': src.get('participants_count'),
                        'team_size_max': src.get('team_size')
                    }
                    if raw['title'] and raw['url']: db.save_event(normalizer.normalize(raw, 'Devfolio')); saved += 1
                except: pass
    except: pass
    print(f'  ✓ {saved}')
    return saved





def scrape_hackculture():
    print('\n🏛️ HackCulture (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Visit /challenges directly
            page.goto('https://hackculture.io/challenges', wait_until='networkidle', timeout=60000)
            
            # Scroll to trigger lazy loading
            for _ in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
            
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract events from rendered HTML
        seen = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Look for challenge links
            if '/challenges/' in href and len(href) > 15:
                if href in seen: continue
                seen.add(href)
                
                # Ensure full URL
                if not href.startswith('http'): 
                    href = urljoin('https://hackculture.io', href)
                
                # Extract title from card text or alt text
                title = a.get_text(strip=True)
                if not title:
                    title = a.find('h3').get_text(strip=True) if a.find('h3') else a.get_text(strip=True)
            
            # Extract Text for parsing
            text = a.get_text(separator=' ', strip=True)
            
            # Extract Date (e.g. "Oct 1 - Oct 5") - HackQuest dates are often range without year on card
            # We will try to parse assuming current/next year context in normalizer if needed, or just leave as text if logic allows
            start_date = None
            # Regex for "Mon DD"
            date_match = re.search(r'([A-Za-z]{3}\s+\d{1,2})', text)
            if date_match:
                 # Minimal effort date parsing, often insufficient without year, but better than nothing?
                 # Actually, let's leave start_date None if no year, to avoid bad data.
                 # Unless we assume 2025?
                 pass

            # Extract Prize
            prize = "Prize TBD"
            prize_match = re.search(r'[₹$]\s?[\d,]+', text)
            if prize_match: prize = prize_match.group(0)

            if len(title) > 3:
                raw = {
                    'title': title, 
                    'url': href, 
                    'start_date': None, # Difficult to extract year from card
                    'mode': 'online',
                    'prize': prize,
                    'participants_count': None,
                    'team_size_max': None
                }
                db.save_event(normalizer.normalize(raw, 'HackCulture')); saved += 1
                    
    except Exception as e: print(f'  Error: {e}')
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
                    # Dates: try regnRequirements or top level
                    regn = h.get('regnRequirements', {})
                    start = h.get('start_date')
                    if not start: start = regn.get('start_regn_dt')
                    
                    end = h.get('end_date')
                    if not end: end = regn.get('end_regn_dt')
                    
                    start_date = parse_iso_timestamp(start)
                    end_date = parse_iso_timestamp(end)
                    
                    # Location
                    addr = h.get('address_with_country_logo', {})
                    city = addr.get('city')
                    state = addr.get('state')
                    location = "Online"
                    mode = "online"
                    
                    region = h.get('region')
                    if region == 'offline' or city:
                        mode = 'in-person'
                        loc_parts = [p for p in [city, state] if p]
                        location = ", ".join(loc_parts) if loc_parts else "In-Person"
                    
                    # Prize
                    prize = "Prize TBD"
                    prizes_list = h.get('prizes', [])
                    if prizes_list:
                        total_cash = 0
                        currency = "₹"
                        for p in prizes_list:
                            try:
                                total_cash += int(float(str(p.get('cash', 0))))
                                if p.get('currency') == 'fa-rupee': currency = "₹"
                                elif p.get('currency') == 'fa-dollar': currency = "$"
                            except: pass
                        if total_cash > 0:
                            prize = f"{currency}{total_cash:,}"
                    
                    raw = {
                        'title': h.get('title'), 
                        'url': f"https://unstop.com/{h.get('public_url')}",
                        'start_date': start_date, 
                        'end_date': end_date, 
                        'location': location,
                        'mode': mode,
                        'prize': prize,
                        'participants_count': h.get('registerCount'),
                        'team_size_max': h.get('opportunity_config', {}).get('show_team_size') if isinstance(h.get('opportunity_config'), dict) else None
                    }
                    db.save_event(normalizer.normalize(raw, 'Unstop')); saved += 1
                except Exception as e: 
                    # print(f"Unstop Error: {e}") 
                    pass
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
                raw = {'title': h.get('title'), 'url': h.get('link'), 'prize': h.get('rewardAmount'), 'mode': 'online',
                       'participants_count': h.get('_count', {}).get('Submission') if isinstance(h.get('_count'), dict) else None,
                       'team_size_max': h.get('team_size')}
                db.save_event(normalizer.normalize(raw, 'Superteam')); saved += 1
    except: pass
    print(f'  ✓ {saved}')
    return saved



# ==========================================
# Browser Scrapers (Consolidated)
# ==========================================




def scrape_dorahacks():
    print('\n🐶 DoraHacks (Browser - Anti-Bot)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        import random
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Use stealthy context options
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768},
                device_scale_factor=1,
            )
            page = context.new_page()
            
            # Go to home first
            try:
                page.goto('https://dorahacks.io/', wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(2000 + random.randint(100, 1000))
                
                # Look for "Hackathon" link
                # Typically in nav
                page.click('a[href="/hackathon"]')
                page.wait_for_load_state('networkidle', timeout=30000)
                
            except:
                # Fallback to direct navigation if click fails
                page.goto('https://dorahacks.io/hackathon', wait_until='domcontentloaded', timeout=40000)

            # Wait for content
            try: page.wait_for_selector('.hackathon-list, a[href*="/hackathon/"]', timeout=20000)
            except: pass
            
            # Scroll
            for _ in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                
            html = page.content()
            browser.close()
        
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        
        # Selectors might be generic or specific classes
        # DoraHacks cards are usually <a> links
        for card in soup.select('a[href*="/hackathon/"]'):
            href = card.get('href', '')
            if not href.startswith('http'): href = 'https://dorahacks.io' + href
            
            if href in seen: continue
            seen.add(href)
            
            # Extract title
            title_el = card.select_one('.font-semibold, h3, h4')
            if not title_el: title_el = card.find('div', class_=lambda c: c and 'title' in c.lower())
            
            title = title_el.get_text(strip=True) if title_el else ""
            if len(title) > 3:
                # Extract participants count from card text
                text = card.get_text(separator=' ', strip=True)
                participants = None
                p_match = re.search(r'(\d+)\s+Participants?', text, re.IGNORECASE)
                if p_match:
                    participants = int(p_match.group(1))
                
                raw = {
                    'title': title,
                    'url': href,
                    'mode': 'online', 
                    'tags': ['Web3'],
                    'participants_count': participants,
                    'team_size_max': None
                }
                db.save_event(normalizer.normalize(raw, 'DoraHacks')); saved += 1
                
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved







def scrape_techgig():
    print('\n💻 TechGig (Browser - Broad)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Try engage subdomain directly as it seemed to have links in debug
            page.goto('https://engage.techgig.com/hackathons', wait_until='networkidle', timeout=60000)
            
            # Scroll
            for _ in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                
            html = page.content()
            browser.close()
        
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        
        # Broadest possible search: All links with 'hackathon' or 'challenge'
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Strict-ish filtering to avoid garbage
            if 'void(0)' in href or len(href) < 10: continue
            if 'contact-us' in href or 'about-us' in href or 'login' in href: continue
             
            # accepted patterns
            is_valid = False
            if '/hackathon' in href or '/challenge' in href: is_valid = True
            
            if not is_valid: continue
            
            if href in seen: continue
            seen.add(href)
            
            if not href.startswith('http'): 
                if href.startswith('/'):
                    href = 'https://engage.techgig.com' + href
                else:
                    href = 'https://engage.techgig.com/' + href
            
            # Title extraction - try link text first
            title = link.get_text(strip=True)
            
            # If link text is empty/generic (e.g. "View"), try finding a title sibling/parent
            if not title or len(title) < 5 or title.lower() in ['view', 'participate', 'register']:
                # Inspect parent
                card = link.find_parent('div') 
                if card:
                    h_tag = card.find(['h2', 'h3', 'h4', 'h5'])
                    if h_tag: title = h_tag.get_text(strip=True)

            if not title: continue # Skip if no title found
            
            # Filter mega generic nav items
            if title.lower() in ['hackathons', 'challenges', 'view all', 'explore', 'browse']: continue
            
            if len(title) > 3:
                # Extract participants and text from card
                participants = None
                text = ""
                # Check parent card text
                card = link.find_parent('div')
                if card:
                    text = card.get_text(separator=' ', strip=True)
                    p_match = re.search(r'(\d+)\s+Registered', text, re.IGNORECASE)
                    if p_match: participants = int(p_match.group(1))

                # Extract dates
                start_date = None
                # Debug logging
                if saved < 2: print(f"  [TechGig Debug] Text: {text[:100]}...")
                date_match = re.search(r'([A-Za-z]{3}\s+\d{1,2},\s+\d{4})', text)
                if date_match:
                    try: 
                        from datetime import datetime
                        start_date = datetime.strptime(date_match.group(1), '%b %d, %Y').strftime('%Y-%m-%d')
                    except: pass
                
                # Extract prize
                prize = "Prize TBD"
                prize_match = re.search(r'[₹$]\s?[\d,]+', text)
                if prize_match: prize = prize_match.group(0)

                raw = {
                    'title': title,
                    'url': href, 
                    'start_date': start_date,
                    'mode': 'online',
                    'prize': prize,
                    'participants_count': participants, 
                    'team_size_max': None
                }
                db.save_event(normalizer.normalize(raw, 'TechGig')); saved += 1
                
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved






def scrape_geeksforgeeks():
    print('\n📗 GeeksforGeeks (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from datetime import datetime
        
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
                
                # Extract text for parsing
                text = card.inner_text().strip()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                title = ""
                start_date = None
                
                if lines:
                    title = max(lines, key=len)
                    
                    for line in lines:
                        if line == title: continue
                        clean_line = line.replace('|', '').strip()
                        # Try parsing "February 24, 2025" format
                        try:
                            # Try standard full date
                            dt = datetime.strptime(clean_line, '%B %d, %Y')
                            start_date = dt.strftime('%Y-%m-%d')
                            break
                        except: pass
                
                # Extract Prize
                prize = "Prize TBD"
                for line in lines:
                    if '₹' in line or '$' in line:
                        import re
                        pm = re.search(r'[₹$]\s?[\d,]+', line)
                        if pm: prize = pm.group(0); break

                if title:
                    raw = {
                        'title': title, 
                        'url': href,
                        'start_date': start_date,
                        'mode': 'online',
                        'prize': prize,
                        'participants_count': None,
                        'team_size_max': None
                    }
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
            # Use stealthy context options (restored)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768}
            )
            page = context.new_page()
            page.goto('https://www.hackerearth.com/challenges/', wait_until='networkidle', timeout=60000)
            
            # Scroll to load more
            for _ in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                
            html = page.content()
            browser.close()

            
        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        
        # Select challenge cards
        # Typically they have class 'challenge-card-modern' or similar
        # We'll use a broad selector for links to event pages
        for card in soup.select('a[href*="/challenges/"], .challenge-card-modern a'):
            href = card.get('href', '')
            if not href: continue
             
            # Clean href
            if not href.startswith('http'): href = 'https://www.hackerearth.com' + href
            
            # Filter
            if '/hackathon/' not in href and '/challenge/' not in href: continue
            if 'hackerearth.com/challenges/' in href and len(href) < 45: continue # likely just the list page
            
            if href in seen: continue
            seen.add(href)
            
            # Extract title
            title = ""
            # Try to find title in common containers within the link or parent
            # If the link itself is the title
            if len(card.get_text(strip=True)) > 5:
                title = card.get_text(strip=True)
            else:
                # Look in parent
                parent = card.find_parent(class_='challenge-card-modern')
                if parent:
                    t_el = parent.select_one('.challenge-list-title')
                    if t_el: title = t_el.get_text(strip=True)
            
            if not title: continue
            
            # Skip generic nav/header text
            if title.lower() in ['hackathons', 'challenges', 'view all', 'explore', 'browse', 'ongoing', 'upcoming']: continue

            # Extract participants
            participants = None
            parent = card.find_parent(class_='challenge-card-modern') or card.find_parent(class_='challenge-card')
            if parent:
                # Extract Text for parsing
                text = parent.get_text(separator=' ', strip=True)
                if saved < 2: print(f"  [HE Debug] Text: {text[:100]}...")
                # pattern: "2000 Registered" or "2000+ Registered"
                p_match = re.search(r'([\d,]+)\+?\s+Registered', text, re.IGNORECASE)
                if p_match:
                    p_str = p_match.group(1).replace(',', '')
                    participants = int(p_str)
            else:
                text = "" # Ensure text is defined even if no parent card is found

            if len(title) > 3:
                # Extract dates
                start_date = None
                date_match = re.search(r'(?:Starts on|STARTS ON)\s*:?\s*([A-Za-z]{3}\s+\d{1,2},\s+\d{2,4})', text, re.IGNORECASE)
                if date_match:
                    try:
                        from datetime import datetime
                        dt_str = date_match.group(1)
                        # Handle 2-digit year
                        if ',' in dt_str and len(dt_str.split(',')[-1].strip()) == 2:
                             dt_str = dt_str.rsplit(' ', 1)[0] + ' 20' + dt_str.split(',')[-1].strip()
                        start_date = datetime.strptime(dt_str, '%b %d, %Y').strftime('%Y-%m-%d')
                    except: pass

                # Extract prize
                prize = "Prize TBD"
                prize_match = re.search(r'[₹$]\s?[\d,]+', text)
                if prize_match: prize = prize_match.group(0)

                raw = {
                    'title': title, 
                    'url': href, 
                    'start_date': start_date,
                    'mode': 'online',
                    'prize': prize,
                    'participants_count': participants,
                    'team_size_max': None
                }
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
                raw = {'title': title, 'url': href, 'mode': 'online',
                       'participants_count': None, 'team_size_max': None}
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
                    raw = {'title': title, 'url': href, 'mode': 'online', 'source': 'DevDisplay',
                           'participants_count': None, 'team_size_max': None}
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
                raw = {'title': title, 'url': href, 'mode': 'online',
                       'participants_count': None, 'team_size_max': None}
                db.save_event(normalizer.normalize(raw, 'MyCareerNet')); saved += 1
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved


def scrape_kaggle():
    print('\n📊 Kaggle (Browser)...')
    saved = 0
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        import re
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.kaggle.com/competitions', wait_until='networkidle', timeout=60000)
            
            # Scroll to load more
            for _ in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                
            html = page.content()
            browser.close()
            

        soup = BeautifulSoup(html, 'html.parser')
        seen = set()
        print(f"  Debug: Soup has {len(soup.find_all('a'))} links")
        
        # Select competition links
        for link in soup.find_all('a', href=True):
            href = link['href']
            

            # Filter
            if '/competitions/' not in href and '/c/' not in href: 
                # print(f"  Skipped (pattern): {href}")
                continue
            # if href.count('/') < 2: continue # e.g. /competitions
            if 'about' in href or 'documentation' in href: continue
            
            # Debug match
            print(f"  Checking {href}")
             
            # Clean href
            if not href.startswith('http'): href = 'https://www.kaggle.com' + href
            
            if href in seen: continue
            seen.add(href)
            

            # Extract info from parent container
            # Traverse parents to find a substantial container (div/li)
            container = link.parent
            found = False
            for _ in range(3): # Go up 3 levels max
                if not container: break
                if container.name in ['div', 'li'] and len(container.get_text(strip=True)) > 50:
                    found = True
                    break
                container = container.parent
            
            if not found or not container:
                # print(f"  Debug: Link match {href} but no valid container found")
                continue
            
            # Start parsing text
            text = container.get_text(separator=' ', strip=True)
            
            # Extract Title
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                h = link.find(['div', 'h1', 'h2', 'span'], class_=True) 
                if h: title = h.get_text(strip=True)
                # If still no title, try container header
                if not title:
                     h = container.find(['h2', 'h3'], class_=not None) # simple check
                     if h: title = h.get_text(strip=True)
            
            if not title: 
                # print(f"  Debug: No title for {href}")
                continue
            
            # Debug successful match
            # print(f"  Debug Matches: {title[:20]}...")
            
            # Prize
            prize = "Prize TBD"
            prize_match = re.search(r'\$[\d,]+', text)
            if prize_match:
                prize = prize_match.group(0)
            
            # Teams
            participants = None
            tm_match = re.search(r'([\d,]+)\s+Teams?', text, re.IGNORECASE)
            if tm_match:
                p_str = tm_match.group(1).replace(',', '')
                participants = int(p_str)

            if len(title) > 3:


                raw = {
                    'title': title, 
                    'url': href, 
                    'mode': 'online',
                    'prize': prize,
                    'participants_count': participants,
                    'team_size_max': 5
                }
                db.save_event(normalizer.normalize(raw, 'Kaggle')); saved += 1
                
    except Exception as e: print(f'  Error: {e}')
    print(f'  ✓ {saved}')
    return saved


def main():
    print('='*50)
    print('  HackFind - CONSOLIDATED Scraper')
    print('='*50)
    
    scrapers = [
        scrape_devpost, scrape_devfolio, scrape_unstop,
        scrape_mlh, scrape_superteam,
        scrape_dorahacks, scrape_techgig, scrape_geeksforgeeks, 
        scrape_hackerearth, scrape_hackquest, scrape_devdisplay, scrape_mycareernet,
        scrape_kaggle
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

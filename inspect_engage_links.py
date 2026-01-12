
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def deep_inspect_engage():
    url = "https://engage.techgig.com/hackathons"
    print(f"Deep inspecting {url}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle', timeout=60000)
        
        for _ in range(3):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(1000)
            
        content = page.content()
        browser.close()
        
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a', href=True)
        print(f"Total links: {len(links)}")
        
        # Print ALL links to understand structure
        for l in links:
            print(f"LINK: {l['href']}")

if __name__ == "__main__":
    deep_inspect_engage()

import os
import re
import time
import hashlib
import random
import threading
from datetime import datetime
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup

# Configuration
OUTPUT_DIR = "website_archives"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
CRAWL_INTERVAL_HOURS = 12
MAX_FILENAME_LENGTH = 180
MAX_THREADS = 3
PLAYWRIGHT_TIMEOUT = 2 * 60 * 1000 #in ms


STEALTH_SCRIPTS = [
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
    "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]})",
    "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
    "window.navigator.chrome = {runtime: {}, app: {}};",
    "const originalQuery = window.navigator.permissions.query; "
    "window.navigator.permissions.query = (parameters) => "
    "(parameters.name === 'notifications' ? "
    "Promise.resolve({ state: Notification.permission }) : "
    "originalQuery(parameters));"
]


thread_local = threading.local()

def get_browser():
    
    if not hasattr(thread_local, "browser"):
        pw = sync_playwright().start()
        
        
        browser = pw.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        thread_local.browser = browser
    return thread_local.browser

def close_browser():

    if hasattr(thread_local, "browser"):
        thread_local.browser.close()
        del thread_local.browser

def create_stealth_context(browser):
    
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
        java_script_enabled=True,
        ignore_https_errors=True,
        
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
    )
    
    
    for script in STEALTH_SCRIPTS:
        context.add_init_script(script)
    
    return context

def human_like_interaction(page):
    
    try:
        
        viewport_size = page.viewport_size
        for _ in range(3):
            x = random.randint(0, viewport_size["width"])
            y = random.randint(0, viewport_size["height"])
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.2, 0.5))
        
        
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(200, 800)
            page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))
    except Exception:
        pass  

def generate_filename(url, is_pdf=False):
    
    parsed = urlparse(url)
    domain = re.sub(r"\W+", "_", parsed.netloc)
    path = parsed.path.strip("/")

   
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename_base = "index" if not path else path.split("/")[-1].split("?")[0]
    filename_base = re.sub(r"\W+", "_", filename_base)[:50]
    
    base_name = f"{domain}_{filename_base}_{url_hash}_{timestamp}"
    
    if len(base_name) > MAX_FILENAME_LENGTH:
        keep_chars = MAX_FILENAME_LENGTH - len(url_hash) - len(timestamp) - 3
        domain_part = domain[:keep_chars//2]
        name_part = filename_base[:keep_chars - len(domain_part)]
        base_name = f"{domain_part}_{name_part}_{url_hash}_{timestamp}"
    
    return f"{base_name}.pdf"

def save_pdf(content, url, is_pdf=False):
    
    filename = generate_filename(url, is_pdf)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath

def download_pdf(url):
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive"
            },
            timeout=30,
            stream=True
        )
        if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
            return save_pdf(response.content, url, is_pdf=True)
        else:
            print(f"Invalid PDF response for {url}: Status {response.status_code}")
    except Exception as e:
        print(f"PDF download failed for {url}: {str(e)}")
    return None

def html_to_pdf(url):
    try:
        browser = get_browser()
        context = create_stealth_context(browser)
        page = context.new_page()
        
        try:
            # Add human-like delays
            time.sleep(random.uniform(1.0, 3.0))
            
            # Navigate with realistic patterns
            page.goto(url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
            
            # Simulate human interaction
            human_like_interaction(page)
            
            # Wait for page to stabilize
            page.wait_for_timeout(random.randint(2000, 5000))
            
            if page.query_selector("div.recaptcha"):
                print("reCAPTCHA challenge detected. Skipping page.")
                return None
                
            pdf_content = page.pdf()
            return save_pdf(pdf_content, url)
        except Exception as e:
            print(f"PDF generation failed for {url}: {str(e)}")
            return None
        finally:
            context.close()
    except Exception as e:
        print(f"Browser error for {url}: {str(e)}")
        return None

def extract_links(url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    base_domain = urlparse(url).netloc
    links = set()

    for link in soup.find_all('a', href=True):
        href = link['href'].strip()
        if not href or href.startswith(('mailto:', 'tel:', 'javascript:')):
            continue

        absolute_url = urljoin(url, href)
        parsed = urlparse(absolute_url)
        
        clean_url = parsed._replace(fragment="", query="").geturl()
        
        if parsed.netloc == base_domain:
            if clean_url.endswith('.pdf'):
                links.add(clean_url)
            else:
                links.add(re.sub(r"/$", "", clean_url))

    return links

def process_url(url, visited, session, queue, lock):
    if url in visited:
        return
    
    with lock:
        visited.add(url)
    
    print(f"Processing: {url}")

    if url.endswith('.pdf'):
        download_pdf(url)
        return

    try:
        time.sleep(random.uniform(1.0, 5.0))
        
        response = session.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive"
            },
            timeout=30,
            allow_redirects=True
        )
        
        if response.status_code != 200:
            print(f"Skipping {url}: Status {response.status_code}")
            return

        content_type = response.headers.get('content-type', '')
        final_url = response.url

        if 'application/pdf' in content_type:
            download_pdf(final_url)
        elif 'text/html' in content_type:
            html_to_pdf(final_url)
            
            new_links = extract_links(final_url, response.content)
            
            # Add new links to queue
            with lock:
                for link in new_links:
                    if link not in visited:
                        queue.append(link)
        else:
            print(f"Skipping unsupported content at {url}: {content_type}")
                
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")

def crawl_website(start_url):
    visited = set()
    queue = [start_url]
    session = requests.Session()
    lock = threading.Lock()
    threads = []

    while queue:
        current_batch = []
        while queue and len(current_batch) < MAX_THREADS:
            url = queue.pop(0)
            current_batch.append(url)
        
        for url in current_batch:
            t = threading.Thread(
                target=process_url,
                args=(url, visited, session, queue, lock)
            )
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        threads.clear()
    
    close_browser()

def crawl_job():
    websites = [
        "https://www.fdic.gov/risk-management-manual-examination-policies",
        # "https://advance.lexis.com/documentpage/?pdmfid=1000516&crid=e93b03e5-5b2e-489f-bf81-2c2cd5b24234&nodeid=AADAACAAD&nodepath=%2FROOT%2FAAD%2FAADAAC%2FAADAACAAD&level=3&haschildren=&populated=false&title=3-1-3.+Use+of+existing+forms+and+filings+relating+to+licenses+or+taxes.&config=00JAA1MDBlYzczZi1lYjFlLTQxTgtYWE3OS02YTgyOGM2NWJlMDYKAFBvZENhdGFsb2feed0oM9qoQOMCSJFX5qkd&pddocfullpath=%2Fshared%2Fdocument%2Fstatutes-legislation%2Furn%3AcontentItem%3A6348-FRF1-DYB7-W0N0-00008-00&ecomp=6gf59kk&prid=b73dd455-a3cc-405f-89ba-3d5d1f3acde9"
    ]

    for url in websites:
        try:
            print(f"\nStarting crawl for: {url}")
            parsed = urlparse(url)
            clean_url = parsed._replace(query="").geturl()
            crawl_website(clean_url)
        except Exception as e:
            print(f"Critical error crawling {url}: {str(e)}")

def setup_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        crawl_job,
        'interval',
        hours=CRAWL_INTERVAL_HOURS,
        next_run_time=datetime.now()
    )
    scheduler.start()
    print(f"Scheduler started. Will run every {CRAWL_INTERVAL_HOURS} hours.")
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    crawl_job()
    
    # Start scheduled runs
    setup_scheduler()
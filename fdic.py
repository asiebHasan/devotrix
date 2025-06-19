import os
import re
import time
import json
import logging
import hashlib
import configparser
from datetime import datetime
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup

# Configuration
CONFIG_FILE = "crawler_config.ini"
OUTPUT_DIR = "website_archives"
LOG_DIR = "crawler_logs"
MAX_THREADS = 5
MAX_DEPTH = 5
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# Setup configuration
def setup_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        config['CRAWLER'] = {
            'output_dir': OUTPUT_DIR,
            'log_dir': LOG_DIR,
            'max_threads': str(MAX_THREADS),
            'max_depth': str(MAX_DEPTH),
            'rate_limit_delay': str(RATE_LIMIT_DELAY),
            'crawl_interval_hours': '12',
            'skip_keywords': 'logout,admin,signout,register,login',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    return config

config = setup_config()

# Create directories
os.makedirs(config['CRAWLER']['output_dir'], exist_ok=True)
os.makedirs(config['CRAWLER']['log_dir'], exist_ok=True)

# Setup logging
def setup_logger():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(config['CRAWLER']['log_dir'], f"crawler_{timestamp}.log")
    
    logger = logging.getLogger("WebCrawler")
    logger.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

class WebCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.visited = set()
        self.pdf_checksums = set()
        self.crawl_stats = {
            'pages_crawled': 0,
            'pdfs_found': 0,
            'pdfs_downloaded': 0,
            'errors': 0,
            'skipped': 0
        }
        self.session = requests.Session()
        self.skip_keywords = [kw.strip() for kw in config['CRAWLER']['skip_keywords'].split(',')]
    
    def should_skip(self, url):
        """Check if URL should be skipped based on keywords"""
        if any(kw in url.lower() for kw in self.skip_keywords):
            return True
        return False
    
    def generate_filename(self, url, is_pdf=False):
        """Generate safe filename with domain, path, and timestamp"""
        parsed = urlparse(url)
        path = parsed.path.strip('/').replace('/', '_') or 'index'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate hash for uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:6]
        
        # Remove special characters
        clean_path = re.sub(r'[^\w\-]', '_', path)[:100]
        filename = f"{self.base_domain}_{clean_path}_{url_hash}_{timestamp}.pdf"
        return os.path.join(config['CRAWLER']['output_dir'], filename)
    
    def save_pdf(self, content, url, is_pdf=False):
        """Save content to PDF file with deduplication"""
        # Check for duplicates
        content_hash = hashlib.md5(content).hexdigest()
        if content_hash in self.pdf_checksums:
            logger.info(f"Skipping duplicate content: {url}")
            self.crawl_stats['skipped'] += 1
            return None
        
        filename = self.generate_filename(url, is_pdf)
        try:
            with open(filename, "wb") as f:
                f.write(content)
            self.pdf_checksums.add(content_hash)
            return filename
        except Exception as e:
            logger.error(f"Failed to save PDF: {str(e)}")
            return None
    
    def download_pdf(self, url):
        """Download existing PDF files"""
        try:
            response = self.session.get(
                url,
                headers={"User-Agent": config['CRAWLER']['user_agent']},
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
                self.crawl_stats['pdfs_found'] += 1
                if self.save_pdf(response.content, url, is_pdf=True):
                    self.crawl_stats['pdfs_downloaded'] += 1
                    logger.info(f"Downloaded PDF: {url}")
                return True
        except Exception as e:
            logger.error(f"PDF download failed for {url}: {str(e)}")
            self.crawl_stats['errors'] += 1
        return False
    
    def html_to_pdf(self, url):
        """Convert HTML page to PDF using headless browser"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # Add delay for dynamic content
                page.wait_for_timeout(2000)
                
                pdf_content = page.pdf()
                browser.close()
                
                if self.save_pdf(pdf_content, url):
                    logger.info(f"Generated PDF: {url}")
                return True
        except Exception as e:
            logger.error(f"PDF generation failed for {url}: {str(e)}")
            self.crawl_stats['errors'] += 1
        return False
    
    def extract_links(self, url, html_content):
        """Extract all valid links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if not href or href.startswith(('mailto:', 'tel:', 'javascript:')):
                continue
            
            # Normalize URL
            absolute_url = urljoin(url, href)
            parsed = urlparse(absolute_url)
            
            # Remove fragments and query parameters
            clean_url = parsed._replace(fragment="", query="").geturl()
            
            # Filter by domain and skip keywords
            if (parsed.netloc == self.base_domain and 
                not self.should_skip(clean_url)):
                links.add(clean_url)
        
        return links
    
    def process_url(self, url, depth=0):
        """Process a single URL recursively"""
        if (url in self.visited or 
            depth > int(config['CRAWLER']['max_depth'])):
            return []
        
        self.visited.add(url)
        self.crawl_stats['pages_crawled'] += 1
        logger.info(f"Processing [{depth}]: {url}")
        
        # Rate limiting
        time.sleep(float(config['CRAWLER']['rate_limit_delay']))
        
        try:
            response = self.session.get(
                url,
                headers={"User-Agent": config['CRAWLER']['user_agent']},
                timeout=30,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                logger.warning(f"Skipped {url}: Status {response.status_code}")
                return []
            
            content_type = response.headers.get('content-type', '')
            final_url = response.url
            
            # Handle PDF files
            if 'application/pdf' in content_type or url.endswith('.pdf'):
                self.download_pdf(final_url)
                return []
            
            # Process HTML content
            elif 'text/html' in content_type:
                # Convert to PDF
                self.html_to_pdf(final_url)
                
                # Extract and return new links
                return self.extract_links(final_url, response.content)
        
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            self.crawl_stats['errors'] += 1
        
        return []
    
    def crawl(self):
        """Main crawl method with BFS implementation"""
        logger.info(f"Starting crawl for: {self.base_url}")
        queue = [(self.base_url, 0)]
        
        with ThreadPoolExecutor(max_workers=int(config['CRAWLER']['max_threads'])) as executor:
            while queue:
                futures = []
                current_level = queue.copy()
                queue = []
                
                for url, depth in current_level:
                    future = executor.submit(self.process_url, url, depth)
                    futures.append((future, depth))
                
                for future, depth in futures:
                    new_links = future.result()
                    for link in new_links:
                        if link not in self.visited:
                            queue.append((link, depth + 1))
        
        return self.crawl_stats

def generate_report(stats):
    """Generate JSON report of crawl statistics"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": timestamp,
        "crawl_stats": stats,
        "websites": list(stats.keys())
    }
    
    report_file = os.path.join(config['CRAWLER']['log_dir'], f"report_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_file

def crawl_job():
    """Main job to crawl both websites"""
    logger.info("Starting crawl job")
    start_time = time.time()
    crawl_stats = {}
    
    websites = [
        "https://www.fdic.gov/risk-management-manual-examination-policies",
        # Lexis URL (commented due to complexity)
        # "https://advance.lexis.com/documentpage/?pdmfid=1000516&crid=e93b03e5-5b2e-489f-bf81-2c2cd5b24234&nodeid=AADAACAAD&nodepath=%2FROOT%2FAAD%2FAADAAC%2FAADAACAAD&level=3&haschildren=&populated=false&title=3-1-3.+Use+of+existing+forms+and+filings+relating+to+licenses+or+taxes.&config=00JAA1MDBlYzczZi1lYjFlLTQxMTgtYWE3OS02YTgyOGM2NWJlMDYKAFBvZENhdGFsb2feed0oM9qoQOMCSJFX5qkd&pddocfullpath=%2Fshared%2Fdocument%2Fstatutes-legislation%2Furn%3AcontentItem%3A6348-FRF1-DYB7-W0N0-00008-00&ecomp=6gf59kk&prid=b73dd455-a3cc-405f-89ba-3d5d1f3acde9"
    ]
    
    for url in websites:
        try:
            crawler = WebCrawler(url)
            stats = crawler.crawl()
            crawl_stats[url] = stats
            logger.info(f"Completed crawl for: {url}")
            logger.info(f"Stats: {json.dumps(stats, indent=2)}")
        except Exception as e:
            logger.exception(f"Critical error crawling {url}: {str(e)}")
    
    # Generate report
    report_file = generate_report(crawl_stats)
    duration = time.time() - start_time
    logger.info(f"Crawl job completed in {duration:.2f} seconds")
    logger.info(f"Report generated: {report_file}")

def setup_scheduler():
    """Configure and start periodic scheduler"""
    scheduler = BackgroundScheduler()
    interval_hours = int(config['CRAWLER']['crawl_interval_hours'])
    
    scheduler.add_job(
        crawl_job,
        'interval',
        hours=interval_hours,
        next_run_time=datetime.now()
    )
    scheduler.start()
    logger.info(f"Scheduler started. Running every {interval_hours} hours.")
    
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down")

if __name__ == "__main__":
    logger.info("Crawler application started")
    
    # Initial run
    crawl_job()
    
    # Start scheduled runs
    setup_scheduler()
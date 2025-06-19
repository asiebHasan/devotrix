import requests
from bs4 import BeautifulSoup
import re
import os
import pdfkit
from time import sleep
from urllib.parse import unquote

class LexisNexisPDFScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://advance.lexis.com"
        
        self.wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        self.config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': f'{self.base_url}/',
        }
        
        self.cookies = {
            'LNPAGEHISTORY': '58d359a8-795a-4c70-8a67-2ea340211169%2C079a80c3-ab41-47e9-8f2c-7f7d34bf84a7%2C22d1dd34-01fd-4b8a-a2d2-5c938719bdd7%2Ca6384de4-da0c-47b9-8809-ad64a623dbf5%2Cc1e499f3-8125-4bd6-a3d8-dc4b6a275b67',
            'ASP.NET_SessionId': '386811cd-a1b4-4276-bf50-4c585b688b30',
            'LexisMachineId': 'c81abd5b-7860-4f8e-8ed2-847eb100fc05',
            'X-LN-InitialSignOn': '',
            '.AspNet.Wam': 'c5c1ae5a-9f52-4881-9140-a93257b6ae4c%3Ala',
            'lna2': 'OGJlNTAyYjZmOGFjNGU2OWFlMDhlMmY0YmEyNzgyOWNiODFiYjU2YjhiMjAwMjE3MTkyYmM0MDk1NjA4YWI1NzY4NTQwZjRkdXJuOnVzZXI6UEExODYxODQ3NDQhMTAwMDIwMiwxNTM5MTA5LCFub25l',
            'X-LN-Session-TTL': '2025-06-19T18%3A23%3A25Z%2C2025-06-19T15%3A23%3A25Z',
            'Perf': '%7B%22name%22%3A%22document_uscontents-handler_minitocbrowse_click%22%2C%22sit%22%3A%221750339417240%22%7D',

        }
        
        self.pdf_options = {
            'quiet': '',
            'page-size': 'Letter',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None 
        }
        
        self.session.headers.update(self.headers)
        self.session.cookies.update(self.cookies)

    def clean_filename(self, filename):
        return re.sub(r'[<>:"/\\|?*]', '_', filename)

    def get_page_html(self, params):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.base_url}/documentpage/",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                if len(response.text) < 1000:
                    raise ValueError("Page content too short")
                    
                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed after {max_retries} attempts: {e}")
                    return None
                sleep(2 ** attempt)  

    def save_as_pdf(self, html, filename):
        try:
            os.makedirs('pdfs', exist_ok=True)
            pdf_path = os.path.join('pdfs', self.clean_filename(filename))
            
            try:
                pdfkit.from_string(
                    html,
                    pdf_path,
                    options=self.pdf_options,
                    configuration=self.config
                )
            except Exception as e:
                print(f"PDF generation warning: {e}. Trying simplified options...")
                pdfkit.from_string(
                    html,
                    pdf_path,
                    options={'quiet': ''},
                    configuration=self.config
                )
            
            print(f"Successfully saved: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"Failed to save PDF: {e}")
            return None

    def find_next_page(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        
        next_link = soup.find('a', {'data-func': re.compile(r'get(Next|Prev)Doc')})
        if next_link:
            params = self._parse_js_onclick(next_link.get('onclick', ''))
            if params:
                return params
                
        for nav_class in ['tocdocnext', 'tocdocprev', 'tocnav']:
            nav_link = soup.find('a', class_=nav_class)
            if nav_link:
                params = self._parse_js_onclick(nav_link.get('onclick', ''))
                if params:
                    return params
                    
        script_data = soup.find('script', string=re.compile('page\.model'))
        if script_data:
            pass
            
        print("No navigable next page found")
        return None

    def scrape_and_crawl(self, start_params, max_pages=10):
        current_params = start_params
        scraped_pages = 0
        failed_pages = 0
        
        while current_params and scraped_pages < max_pages:
            print(f"\nPage {scraped_pages + 1}/{max_pages}")
            
            html = self.get_page_html(current_params)
            if not html:
                failed_pages += 1
                if failed_pages > 2:
                    print("Too many consecutive failures, aborting")
                    break
                continue
            
            failed_pages = 0
            
            section_name = unquote(current_params.get('pddocfullpath', '')).split('/')[-1]
            pdf_filename = f"{scraped_pages + 1:03d}_{section_name[:50]}.pdf"
            
            if not self.save_as_pdf(html, pdf_filename):
                continue
                
            current_params = self.find_next_page(html)
            scraped_pages += 1
            sleep(1.5)
            
        print(f"\nCompleted: {scraped_pages} pages scraped")

if __name__ == "__main__":
    scraper = LexisNexisPDFScraper()
    
    start_params = {
    }
    
    scraper.scrape_and_crawl(start_params, max_pages=20)
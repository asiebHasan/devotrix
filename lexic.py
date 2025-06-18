import requests
from bs4 import BeautifulSoup
import pdfkit

# Configuration for pdfkit (adjust path if necessary)
# path_to_wkhtmltopdf = '\pdf'
# config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

cookies = {
    'LNPAGEHISTORY': '9510ff5e-cd98-4d96-9605-363a5dad7a79%2Ca24b41a3-acdf-4938-a4eb-7f725a77375a%2Ca8088e99-6dc3-41a1-8947-bba4b6488541%2Ca199abee-97ad-4456-be37-7a25476e7502%2C3546a013-ca0c-462b-84f0-200278bb403f%2C1b9e9759-f7dd-4681-94cc-f51515129eab',
    'ASP.NET_SessionId': '7e374021-d317-4154-a0e3-11cda45432ae',
    'LexisMachineId': 'd46ba0c3-7ce2-4e0d-8af7-e616864cd90f',
    '.AspNet.Wam': '04f91194-a6f1-41af-ba62-a296743bd078%3Ala',
    'lna2': 'ZjVhMzNkY2MxZTVlNDBlZDVkNTc0YzY5NjMwMDFhNmJjNjA0YWI5YjBhMjI2ODNlZjNiOGQ3YzA3ODgxMTI5MDY4NTJmYTJidXJuOnVzZXI6UEExODY2NzIxNTchMTAwMDIwMiwxNTM5MTA5LCFub25l',
    'X-LN-Session-TTL': '2025-06-18T22%3A40%3A58Z%2C2025-06-18T19%3A40%3A58Z',
    'Perf': '%7B%22name%22%3A%22document_uscontents-handler_minitocbrowse_click%22%2C%22sit%22%3A%221750268470581%22%7D',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=0, i',
    'referer': 'https://advance.lexis.com/documentpage/?pdmfid=1000516&crid=a8088e99-6dc3-41a1-8947-bba4b6488541&pdistocdocslideraccess=true&config=00JAA1MDBlYzczZi1lYjFlLTQxMTgtYWE3OS02YTgyOGM2NWJlMDYKAFBvZENhdGFsb2feed0oM9qoQOMCSJFX5qkd&pddocfullpath=%2Fshared%2Fdocument%2Fstatutes-legislation%2Furn%3AcontentItem%3A6348-FRF1-DYB7-W0N5-00008-00&pdcomponentid=234187&pdtocnodeidentifier=AADAADAABAAB&ecomp=h2vckkk&prid=a24b41a3-acdf-4938-a4eb-7f725a77375a',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
}

params = {
    'pdmfid': '1000516',
    'crid': 'a199abee-97ad-4456-be37-7a25476e7502',
    'pdistocdocslideraccess': 'true',
    'config': '00JAA1MDBlYzczZi1lYjFlLTQxMTgtYWE3OS02YTgyOGM2NWJlMDYKAFBvZENhdGFsb2feed0oM9qoQOMCSJFX5qkd',
    'pddocfullpath': '/shared/document/statutes-legislation/urn:contentItem:6348-FRF1-DYB7-W0N2-00008-00',
    'pdcomponentid': '234187',
    'pdtocnodeidentifier': 'AADAACAAF',
    'ecomp': 'h2vckkk',
    'prid': 'a8088e99-6dc3-41a1-8947-bba4b6488541',
}

try:
    # Fetch the page
    response = requests.get(
        'https://advance.lexis.com/documentpage/',
        params=params,
        cookies=cookies,
        headers=headers
    )
    response.raise_for_status()  # Raise error for bad status

    # Generate PDF
    pdfkit.from_string(response.text, 'lexis_document.pdf')
    print("PDF generated successfully: 'lexis_document.pdf'")

    # Parse HTML to find next page link
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Locate the navigation container
    nav_container = soup.find('ul', class_='pagination')
    if not nav_container:
        raise ValueError("Pagination container not found")

    # Find active page element
    active_page = nav_container.find('li', class_='active')
    if not active_page:
        raise ValueError("Active page not found")

    # Get the next sibling (next page)
    next_page_li = active_page.find_next_sibling('li')
    if not next_page_li:
        print("No next page found")
    else:
        next_page_link = next_page_li.find('a')
        if next_page_link and 'href' in next_page_link.attrs:
            next_page_url = next_page_link['href']
            print(f"Next page URL: {next_page_url}")
        else:
            print("Next page link not found")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
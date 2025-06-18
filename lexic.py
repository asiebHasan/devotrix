import requests
from bs4 import BeautifulSoup
import pdfkit
import re

path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

cookies = {
    'LNPAGEHISTORY': '6df83e2a-e503-4419-9f2a-311210758fa5',
    'LexisMachineId': 'f6e88642-6dee-4358-8eca-06830a87332e',
    'ASP.NET_SessionId': '817485a7-fe90-49c0-a026-154b0bad54d5',
    'LNPAGELOAD-e93b03e5-5b2e-489f-bf81-2c2cd5b24234': '',
    'X-LN-InitialSignOn': '',
    '.AspNet.Wam': '578e1fd6-6a09-4dbf-9eb0-ae36cf62177f%3Ala',
    'lna2': 'MGFiM2Q4OTg3ZmQyNGM5NzAxMzY4MjAzMDI1MGYwNjZmZTlkZTNjODZlYTIyZjk2ODdkMmQ3NTNlMmI5NmRmNzY4NTMwY2VkdXJuOnVzZXI6UEExODY2NzE3MzIhMTAwMDIwMiwxNTM5MTA5LCFub25l',
    'X-LN-Session-TTL': '2025-06-19T00%3A01%3A00Z%2C2025-06-18T21%3A01%3A00Z',
    'Perf': '%7B%22name%22%3A%22document_uscontents-handler_minitocbrowse_click%22%2C%22sit%22%3A%221750273295270%22%7D',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'priority': 'u=0, i',
    'referer': 'https://advance.lexis.com/documentpage/?pdmfid=1000516&crid=6df83e2a-e503-4419-9f2a-311210758fa5&nodeid=AADAACAAD&nodepath=%2fROOT%2fAAD%2fAADAAC%2fAADAACAAD&level=3&haschildren=&populated=false&title=3-1-3.+Use+of+existing+forms+and+filings+relating+to+licenses+or+taxes.&config=00JAA1MDBlYzczZi1lYjFlLTQxMTgtYWE3OS02YTgyOGM2NWJlMDYKAFBvZENhdGFsb2feed0oM9qoQOMCSJFX5qkd&pddocfullpath=%2fshared%2fdocument%2fstatutes-legislation%2furn%3acontentItem%3a6348-FRF1-DYB7-W0N0-00008-00&ecomp=6gf59kk&prid=e93b03e5-5b2e-489f-bf81-2c2cd5b24234',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    # 'cookie': 'LNPAGEHISTORY=6df83e2a-e503-4419-9f2a-311210758fa5; LexisMachineId=f6e88642-6dee-4358-8eca-06830a87332e; ASP.NET_SessionId=817485a7-fe90-49c0-a026-154b0bad54d5; LNPAGELOAD-e93b03e5-5b2e-489f-bf81-2c2cd5b24234=; X-LN-InitialSignOn=; .AspNet.Wam=578e1fd6-6a09-4dbf-9eb0-ae36cf62177f%3Ala; lna2=MGFiM2Q4OTg3ZmQyNGM5NzAxMzY4MjAzMDI1MGYwNjZmZTlkZTNjODZlYTIyZjk2ODdkMmQ3NTNlMmI5NmRmNzY4NTMwY2VkdXJuOnVzZXI6UEExODY2NzE3MzIhMTAwMDIwMiwxNTM5MTA5LCFub25l; X-LN-Session-TTL=2025-06-19T00%3A01%3A00Z%2C2025-06-18T21%3A01%3A00Z; Perf=%7B%22name%22%3A%22document_uscontents-handler_minitocbrowse_click%22%2C%22sit%22%3A%221750273295270%22%7D',
}

params = {
    'pdmfid': '1000516',
    'crid': '2709efe8-810c-4d31-9aac-9550e8c32906',
    'pdistocdocslideraccess': 'true',
    'config': '00JAA1MDBlYzczZi1lYjFlLTQxMTgtYWE3OS02YTgyOGM2NWJlMDYKAFBvZENhdGFsb2feed0oM9qoQOMCSJFX5qkd',
    'pddocfullpath': '/shared/document/statutes-legislation/urn:contentItem:6348-FRF1-DYB7-W0N1-00008-00',
    'pdcomponentid': '234187',
    'pdtocnodeidentifier': 'AADAACAAE',
    'ecomp': 'h2vckkk',
    'prid': '6df83e2a-e503-4419-9f2a-311210758fa5',
}

response = requests.get('https://advance.lexis.com/documentpage/', params=params, cookies=cookies, headers=headers)

soup = BeautifulSoup(response.text, 'html.parser')

pdfkit.from_string(response.text, 'lexis_document.pdf', configuration=config)
print("PDF generated successfully: 'lexis_document.pdf'")

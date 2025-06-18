import requests
import pdfkit

import requests

cookies = {
    'LNPAGEHISTORY': '6dc39607-53ef-4ff2-b765-420019ec981d%2C6dc39607-53ef-4ff2-b765-420019ec981d%2Ce949358e-13e6-4adb-91e7-0fb5af165d29%2C9510ff5e-cd98-4d96-9605-363a5dad7a79%2Ca24b41a3-acdf-4938-a4eb-7f725a77375a%2Ca8088e99-6dc3-41a1-8947-bba4b6488541',
    'ASP.NET_SessionId': '7e374021-d317-4154-a0e3-11cda45432ae',
    'LexisMachineId': 'd46ba0c3-7ce2-4e0d-8af7-e616864cd90f',
    '.AspNet.Wam': '04f91194-a6f1-41af-ba62-a296743bd078%3Ala',
    'lna2': 'YTYxZDZjZjlkM2UyZGNiYWMzMzhlMzUwZDg4OTU0MTMyYjZmYWMzMDNkMzc0MTIzMzBkZWU4OThjMGM0NWI2ODY4NTJlYTY1dXJuOnVzZXI6UEExODY2NzIxNTchMTAwMDIwMiwxNTM5MTA5LCFub25l',
    'X-LN-Session-TTL': '2025-06-18T21%3A33%3A41Z%2C2025-06-18T18%3A33%3A41Z',
    'Perf': '%7B%22name%22%3A%22document_uscontents-handler_minitocbrowse_click%22%2C%22sit%22%3A%221750264431955%22%7D',
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
    # 'cookie': 'LNPAGEHISTORY=6dc39607-53ef-4ff2-b765-420019ec981d%2C6dc39607-53ef-4ff2-b765-420019ec981d%2Ce949358e-13e6-4adb-91e7-0fb5af165d29%2C9510ff5e-cd98-4d96-9605-363a5dad7a79%2Ca24b41a3-acdf-4938-a4eb-7f725a77375a%2Ca8088e99-6dc3-41a1-8947-bba4b6488541; ASP.NET_SessionId=7e374021-d317-4154-a0e3-11cda45432ae; LexisMachineId=d46ba0c3-7ce2-4e0d-8af7-e616864cd90f; .AspNet.Wam=04f91194-a6f1-41af-ba62-a296743bd078%3Ala; lna2=YTYxZDZjZjlkM2UyZGNiYWMzMzhlMzUwZDg4OTU0MTMyYjZmYWMzMDNkMzc0MTIzMzBkZWU4OThjMGM0NWI2ODY4NTJlYTY1dXJuOnVzZXI6UEExODY2NzIxNTchMTAwMDIwMiwxNTM5MTA5LCFub25l; X-LN-Session-TTL=2025-06-18T21%3A33%3A41Z%2C2025-06-18T18%3A33%3A41Z; Perf=%7B%22name%22%3A%22document_uscontents-handler_minitocbrowse_click%22%2C%22sit%22%3A%221750264431955%22%7D',
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

response = requests.get('https://advance.lexis.com/documentpage/', params=params, cookies=cookies, headers=headers)

if response.status_code == 200:
    html_content = response.text
    with open("lexis_document.html", "w", encoding='utf-8') as file:
        file.write(html_content)
    
    pdfkit.from_file("lexis_document.html", "lexis_document.pdf")
    print("PDF generated successfully as 'lexis_document.pdf'")
else:
    print(f"Failed to retrieve page. Status code: {response.status_code}")

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re

base_url = "https://vu.brunet.app/exams/"
download_dir = "/host_desktop/VU_EXAMS"
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

solution_urls = []  # Collect ALL solution URLs first

def collect_solutions(url, visited=set()):
    if url in visited:
        return
    visited.add(url)
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = urljoin(url, link['href'])
        if href.endswith('.pdf') and re.search(r'solution', href, re.I):
            solution_urls.append(href)
            print(f"Found solution {len(solution_urls)}: {href}")
        elif '/exams/' in href:
            collect_solutions(href, visited)

def download_solutions():
    total_found = len(solution_urls)
    downloaded = 0
    os.makedirs(download_dir, exist_ok=True)
    
    print(f"\nStarting downloads: {total_found} solution files found.")
    for i, href in enumerate(solution_urls, 1):
        filename = os.path.basename(urlparse(href).path)
        filepath = os.path.join(download_dir, filename)
        
        if os.path.exists(filepath):
            print(f"Skipping ({i}/{total_found}): {filename}")
        else:
            try:
                with open(filepath, 'wb') as f:
                    f.write(session.get(href).content)
                downloaded += 1
                print(f"Downloaded ({i}/{total_found}): {filename}")
            except Exception as e:
                print(f"Failed ({i}/{total_found}): {filename} - {e}")
    
    print(f"\nFinal: {downloaded}/{total_found} saved to {download_dir}")

# Run it
collect_solutions(base_url)
download_solutions()

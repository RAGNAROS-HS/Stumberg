import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re

base_url = "https://vu.brunet.app/exams/"
download_dir = "/host_desktop/VU_EXAMS" 
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})
total_found = 0
downloaded = 0

def download_solutions(url, visited=set()):
    global total_found, downloaded
    if url in visited:
        return
    visited.add(url)
    resp = session.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = urljoin(url, link['href'])
        if href.endswith('.pdf') and re.search(r'solution', href, re.I):
            total_found += 1
            print(f"Found solution {total_found}: {href}")
        elif '/exams/' in href:
            download_solutions(href, visited)
    
    # Download phase with progress
    if total_found > 0:
        print(f"\nStarting downloads: {total_found} solution files found.")
        resp = session.get(url)  # Refetch for download links
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = urljoin(url, link['href'])
            if href.endswith('.pdf') and re.search(r'solution', href, re.I):
                filename = os.path.basename(urlparse(href).path)
                filepath = os.path.join(download_dir, filename)
                os.makedirs(download_dir, exist_ok=True)
                
                if os.path.exists(filepath):
                    print(f"Skipping (exists): {downloaded+1}/{total_found} - {filename}")
                else:
                    with open(filepath, 'wb') as f:
                        f.write(session.get(href).content)
                    downloaded += 1
                    print(f"Downloaded {downloaded}/{total_found}: {filename}")
    
    print(f"Completed {url}: {downloaded}/{total_found}")

download_solutions(base_url)
print(f"\nFinal: {downloaded}/{total_found} solution PDFs saved to {download_dir}")
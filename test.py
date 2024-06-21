import re
from pprint import pp
from bs4 import BeautifulSoup
import math
import os
from pathlib import Path

file_directory = 'rhf' 
queue = ['index.html']
visited = []
visited_urls = []
file_limit = 2000

while len(queue) > 0 and len(visited) <= file_limit:
    print(len(visited))
    file_name = queue.pop(0)
    if not(file_name.endswith('.html') or file_name.endswith('.htm')) or file_name.startswith('mailto:'):
        continue
    file_path = Path(os.path.join(file_directory, file_name)).resolve()
    if file_path in visited:
        continue
    visited.append(file_path)
    visited_urls.append(file_name)

    try:
        with open(file_path) as f:
            html = f.read()
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            # Extract the links from the text
            path = '/'.join(file_name.split('/')[:-1])
            for link in soup.find_all('a', href=True):
                root = link['href'].split('/')[0]
                if root.endswith('.com') or root.endswith('.org') or root.endswith('.net'):
                    href = link['href']
                else:
                    href = path + '/' + link['href']
                links.append(href)
                queue.append(href)
            # pp(links)
    except Exception as e:
        print(e)
        continue
# pp(visited_urls)
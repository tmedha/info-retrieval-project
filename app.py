# Medha Tripathi (Student ID: 20655230)
# Samyuktha Reddy Gurram (Student ID: 20719222)
# Suyesh Bhatta (Student ID: 20672078)

# Thinsg to do:
# Words ko wapas list
# Tokenizer

from zipfile import ZipFile
from bs4 import BeautifulSoup
import os
import re


with ZipFile('Jan.zip', 'r') as zip:
    zip.extractall('.')

file_directory = 'Jan' 

file_list = os.listdir(file_directory)
index_map = {}

for file_name in file_list:
    file_path = os.path.join(file_directory, file_name)
    
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text().lower()
            extracted_strings = re.findall(r'[a-z]+', text)
            extracted_strings = set(extracted_strings)
            links = []
            for link in soup.find_all('a', href=True):
                links.append(link['href'])
            index_map[file_name] = {
                "words": extracted_strings,
                "links": links
            }
print(index_map)
while False:
    search_key = input('Enter a search key=> ').strip()
    matches = []
    if search_key == '':
        print('Bye.')
        break
    for file_name in index_map:
        if search_key in index_map[file_name]:
            matches.append(file_name)
    if len(matches) > 0:
        for file_name in matches:
            print('Found a match:', file_name)
    else:
        print('No match.')
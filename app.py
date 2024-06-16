# Medha Tripathi (Student ID: 20655230)
# Samyuktha Reddy Gurram (Student ID: 20719222)
# Suyesh Bhatta (Student ID: 20672078)

# decode utf
# nltk

from zipfile import ZipFile
from bs4 import BeautifulSoup
import os
import re
from pprint import pp
import math
from flask import Flask, render_template, request

from functions import generate_index, query


with ZipFile('Jan.zip', 'r') as zip:
    zip.extractall('.')

file_directory = 'Jan' 

inverted_index, file_properties, index_map = generate_index(file_directory)

# while True:
#     search_key = input('Enter a search key=> ').strip().lower()
#     matches = []
#     if search_key == '':
#         print('Bye.')
#         break
#     documents = query(search_key, file_properties, inverted_index)
#     if len(documents) > 0:
#         for file_name in documents:
#             print('Found a match:', file_name)
#     else:
#         print('No match.')

app = Flask(__name__,
            static_url_path='', 
            static_folder='static'
)

@app.route("/")
def home():
    search = request.args.get('search')
    print(search)
    if search:
        documents = query(search.lower(), file_properties, inverted_index)
        return render_template('home.html', documents=documents)

    return render_template('home.html')
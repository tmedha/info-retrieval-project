# Medha Tripathi (Student ID: 20655230)
# Samyuktha Reddy Gurram (Student ID: 20719222)
# Suyesh Bhatta (Student ID: 20672078)

from zipfile import ZipFile
from flask import Flask, render_template, request
import os

from functions import generate_index, query

if not os.path.exists('rhf'):
    with ZipFile('rhf.zip', 'r') as zip:
        zip.extractall('.')

file_directory = 'rhf' 

inverted_index, file_properties, index_map, document_map = generate_index(file_directory)

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
            static_url_path='/rhf', 
            static_folder=file_directory
)

@app.route("/")
def home():
    search = request.args.get('search')
    print(search)
    if search:
        documents, documents2 = query(search.lower(), file_properties, inverted_index, document_map)
        return render_template('home.html', documents=documents, documents2=documents2)

    return render_template('home.html')
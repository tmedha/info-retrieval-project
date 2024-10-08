from bs4 import BeautifulSoup
import re
import math
import os
import pickle
from pathlib import Path
# from pprint import pprint as pp

# Create a set of stopwords
stopwords = {'a', 'an', 'the', 'of'}

def get_html_files(file_directory):
    queue = ['index.html']
    visited = []
    visited_urls = []

    while len(queue) > 0:
        # print(len(visited), 'files spidered.', end='\r')
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
    print('Spidering completed.')
    return visited_urls

# Function to generate the inverted index
def generate_index(file_directory):
    index_file = 'index.pkl'
    if os.path.isfile(index_file):
        with open(index_file, 'rb') as filehandle:
            inverted_index, file_properties, index_map, document_map = pickle.load(filehandle)
        return inverted_index, file_properties, index_map, document_map
    
    # Get the list of files in the directory
    file_list = get_html_files(file_directory)
    total_files = len(file_list)
    index_map = {}
    document_map = {}
    # Initialize the inverted index and file properties
    inverted_index = {}
    file_properties = {file_name: {'max_freq': 0, 'doc_vector': 0} for file_name in file_list}

    # Iterate through the files
    for file_name in file_list:
        file_path = os.path.join(file_directory, file_name)
        
        # Read the content of the file
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    # Parse the content using BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text().lower()
                    # Extract the words from the text
                    extracted_strings = re.findall(r'[a-z]+', text)
                    extracted_strings = set(extracted_strings)
                    links = []
                    # Extract the links from the text
                    for link in soup.find_all('a', href=True):
                        links.append(link['href'])
                    index_map[file_name] = {
                        "words": extracted_strings,
                        "links": links
                    }
                    # Iterate through the words
                    for i in re.finditer(r'[a-z\']+', text):
                        m = i.group()
                        if m in stopwords:
                            continue
                        a, b = i.span()
                        if m not in inverted_index:
                            inverted_index[m] = {}
                        # Update the inverted index
                        if file_name not in inverted_index[m]:
                            inverted_index[m][file_name] = {
                                'freq': 0,
                                'postings': []
                            }
                        inverted_index[m][file_name]['freq'] += 1
                        inverted_index[m][file_name]['postings'].append(a)
            except: 
                continue

    for word in inverted_index:
        files = inverted_index[word]
        for file_name in files:
            freq = files[file_name]['freq']
            if freq > file_properties[file_name]['max_freq']:
                file_properties[file_name]['max_freq'] = freq

    for word in inverted_index:
        files = inverted_index[word]
        df = len(files)
        for file_name in files:
            data = files[file_name]
            freq = data['freq']
            max_freq = file_properties[file_name]['max_freq']
            # Calculate the tfidf
            tfidf = (freq / max_freq) * (math.log(total_files / (df + 1), 2) + 1)
            data['tfidf'] = tfidf

    for word in inverted_index:
        files = inverted_index[word]
        for file_name in files:
            tfidf = files[file_name]['tfidf']
            file_properties[file_name]['doc_vector']+= tfidf*tfidf
    
    for word in inverted_index:
        files = inverted_index[word]
        for file_name in files:
            if file_name not in document_map:
                document_map[file_name] = {}
            document_map[file_name][word] = files[file_name]['tfidf']
    
    with open(index_file, 'wb') as filehandle:
        pickle.dump([inverted_index, file_properties, index_map, document_map], filehandle, protocol=pickle.HIGHEST_PROTOCOL)


    return inverted_index, file_properties, index_map, document_map

# Function to get the relevant documents
def get_relevant_documents(relevances):
    documents = []
    for document in relevances:
        if relevances[document] > 0:
            documents.append(document)
    return documents

# Function to get the sorted relevant documents
def get_sorted_relevant_documents(relevances):
    sorted_documents = list(relevances.items())
    sorted_documents.sort(key=lambda x: x[1], reverse=True)
    documents = []
    for document in sorted_documents:
        if document[1] > 0:
            documents.append(document[0])
    return documents

# Function to query the inverted index
def query_single(query, file_properties, inverted_index):
    relevances = {}
    if query not in inverted_index:
        return []
    data = inverted_index[query]
    for file_name in data:
        tfidf = data[file_name]['tfidf']
        doc_vector = file_properties[file_name]['doc_vector']
        relevance = (1 / math.sqrt(2)) * (1 / math.sqrt(doc_vector)) * tfidf
        relevances[file_name] = relevance
    return get_relevant_documents(relevances)

# Function to query the inverted index using vector space model
def query_vector(query, file_properties, inverted_index):
    queries = query.split(' ')
    relevances = {file_name: 0 for file_name in file_properties}
    for file_name in relevances:
        doc_vector = file_properties[file_name]['doc_vector']
        tfidf = 0
        for word in queries:
            if word in inverted_index and file_name in inverted_index[word]:
                tfidf += inverted_index[word][file_name]['tfidf']
        relevance = (1 / math.sqrt(2)) * (1 / (math.sqrt(doc_vector)+1)) * tfidf
        relevances[file_name] = relevance
    # print(relevances)
    return get_sorted_relevant_documents(relevances)

# Function to query the inverted index using AND operator
def query_and(query, file_properties, inverted_index):
    queries = query.split(' and ')
    relevances = {file_name: 0 for file_name in file_properties}
    for file_name in relevances:
        doc_vector = file_properties[file_name]['doc_vector']
        tfidf = 0
        all = True
        for word in queries:
            if word in inverted_index and file_name in inverted_index[word]:
                continue
            else:
                all = False
        if not all:
            continue
        for word in queries:
            if word in inverted_index and file_name in inverted_index[word]:
                tfidf += inverted_index[word][file_name]['tfidf']
        relevance = (1 / math.sqrt(2)) * (1 / math.sqrt(doc_vector)) * tfidf
        relevances[file_name] = relevance
    return get_relevant_documents(relevances)

# Function to query the inverted index using BUT operator
def query_but(query, file_properties, inverted_index):
    query1, query2 = query.split(' but ')
    if query1 not in inverted_index:
        return []
    data = inverted_index[query1]
    relevances = {file_name: 0 for file_name in file_properties}
    for file_name in relevances:
        if query2 in inverted_index and file_name in inverted_index[query2]:
            continue
        if query1 in inverted_index and file_name not in inverted_index[query1]:
            continue
        doc_vector = file_properties[file_name]['doc_vector']
        tfidf = data[file_name]['tfidf']
        relevance = (1 / math.sqrt(2)) * (1 / math.sqrt(doc_vector)) * tfidf
        relevances[file_name] = relevance
    return get_relevant_documents(relevances)

# Function to query the inverted index using OR operator
def query_or(query, file_properties, inverted_index):
    queries = query.split(' or ')
    documents = []
    for word in queries:
        documents += query_single(word, file_properties, inverted_index)
    return list(set(documents))

# Function to query the inverted index using phrasal search
def query_phrasal(query, file_properties, inverted_index):
    queries = query.strip('"').split(' ')
    if len(queries) == 1:
        return query_single(queries[0], file_properties, inverted_index)
    for query in queries:
        if query not in inverted_index:
            return []
    data = inverted_index[queries[0]]
    relevances = {file_name: 0 for file_name in file_properties}
    for file_name in relevances:
        if queries[0] in inverted_index and file_name not in inverted_index[queries[0]]:
            continue
        doc_vector = file_properties[file_name]['doc_vector']
        tfidf = data[file_name]['tfidf']
        relevance = (1 / math.sqrt(2)) * (1 / math.sqrt(doc_vector)) * tfidf
        # Get the postings of the first word
        postings = [*data[file_name]['postings']]
        go_next = False
        for i in range(1, len(queries)):
            previous_word = queries[i-1]
            current_word = queries[i]
            to_remove = []
            if current_word in stopwords or file_name not in inverted_index[current_word]:
                go_next = True
                break
            if current_word not in inverted_index:
                return []
            for j in range(len(postings)):
                postings[j] += len(previous_word) + 1
            for posting in postings:
                if posting not in inverted_index[current_word][file_name]['postings']:
                    to_remove.append(posting)
            for p in to_remove:
                postings.remove(p)
        if go_next:
            continue
        if len(postings) > 0:
            relevances[file_name] = relevance

    return get_relevant_documents(relevances)

def get_correlated_documents(queries, documents, file_properties, inverted_index, document_map):
    stop1 = 4
    stop2 = 3
    stop3 = 100
    stop4 = 5
    stop5 = 50
    top_documents = documents[:stop1]
    keywords = []
    correlations = {}
    for doc in top_documents:
        for word in inverted_index:
            if doc in inverted_index[word]:
                keywords.append(word)
    for word1 in queries:
        if word1 in inverted_index:
            for word2 in keywords:
                corr = 0
                word1_documents = set(inverted_index[word1].keys())
                word2_documents = set(inverted_index[word2].keys())
                common_documents = word1_documents & word2_documents
                for com_d in common_documents:
                    word1_tfidf = inverted_index[word1][com_d]['tfidf']
                    word2_tfidf = inverted_index[word2][com_d]['tfidf']
                    corr += word1_tfidf*word2_tfidf
                if word2 not in correlations:
                    correlations[word2] = 0
                correlations[word2] += corr
    correlations_list = [{'word': word, 'corr': corr} for word, corr in correlations.items()]
    correlations_list.sort(reverse=True, key=lambda x: x['corr'])
    top_correlations = correlations_list[:stop2]
    top_keywords = [word['word'] for word in top_correlations]
    now_words = queries + top_keywords
    reformulated_query = ' '.join(now_words)
    related_documents = query_vector(reformulated_query, file_properties, inverted_index)[:stop3]
    doc_correlations = {}
    for doc1 in documents[:stop4]:
        for doc2 in related_documents:
            if doc1 == doc2:
                continue
            if doc2 not in doc_correlations:
                doc_correlations[doc2] = 0
            doc1_words = set(document_map[doc1].keys())
            doc2_words = set(document_map[doc2].keys())
            common_words = doc1_words & doc2_words
            for word in common_words:
                doc_correlations[doc2] += document_map[doc1][word]*document_map[doc2][word]
    doc_correlations_list = [{'doc': doc, 'corr': corr} for doc, corr in doc_correlations.items()]
    doc_correlations_list.sort(reverse=True, key=lambda x: x['corr'])
    top_doc_correlations = doc_correlations_list[:stop5]
    top_docs = [doc['doc'] for doc in top_doc_correlations]
    return top_docs

# Function to process the queries
def query(search_key, file_properties, inverted_index, document_map):
    if '"' in search_key:
        queries = search_key.strip('"').split(' ')
        documents = query_phrasal(search_key, file_properties, inverted_index)
    elif ' and ' in search_key:
        queries = search_key.split(' and ')
        documents = query_and(search_key, file_properties, inverted_index)
    elif ' but ' in search_key:
        query1, query2 = search_key.split(' but ')
        queries = [query1]
        documents = query_but(search_key, file_properties, inverted_index)
    elif ' or ' in search_key:
        queries = search_key.split(' or ')
        documents = query_or(search_key, file_properties, inverted_index)
    elif ' ' not in search_key:
        queries = [search_key]
        documents = query_single(search_key, file_properties, inverted_index)
    else:
        queries = search_key.split(' ')
        documents = query_vector(search_key, file_properties, inverted_index)

    documents2 = get_correlated_documents(queries, documents, file_properties, inverted_index, document_map)
    
    return documents, documents2
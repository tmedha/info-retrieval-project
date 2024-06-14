from bs4 import BeautifulSoup
import re
import math
import os

def generate_index(file_directory):
    file_list = os.listdir(file_directory)
    total_files = len(file_list)
    index_map = {}
    inverted_index = {}
    file_properties = {file_name: {'max_freq': 0, 'doc_vector': 0} for file_name in file_list}

    stopwords = {'a', 'an', 'the', 'of'}

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
                for i in re.finditer(r'[a-z]+', content):
                    m = i.group()
                    if m in stopwords:
                        continue
                    a, b = i.span()
                    if m not in inverted_index:
                        inverted_index[m] = {}
                    if file_name not in inverted_index[m]:
                        inverted_index[m][file_name] = {
                            'freq': 0,
                            'postings': []
                        }
                    inverted_index[m][file_name]['freq'] += 1
                    inverted_index[m][file_name]['postings'].append(a)
    # pp(inverted_index)

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
            tfidf = (freq / max_freq) * (math.log(total_files / (df + 1), 2) + 1)
            data['tfidf'] = tfidf

    for word in inverted_index:
        files = inverted_index[word]
        for file_name in files:
            tfidf = files[file_name]['tfidf']
            file_properties[file_name]['doc_vector']+= tfidf*tfidf

    return inverted_index, file_properties, index_map

def get_relevant_documents(relevances):
    documents = []
    for document in relevances:
        if relevances[document] > 0:
            documents.append(document)
    return documents

def query_single(query, file_properties, inverted_index):
    relevances = {}
    data = inverted_index[query]
    for file_name in data:
        tfidf = data[file_name]['tfidf']
        doc_vector = file_properties[file_name]['doc_vector']
        relevance = (1 / math.sqrt(2)) * (1 / math.sqrt(doc_vector)) * tfidf
        relevances[file_name] = relevance
    return get_relevant_documents(relevances)

def query_vector(query, file_properties, inverted_index):
    queries = query.split(' ')
    relevances = {file_name: 0 for file_name in file_properties}
    for file_name in relevances:
        doc_vector = file_properties[file_name]['doc_vector']
        tfidf = 0
        for word in queries:
            if word in inverted_index and file_name in inverted_index[word]:
                tfidf += inverted_index[word][file_name]['tfidf']
        relevance = (1 / math.sqrt(2)) * (1 / math.sqrt(doc_vector)) * tfidf
        relevances[file_name] = relevance
    return get_relevant_documents(relevances)

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

def query_but(query, file_properties, inverted_index):
    query1, query2 = query.split(' but ')
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

def query_or(query, file_properties, inverted_index):
    queries = query.split(' or ')
    documents = []
    for word in queries:
        documents += query_single(word, file_properties, inverted_index)
    return list(set(documents))

def query_phrasal(query, file_properties, inverted_index):
    queries = query.strip('"').split(' ')
    if len(queries) == 1:
        return query_single(queries[0], file_properties, inverted_index)
    data = inverted_index[queries[0]]
    relevances = {file_name: 0 for file_name in file_properties}
    for file_name in relevances:
        if queries[0] in inverted_index and file_name not in inverted_index[queries[0]]:
            continue
        doc_vector = file_properties[file_name]['doc_vector']
        tfidf = data[file_name]['tfidf']
        relevance = (1 / math.sqrt(2)) * (1 / math.sqrt(doc_vector)) * tfidf
        postings = data[file_name]['postings']
        for i in range(1, len(queries)):
            previous_word = queries[i-1]
            current_word = queries[i]
            if current_word not in inverted_index or file_name not in inverted_index[current_word]:
                return []
            for j in range(len(postings)):
                postings[j] += len(previous_word) + 1
            for posting in postings:
                if posting not in inverted_index[current_word][file_name]['postings']:
                    postings.remove(posting)
        if len(postings) > 0:
            relevances[file_name] = relevance

    return get_relevant_documents(relevances)

def query(search_key, file_properties, inverted_index):
    documents = []
    if ' and ' in search_key:
        documents = query_and(search_key, file_properties, inverted_index)
    elif ' but ' in search_key:
        documents = query_but(search_key, file_properties, inverted_index)
    elif ' or ' in search_key:
        documents = query_or(search_key, file_properties, inverted_index)
    elif '"' in search_key:
        documents = query_phrasal(search_key, file_properties, inverted_index)
    elif ' ' not in search_key:
        documents = query_single(search_key, file_properties, inverted_index)
    else:
        documents = query_vector(search_key, file_properties, inverted_index)
    
    return documents
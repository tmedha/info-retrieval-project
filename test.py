import re
from pprint import pp
x='''
cat dog rat mat bat cat cat rat dog
'''
inverted_index = {}
document = 'x'
for i in re.finditer(r'[a-z]+', x):
    m = i.group()
    a, b = i.span()
    if m not in inverted_index:
        inverted_index[m] = {}
    if document not in inverted_index[m]:
        inverted_index[m][document] = {
            'freq': 0,
            'postings': []
        }
    inverted_index[m][document]['freq'] += 1
    inverted_index[m][document]['postings'].append(a)
pp(inverted_index)
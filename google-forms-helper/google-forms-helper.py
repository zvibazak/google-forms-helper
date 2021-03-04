#!/usr/bin/env python3
import requests
import re
import json
from datetime import datetime

FORM = 1
FIELDS = 1
TITLE = 8
ID = 0
NAME = 1
DESCRIPTION = 2
TYPE = 3
VALUE = 4
OPTIONS = 1
URL = -5

types = {
    0: 'Short Answer',
    1: 'Paragraph',
    2: 'Radio',
    3: 'Dropdown',
    4: 'Checkboxes',
    9: 'Date',
}

DEFAULT_VALUE = ''

choice_types = ['Radio', 'Checkboxes', 'Dropdown']

def get_url(data):
    return 'https://docs.google.com/forms/d/' + str(data[URL]) + '/formResponse'

def get_name(data):
    return data[FIELDS][TITLE]

def get_options(elem):
    options_raw = elem[VALUE][0][OPTIONS]
    return list(map(lambda l: l[0], options_raw))

def get_fields(data):
    fields = {}
    for elem in data[FORM][FIELDS]:
        field = {
            'description': elem[DESCRIPTION],
            'type': types.get(elem[TYPE]),
            'id': elem[VALUE][0][ID],
            'submit_id': 'entry.' + str(elem[VALUE][0][ID]),
            'value': DEFAULT_VALUE
        }

        if field['type'] in choice_types:
            field['options'] = get_options(elem)

        fields[elem[NAME]] = field
    return fields

def parse_data(data_str):
    data = json.loads(data_str)
    return {
        'url': get_url(data),
        'name': get_name(data),
        'fields': get_fields(data),
    }

def get_form(url):
    body = requests.get(url).text
    match = re.search(r'FB_PUBLIC_LOAD_DATA_ = ([^;]*);', body)
    if not match: return None
    data = parse_data(match.group(1))
    return data

def output(form):
    for name in form['fields']:
        field = form['fields'][name]
        print(name + ' (' + str(field['id']) + ')')
        if field['description']: print('> ' + field['description'])
        if 'options' in field:
            for option in field['options']:
                print('  - ' + option)
        print()

def submit(form):
    payload = {}
    for name in form['fields']:
        field = form['fields'][name]
        if field['type'] in choice_types and field['value'] not in field['options']:
            payload[field['submit_id']] = '__other_option__'
            payload[field['submit_id'] + '.other_option_response'] = field['value']
        elif field['type'] == types[9]: #Date
            payload[field['submit_id']+'_year'] = field['value'][0]
            payload[field['submit_id']+'_month'] = field['value'][1]
            payload[field['submit_id']+'_day'] = field['value'][2]
        else:
            payload[field['submit_id']] = field['value']
    res = requests.post(form['url'], data=payload)
    form_res=""
    match = re.search(r'<div class="freebirdFormviewerViewResponseConfirmationMessage">(.*)<\/div><div class="freebirdFormviewerViewResponseLinksContainer"', res.text)
    if match: 
        form_res = match.group(1)        
    print(res.status_code,res.reason,form_res)
    return res

if __name__ == "__main__":
    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36'
    })

    url = "https://docs.google.com/forms/d/e/1FAIpQLSff3dmaMyuU5TQ2fLdQOY5Mf2kF3molP_d73dcFe8b74vw/viewform"
    
    data = get_form(url)
    output(data)
    #fill the data
    submit(data)

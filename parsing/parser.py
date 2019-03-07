from bs4 import BeautifulSoup
import jdatetime
import datetime
import re
import time
import json
import sys
from os import listdir

# Project packages
import nationalid
import dateextract
import namehelper
import translator

# Global vars
DEBUG = True

''' Handy regex
All persian numerals: [۰۱۲۳۴۵۶۷۸۹]\w+
                      or [\u06F0-\u06F90-9]+
'''

#################################
# CENTRAL FILE PROCESSOR
# This calls all the parsing helpers
# and sends back all parsed data for a provided file name
#################################
def parse(fileName):
    certaintyScore = 100 # This will be decreased by percentages if signs of uncertainty show
    # Get document ID
    file_chunks = fileName.split('/')
    last_chunk = file_chunks[len(file_chunks)-1]
    document_id = last_chunk[:len(last_chunk)-5] # Remove the .html at the end
    print('Document ID:', document_id)
    # Grab file contents
    htmlFile = open(fileName)
    html = htmlFile.read()
    htmlFile.close()
    # Extract all pertinent sections
    soup = BeautifulSoup(html, 'html.parser')
    # This extracts the declaration which doesn't include the document information section. This is where the names occur.
    declaration = ''
    try:
        declaration = soup.find(class_='Jus').contents[0]
    except:
        print('Malformed file')
        return
    # This extracts where the national ID is sometimes stored
    title = ''
    try:
        title = soup.find(id='cphMain_lblNewsTitle').contents[0]
    except:
        title = ''
    # These are all the extracted text chunks functions will have available to parse
    contents = {
            'title': title,
            'declaration': declaration
            }
    # Company ID retreival
    companyId = nationalid.parse_id(contents['title'])
    if DEBUG:
        print('National ID (title):', companyId)
    if companyId == None:
        certaintyScore *= 0.8  # Proof of concept not good 
        companyId = nationalid.parse_id(contents['declaration']) # This finds a company ID in the text but it might be referencing another corporation
    if DEBUG:
        print('National ID (declaration):', nationalid.parse_id(contents['declaration']))
    # Various date retreival
    try:
        dates = dateextract.parse_dates(html, contents)
    except:
        print('Malformed file. Returning early')
        return
    # Name retreival
    names = get_names(contents)
    names += double_tap_names(contents)
    names += namehelper.parse_name_sandwhich(contents)
    cleaned_names = clean(names)
    # Now we get the document date in English dates
    persian_date = dates['registration_date']
    date_data = persian_date.split('/')
    document_date = jdatetime.datetime(int(date_data[0]), int(date_data[1]), int(date_data[2])).togregorian()
    document_timestamp = time.mktime(document_date.timetuple())
    print(document_timestamp)
    return {
        'document_id': document_id,
        'document_date': document_timestamp,
        'company_id': translator.convert(companyId),
        's3_path': fileName[6:],
        'names': cleaned_names,
        'dates': dates,
        'raw_title': contents['title'],
        'raw_body': contents['declaration'],
        'certainty_score': certaintyScore,
        'parser_version': 1
    }

def clean(names):
    '''Deduplicates names and tries to improve ID selection and name accuracy
    '''
    num_names = len(names)
    cleaned = []
    alias_list = {}
    # First we take names marked with the same ID and merge them preserving the
    # name variations in an alias list
    for i in range(num_names):
        new = True
        if not names[i] == None:
            for j in range(0, i): # Search every name preceding this one
                if names[i]['employee_id'] == names[j]['employee_id']:
                    new = False
        if new:
            if not names[i] == None:
                alias_list[names[i]['employee_id']] = [names[i]['name']]
            cleaned += [names[i]]
        else:
            alias_list[names[i]['employee_id']] += [names[i]['name']]
    names = cleaned
    num_names = len(names)
    cleaned = []
    # Second we take names without an ID (id=None) and if they exactly match one
    # of the names for a person with an ID we merge the two
    for i in range(num_names):
        matches = []
        for j in range(num_names):
            if not i == j:
                if names[i]['employee_id'] == None:
                    if not names[j]['employee_id'] == None:
                        for name_check in alias_list[names[j]['employee_id']]:
                            if name_check.find(names[i]['name']):
                                matches += [names[j]['employee_id']]
        if len(matches) > 1:
            cleaned += [names[i]]
        elif len(matches) == 1:
            alias_list[matches[0]] += names[i]['name'] # This now belongs to said ID and we don't save it anymore
        else:
            cleaned += [names[i]]
    formatted = []
    for i in cleaned:
        if not i['employee_id'] == None:
            i['aliases'] = alias_list[i['employee_id']]
        else:
            i['aliases'] = [i['name']]
        formatted += [i]
    return formatted

def get_names(contents):
    text = contents['declaration'] # Names only occur in the declaration
    names = []
    # This Regex so far has been successful sometimes but not always, uncomment and test individually
    regex = [
            #':\s(.*)\s([\u06F0-\u06F90-9]{10})',
            #': (.*) \,',
            #'[\u06F0-\u06F90-9]{10} (.*) :',
            #namehelper.SALUTATIONS[0] + ' (.*)' + namehelper.NATIONAL_BANK_NUMBER + ' ([\u06F0-\u06F90-9]{10})',
            #'([\u06F0-\u06F90-9]{10}) ' + namehelper.NATIONAL_BANK_NUMBER + ' (.*) ' + namehelper.SALUTATIONS[0],
            #'([\u06F0-\u06F90-9]{10}) به شماره ملی'
            ] # Note: This regex is currently innacurate, but serves as a test extraction
    for i in regex: # Loop through every regex pattern
        namesNew = re.findall(i, text)
        for j in namesNew:
            # If the regex supported grabbing an ID, then add it otherwise don't
            if len(j) == 1:
                names += [{
                    'name': translator.convert(j[0]),
                    'employee_id': None
                    }]
            else:
                names += [{
                    'name': translator.convert(j[0]),
                    'employee_id': translator.convert(j[1])
                    }]
    return names

def double_tap_names(contents):
    # This function is built on the principle of finding any ID at all
    # and then confirming or denying the existence of other words, etc.
    # nearby until you know exactly where to cut the name from.
    # Notes: re namespaces regex variables
    text = contents['declaration']
    # Grabs ID and 40 characters on either side
    re_id_chunk = '.{30}[\u06F0-\u06F90-9]{10}.{20}'
    re_id = '[\u06F0-\u06F90-9]{10}'
    all_id_chunks = re.findall(re_id_chunk, text) # Find every possible ID (might include business IDs, etc.)
    people = []
    for i in all_id_chunks:
        if len(re.findall(re_id, i)) > 1:
            print('Unfortunately we found multiple IDs in the string.')
        # Double tap
        confirmed_name = False
        parsed_name = None
        if namehelper.NATIONAL_BANK_NUMBER in i: # This national bank number has only every appeared connected with a person's ID
            confirmed_name = True
            idx_signifier = i.find(namehelper.NATIONAL_BANK_NUMBER)
            parsed_name = i[:idx_signifier] # Liberal cutting but won't miss a portion of the name
        elif namehelper.SALUTATIONS[0] in i: # If we see Mr. then we know it's a name
            confirmed_name = True
            idx_signifier = i.find(namehelper.SALUTATIONS[0])
            parsed_name = i[idx_signifier:] # Too liberal as well but can be refined
        if not parsed_name:
            # In the future we will do named entity recognition here
            print('No name grabbed')
            pass
        if confirmed_name:
            parsed_name = translator.convert(parsed_name) # Clean it up as much as we can
            people += [{ 'name': parsed_name, 'employee_id': translator.convert(re.findall(re_id, i)[0]) }] # ID is changed to English numerals
    return people

def parse_folder(folder):
    was = time.time()
    # This array can be changed to pull from every file in a directory
    to_parse = [
            'test-files/examplePersianDoc.html',
            'test-files/namesAtEndWeird.html',
            'test-files/sample_1.html',
            'test-files/sample_2.html',
            'test-files/sample_3.html',
            'test-files/sample_4.html'
            ]
    try:
        files = listdir(folder)
        to_parse = []
        for i in files:
            to_parse += [ folder + '/' + i ]
    except:
        pass
    parsedCount = 0
    batch = 0
    all_data = []
    for i in to_parse:
        if DEBUG:
            print()
            print('-----------------------')
            print('- Parsing {0}'.format(i))
            print('- At time {0}'.format(datetime.datetime.now()))
            print('-----------------------')
        data = parse(i) # Grab all the data we support extracting
        if DEBUG:
            print(data)
        if not data == None:
            parsedCount += 1
            all_data += [data]
        else:
            print('Parser returned nothing')
        if (parsedCount-3000*batch) > 3000:
            batch += 1
            print('Saving batch {0}'.format(batch))
            file_id = folder.replace('/', '-')
            out_file = open('records/persian_records_{0}_batch_{1}.json'.format(file_id, batch), 'w')
# TODO: Add additional metadata to the JSON
            out_file.write(json.dumps({
                'parsed_time': was,
                'parsed_duration': was - time.time(), # Let's us keep track of how each parsing job is doing
                'data': all_data, # All the data will be here
                'count': parsedCount
                }))
            out_file.close()
            print('Finished saving.')

    if DEBUG:
        print('Start:', was)
        print('End:', time.time())
    if not parseCount % 3000 == 0:
        batch += 1
        print('Saving contents...')
        file_id = folder.replace('/', '-')
        out_file = open('records/persian_records_{0}_batch_{1}.json'.format(file_id, batch), 'w')
# TODO: Add additional metadata to the JSON
        out_file.write(json.dumps({
            'parsed_time': was,
            'parsed_duration': was - time.time(), # Let's us keep track of how each parsing job is doing
            'data': all_data, # All the data will be here
            'count': parsedCount
            }))
        out_file.close()
        print('Finished saving.')

######################
# Worker kick-off
######################
config_file = open('state.json')
config_raw = config_file.read()
config_file.close()
config = json.loads(config_raw)
if config['parsing'] == True:
    print('Parsing in progress. Cancelling.')
    sys.exit()
else:
    config['parsing'] = True
    config_file = open('state.json', 'w')
    config_file.write(json.dumps(config, indent=4))
    config_file.close()

directory = '~/s3mnt/'
try:
    directory = sys.argv[1]
except:
    pass

internal_directories = listdir(directory)
to_parse = []
for i in internal_directories:
    done = False
    for j in config['completed']:
        if i == j:
            done = True
    if not done:
        to_parse += [i]

print('Parsing list:')
print(to_parse)


successful = []
for i in to_parse:
    try:
        parse_folder(directory + '/' + i + '/new')
        parse_folder(directory + '/' + i + '/old')
        config['completed'] += [i]
        config_file = open('state.json', 'w')
        config_file.write(json.dumps(config, indent=4))
        config_file.close()
        successful += [i]
    except Exception as e:
        print(e)
        print('Failed to parse data for {0}'.format(i))
#config['completed'] += successful # Add success parsings to the registry
config['parsing'] = False
config_file = open('state.json', 'w')
config_file.write(json.dumps(config, indent=4))

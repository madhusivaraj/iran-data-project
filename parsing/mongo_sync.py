from pymongo import MongoClient
from threading import Thread
import sys
from os import listdir
import json
import csv
HOST_NAME = 'localhost'
PORT = 27017
connection_string = 'mongodb://iran_user:\'A>j|y*Q?)98@ds137631.mlab.com:37631/iran_parsed_info_free'
connection_string = 'mongodb://2aJcl724:h&TL0m38#@142.93.2.16:27017/iran_data'
client = MongoClient(connection_string)

BUSINESS_ID_TO_NAME = {}
try:
    data_file = open('companies_id_name.csv')
    reader = csv.reader(data_file)
    first = True
    for row in reader:
        if not first:
            BUSINESS_ID_TO_NAME[row[0]] = row[1]
except:
    print("FAILURE: Couldn't load business IDs")


db = client['iran_data']

collection = db.document_info

to_post = {
        'document_id': '',
        'names': [],
        'meeting_date': ''
        }

#result = db.document_info.insert_one(to_post)

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def get_record_count():
    return db.document_info.count()

def get_first_record():
    return db.document_info.find()[0]


def send_one(i):
    db.document_info.replace_one( {'document_id': i['document_id']}, i, upsert=True) # Replace if exists, otherwise create


def sync_record(file_name):
    data_file = open(file_name)
    data = json.loads(data_file.read())
    for chunk in chunks(data['data'], 8):
        for i in chunk:
            i['company_name'] = None
            try:
                i['company_name'] = BUSINESS_ID_TO_NAME[i['company_id']]
            except:
                pass
            t1 = Thread(target=send_one, args=[i])
            t1.start()
            t1.join()


##############################
# Worker Kick-Off
##############################
config_file = open('sync_state.json')
config_raw = config_file.read()
config_file.close()
config = json.loads(config_raw)
if config['syncing'] == True:
    print('Syncing in progress. Cancelling.')
    sys.exit()
else:
    config['syncing'] = True
    config_file = open('sync_state.json', 'w')
    config_file.write(json.dumps(config, indent=4))
    config_file.close()

directory = 'records/'
try:
    directory = sys.argv[1]
except:
    pass

record_files = listdir(directory)
to_sync = []
for i in record_files:
    done = False
    for j in config['synced_list']:
        if i == j:
            done = True
    if not done:
        to_sync += [i]

print('Sync list:')
print(to_sync)
#print('Current DB record count:', get_record_count())

synced = []
for i in to_sync:
    try:
        print('## Syncing record {0}'.format(directory + i))
        sync_record(directory + i)
        synced += [i]
        config['synced_list'] += [i]
        config_file = open('sync_state.json', 'w')
        config_file.write(json.dumps(config, indent=4))
    except Exception as e:
        print(e)
        print('Sync failed for record {0}'.format(directory + i))

config['syncing'] = False
config_file = open('sync_state.json', 'w')
config_file.write(json.dumps(config, indent=4))
print('Finished DB record count:', get_record_count())

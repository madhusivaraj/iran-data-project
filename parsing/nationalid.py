import re

def parse_id(text):
    # Note: Based on my research, the expression National ID is the same upper and lower case
    possible_types = [
            'شناسه ملی ([\u06F0-\u06F90-9]{11})'
            ]
    retreived_ids = []
    for i in possible_types:
        namesNew = re.findall(i, text)
        retreived_ids += namesNew
    if len(retreived_ids) == 1:
        return retreived_ids[0]
    else:
        print('Multiple IDs detected.')
        if len(retreived_ids) > 0:
            return retreived_ids[0] # No intelligent way to determine IDs
        else:
            return None


import re

import translator

SALUTATIONS = [
        'خانم' # Ms.
        ]

NATIONAL_BANK_NUMBER = 'به شماره ملی'


PRECEDING_SET = [
        'خانم', # Mrs.
        'قای', # Mr.
        ':', # Colon
        '.', # Period
        '-', # Dash
        'و', # And
        'سمت' # Title
        ]

PROCEEDING_SET = [
        'نمایندگی', # Representation
        'شماره ملی', # National number or SSN
        'کدملی', # [Unsure]
        'کد ملی', # National number or SSN
        'شناسه ملی', # National ID (of the company)
        'سمت' # Title
        ]

def substring_indexes(substring, string):
    """
    Generate indices of substring ends in string
    """
    last_found = -1  # Begin at -1 so the next position to search from is 0
    while True:
        # Find next index of substring, by starting after its last known position
        last_found = string.find(substring, last_found + 1)
        if last_found == -1:
            break  # All occurrences have been found
        yield last_found + (len(substring) - 1) # Return for iterator and make index be at the end


def parse_name_sandwhich(contents):
    '''This function operates on the principle that a name
    always occurs between two words/phrases and therefore
    if we compile a list of every word that precedes a name
    and every word that follows it, we can therefore ensure we
    retreive every name.

    Args:
        contents - Generalized text content object as in parser.py

    Returns:
        list of dictionaries with keys `name` and `id`
    '''
    to_return = []
    text = contents['declaration'] # Parse out the main body
    for substring in PRECEDING_SET:
        for i in substring_indexes(substring, text):
            bottom = i+1 # Move to the next character
            partition = 30 # Number of characters to search through
            search_span = text[bottom:bottom+partition]
            name_set = []
            re_id = '[\u06F0-\u06F90-9]{10}'
            id_search_span = text[bottom:bottom + partition + 10]
            ids = re.findall(re_id, id_search_span)
            id = None
            if len(ids) > 1:
                print('ERROR: multiple ids found in sandwhich method')
                print(ids)
                id = ids[0] # The first ID in the string is probably the right one
            if len(ids) == 1:
                id = ids[0]
            for proceed in PROCEEDING_SET:
                top = search_span.find(proceed) # Find first instance of the proceeding text
                if not top == -1:
                    name = search_span[:top] # By definition idx=0 is the start of name span
                    name_set += [ {'name': translator.convert(name), 'employee_id': translator.convert(id)} ]
            if len(name_set) > 1:
                print('Multiple names where found for the same beggining. Ensure clean function works.')
            to_return += name_set
    return to_return

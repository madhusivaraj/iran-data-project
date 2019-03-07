from bs4 import BeautifulSoup
import re

import translator

def parse_dates(html, contents):
    newspaperdateId = 'cphMain_lblNewsPaperDate'
    registrationdateId = 'cphMain_lblNewsDate'

    soup = BeautifulSoup(html, 'html.parser')
    newspaper_date = translator.convert(soup.find(id=newspaperdateId).contents[0])
    registration_date = translator.convert(soup.find(id=registrationdateId).contents[0])

    date_regex = [
            '[\u06F0-\u06F90-9]{4}/[\u06F0-\u06F90-9]{2}/[\u06F0-\u06F90-9]{2}',
            '[\u06F0-\u06F90-9]{2}/[\u06F0-\u06F90-9]{2}/[\u06F0-\u06F90-9]{4}'
        ]
    random_dates = []
    for i in date_regex:
        random_dates += re.findall(i, contents['declaration'])

    meeting_date = None
    if len(random_dates) >= 1:
        meeting_date = translator.convert(random_dates[0])

    return {
            'newspaper_date': newspaper_date,
            'registration_date': registration_date,
            'meeting_date': meeting_date,
            'random_dates': random_dates
            }

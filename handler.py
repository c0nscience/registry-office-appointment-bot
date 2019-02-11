import json
import random
import re
from datetime import datetime
import pytz

import requests
from bs4 import BeautifulSoup

base_url = 'https://service.berlin.de'


def next_month(href):
    return href and re.compile("terminvereinbarung/termin/day").search(href)


def bookable_appointment(href):
    return href and re.compile("terminvereinbarung/termin/time").search(href)


def search_for_available_appointment(text, class_='calendar-month-table'):
    soup = BeautifulSoup(text, 'html.parser')

    print(soup.title.string)

    month_widgets = soup.find_all(class_=class_)

    available_appointment_link = None
    next_month_link = None

    for index, month_widget in enumerate(month_widgets):
        if available_appointment_link:
            return

        month_links = month_widget.find_all(href=next_month)

        if len(month_links) > 0:
            next_month_link = month_links[0]

        available_links = month_widget.find_all(href=bookable_appointment)
        links = [link.get('href') for link in available_links]

        if len(links) > 0:
            available_appointment_link = links[0]

    if available_appointment_link:
        return available_appointment_link, None
    else:
        return None, next_month_link


user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 6.0.1; SM-J700M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.80 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
]

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en,de;q=0.9',
    'Upgrade-Insecure-Requests': str(1),
    'User-Agent': user_agents[random.randint(0, len(user_agents) - 1)],
    'Host': 'service.berlin.de'
}


def fetch_site_and_check(s, url, depth, params=None, referer=None):
    print('depth', depth)
    headers['Referer'] = referer
    response = s.get(url, params=params, headers=headers)
    available_appointment_link, next_month_link = search_for_available_appointment(response.text)

    if next_month_link and depth > 0:
        path = next_month_link.get('href')
        new_url = f'{base_url}{path}'
        if not referer:
            return fetch_site_and_check(s, new_url, depth - 1, referer=f'{base_url}/terminvereinbarung/termin/day/')
        else:
            return fetch_site_and_check(s, new_url, depth - 1, referer=url)
    else:
        return available_appointment_link, url


def scraper(event, context):
    paramsMitte = {
        'termin': 1,
        'dienstleister': '327795',
        'anliegen[]': ('318961',),
        'herkunft': 1
    }

    paramsSpandau = {
        'termin': 1,
        'dienstleister': '122932',
        'anliegen[]': ('318961',),
        'herkunft': 1
    }

    params = paramsMitte

    # Heiraten ohne Ausland Anmeldung: 318961
    # Standesamt Mitte: 327795
    # Standesamt Spandau: 122932
    # https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&dienstleister=327795&anliegen[]=318961&herkunft=1
    # https://service.berlin.de/terminvereinbarung/termin/tag.php?termin=1&dienstleister=122932&anliegen[]=318961&herkunft=1

    # bookable appointment
    # href = https://service.berlin.de/terminvereinbarung/termin/time/1561932000/

    # https://service.berlin.de/terminvereinbarung/termin/time/1561968000/428/
    s = requests.Session()

    available_appointment_link, referer = fetch_site_and_check(s,
                                                               'https://service.berlin.de/terminvereinbarung/termin/tag.php',
                                                               6,
                                                               params=params)

    # search in timetable for the first available time
    # print(available_appointment_link, referer)
    if available_appointment_link:
        timestamp_string = re.findall('\\d+', available_appointment_link)[0]
        timestamp = int(timestamp_string)

        local_timezone = pytz.timezone('Europe/Berlin')
        local_time = datetime.fromtimestamp(timestamp, local_timezone)

        appointment_date = local_time.strftime('%d.%m.%Y')

        r = requests.Request('Get', 'https://service.berlin.de/terminvereinbarung/termin/tag.php',
                             params=params)

        prep_r = r.prepare()

        body = {
            'payload': json.dumps({'text': f'Termin am {appointment_date}!! <{prep_r.url}|HIER KLICKEN>'})
        }
        # TODO parametrize slack url
        response = requests.post('https://hooks.slack.com/services/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', data=body)

        # TODO we are stuck here since we can't trick the robot detection -.-
        # time.sleep(random.randint(3, 8))
        # headers['Referer'] = referer
        # response = s.get(f'https://service.berlin.de{available_appointment_link}', headers=headers)
        # available_appointment_time_link, _ = search_for_available_appointment(response.text, class_='timetable')
        #
        # print(available_appointment_time_link)

    return {}


# scraper(None, None)

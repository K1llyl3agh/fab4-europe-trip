import json, base64, re, datetime, html, urllib.parse

sched = json.load(open('site_data_schedule.json'))
places = json.load(open('site_data_places.json'))
travel_json = json.load(open('travel_overview.json'))

def b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')

IMG = {
    'london': b64('london_map.png'),
    'italy': b64('italy_map.png'),
    'rome': b64('rome_map.png'),
    'tuscany': b64('tuscany_map.png'),
    'milan': b64('milan_map.png'),
    'hero': b64('fab4_hero_photo_web.jpg'),
    'ship': b64('ship_web.jpg'),
    'qv8': b64('qv8.png'),
    'ship_at_sea': b64('ship_at_sea_web.jpg'),
    'ztl': b64('ztl_map.png'),
}

EUROPE_MAP_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 700">
<g fill="#ffffff" fill-opacity="0.14" stroke="none">
  <path d="M170,560 L150,470 L165,420 L200,420 L180,400 L220,390 L280,350 L300,320 L330,300 L320,280 L340,260
           L350,270 L330,220 L310,180 L330,140 L300,100 L280,60 L360,55 L420,70 L430,150 L410,220 L400,260
           L380,290 L400,300 L470,290 L560,270 L600,250 L680,260 L750,280 L780,350 L760,400 L700,380
           L680,450 L650,520 L620,560 L600,500 L560,460 L540,480 L560,520 L520,560 L500,600 L480,560
           L470,500 L490,460 L500,420 L400,440 L300,480 L200,540 Z"/>
  <ellipse cx="100" cy="250" rx="24" ry="34"/>
  <path d="M140,180 L178,190 L182,260 L160,320 L138,300 L130,230 Z"/>
  <circle cx="540" cy="620" r="10"/>
  <circle cx="640" cy="560" r="7"/>
  <circle cx="665" cy="540" r="5"/>
  <ellipse cx="80" cy="90" rx="18" ry="13"/>
</g>
<g fill="none" stroke="#ffffff" stroke-opacity="0.10" stroke-width="1.4">
  <line x1="0" y1="90" x2="1000" y2="90"/>
  <line x1="0" y1="200" x2="1000" y2="200"/>
  <line x1="0" y1="310" x2="1000" y2="310"/>
  <line x1="0" y1="420" x2="1000" y2="420"/>
  <line x1="0" y1="530" x2="1000" y2="530"/>
  <line x1="0" y1="640" x2="1000" y2="640"/>
  <line x1="90" y1="0" x2="90" y2="700"/>
  <line x1="220" y1="0" x2="220" y2="700"/>
  <line x1="350" y1="0" x2="350" y2="700"/>
  <line x1="480" y1="0" x2="480" y2="700"/>
  <line x1="610" y1="0" x2="610" y2="700"/>
  <line x1="740" y1="0" x2="740" y2="700"/>
  <line x1="870" y1="0" x2="870" y2="700"/>
</g>
</svg>'''
EUROPE_MAP_B64 = base64.b64encode(EUROPE_MAP_SVG.encode('utf-8')).decode('ascii')

def esc(s):
    return html.escape(str(s)) if s is not None else ''

def collapse_events(events):
    blocks = []
    for e in events:
        t, name, status, addr = e['time'], e['event'], e['status'], e['address']
        base = re.sub(r'\s*\(continues.*?\)\s*$', '', name).strip()
        is_continue = '(continues' in name.lower()
        if blocks and is_continue:
            last = blocks[-1]
            last['end'] = t
            m = re.search(r'ends?\.?\s*(approx\.?\s*)?(\d{1,2}(:\d{2})?\s*[ap]m)', name, re.I)
            if m:
                last['end_label'] = m.group(2)
            if addr and not last['address']:
                last['address'] = addr
            if status:
                last['status'] = status
            continue
        start_display = t
        sm = re.search(r'\(starts?\.?\s*(approx\.?\s*)?(\d{1,2}(:\d{2})?\s*[ap]m)\)', base, re.I)
        if sm:
            start_display = sm.group(2)
            base = re.sub(r'\s*\(starts?.*?\)\s*$', '', base).strip()
        blocks.append({'start': start_display, 'end': t, 'end_label': None, 'name': base, 'status': status, 'address': addr})
    for b in blocks:
        if b['end_label']:
            b['time_display'] = f"{b['start']} – {b['end_label']}"
        elif b['end'] != b['start']:
            b['time_display'] = f"{b['start']} – {b['end']}"
        else:
            b['time_display'] = b['start']
    return blocks

STATUS_CLASS = {
    'Booked': 'badge-booked',
    'To Book': 'badge-tobook',
    'To Confirm': 'badge-toconfirm',
    'Optional': 'badge-optional',
}

def badge(status):
    if not status:
        return ''
    cls = STATUS_CLASS.get(status, 'badge-optional')
    return f'<span class="badge {cls}">{esc(status)}</span>'

WEBLINKS = [
    ('lighterman', 'https://www.thelighterman.co.uk/'),
    ('hard rock', 'https://cafe.hardrock.com/london/'),
]

def weblink_for(name):
    n = name.lower()
    for keyword, url in WEBLINKS:
        if keyword in n:
            return url
    return None

EVENT_TRIPADVISOR = [
    ('dinner at albert schloss', 'https://www.tripadvisor.co.uk/Restaurant_Review-g186338-d26909472-Reviews-Albert_s_Schloss_Soho-London_England.html'),
    ('dinner at the lighterman', 'https://www.tripadvisor.com/Restaurant_Review-g186338-d10121217-Reviews-The_Lighterman-London_England.html'),
    ('combo: tower of london', 'https://www.tripadvisor.com/Attraction_Review-g186338-d187788-Reviews-Tower_of_London-London_England.html'),
    ("potential early lunch at harry's knightsbridge", 'https://www.tripadvisor.com/Restaurant_Review-g186338-d13224804-Reviews-Harry_s_Dolce_Vita_Knightsbridge-London_England.html'),
]

def tripadvisor_for(name):
    n = name.lower()
    for keyword, url in EVENT_TRIPADVISOR:
        if keyword in n:
            return url
    return None

EVENT_PHONE = [
    ('dinner at albert schloss', '020 8165 0000'),
    ('dinner at the lighterman', '020 3846 3400'),
    ('dinner at hard rock cafe london', '0044 20 7514 1700'),
]

def event_phone_for(name):
    n = name.lower()
    for keyword, phone in EVENT_PHONE:
        if keyword in n:
            return phone
    return None

EVENT_W3W = [
    ('dinner at albert schloss', 'assist.given.desk'),
    ('mousetrap begins', 'trains.areas.nights'),
    ('dinner at the lighterman', 'guides.riots.trader'),
    ('arrive at the level', 'baked.belly.neck'),
    ('victoria and albert museum', 'spots.mugs.cards'),
    ("harry's knightsbridge", 'icon.spends.third'),
    ('tower of london', 'swift.blitz.funds'),
    ('vaudeville theatre', 'diner.donor.rails'),
    ('waterstones piccadilly', 'blank.buns.bump'),
    ('hard rock cafe london', 'month.wakes.tests'),
    ('the republic hotel', 'sports.pocket.anchors'),
    ('fontana delle naiadi', 'mouth.dished.cheaply'),
    ('santa maria degli angeli', 'mouth.dished.cheaply'),
    ('colosseum arena floor', 'food.reddish.dormant'),
    ('transfer by private minibus to queen victoria', 'snipe.nipped.miss'),
    ('collect avis hire car', 'snipe.nipped.miss'),
]

def event_w3w_for(name):
    n = name.lower()
    for keyword, words in EVENT_W3W:
        if keyword in n:
            return words
    return None

LIGHTERMAN_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAQgAAAEIAQAAAACLjVdSAAABi0lEQVR4nO2YwY7CMBBDn6v+/y97D54ksFqJE2G0AYTapj6Y0cRjR+bF53oF+CL+MeIG5c6y0izCa7UN0231wJAiVDm8HtSH6b56oFUTWeOxLl2YbkdIIAuM9UEebRAGK53ivxF7eHwSccP897IAOb+x2oXpHgQereBf3/G6C9Nt/TH3Rg3ciMdc7cJ0D0KuDbKGClNOjU7zH0MtZBHfESsyBsyB9dBsh1yrYyCl6sJ0G8IY2x6SKhmlR9SL6QZE/Km1HFiKoYwY92G6DaFY0loou24h6bz8chELImFhZduUIzszv1ggXHsmeyUrPk8/LpBLQQVJt6kKHKgf8kr7XncxZtZx/uMaCaZmiqKupann6UfybQauFTGdbv1A/cBmujEYnmy+Ozbfuqx7ZgzjEKQP0231eAyzyXR1LKQD/cfT+foQErLoY/NLyahB49QQkM/rjwdEgtzwI46Nb8n0jYj76clibJN5JtSF6UaE61C53Pq0Id7MowHiZg6YCjCejz4zv7Tg8UX0RPwAXk7F86HV554AAAAASUVORK5CYII='

ALBERT_SCHLOSS_MENU_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAN4AAADeAQAAAAB6HIMaAAAB80lEQVR4nO2YMY4bMQxFn6wBXMrAHsBHkW6QIwW5meYoPsACVGmAg59CsrfJbtIEZrHEFDNi88Chvr6YxKdxnD7PwXfyb0lkAFmiKGs9AFQPR3uCKonRnJ2RfCQgS7KAtT0BKbX54ZCu3UdjpO2FQJ/G9nzLxnEV45LfXwn0T8nyC3bYt6Lj2gMA/TE2QLBRjzfb3n8A2aCIEZD2BHtKidHOtwYwGqMdKaVLQFo0w3BqlqB6WWvxFAxZlZQNL91L9yIgq1NC0kpQZWSrFFE6RTJy0Noi9Sxlq07NRn6QR6RdbSCnUuSzvBCW1oEin5BUWaVIFtInjEbpsv1sZMPhuHbYj0tMBetzo2V1SbKqKQgxO8Fw8NWxoiw1yxE7YWrC0tis7lTAIWTfInV/VhgAn+QRaU+Mdra6lb4BVC+d0o/LC4G+ilVbdX/KbOnThsWr7dMnrMN3HRbgEe9lyKqselE2ZExZcML6hLr++5QC9Sd2TFpK9yI9ToesDjVqbQGyuoxpxX2th+zbx91huUSYxiak3n7Marx0HpedqP72tGY1wGhzozk4+wuBvghZXXuq9DUKMwiqtx/JbbR8a/fU7tfuEYC+Su5QgQ3Ot5/zPR7tc1aD4Niqb9zf7ICzAk6bH5owpx/G8relh7w7pO9J/n9L/gat0o2rzB38FAAAAABJRU5ErkJggg=='
HARD_ROCK_MENU_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAMYAAADGAQAAAACh4MLwAAABkElEQVR4nO2YMW7lMAxEn0wDKeUb/KNQN1vszeQbUeUHZEwKfafa7AJbJCwiuJGmGYyGQ9FF/Hld2ycA/CCAAsAkCzeJuoT0+f3cNnBJjDI5J0wwSZFBtw0opVH79dB1ADDK/sUM/oW8xWnBW3wfg8+Q0eZojHKVlobbDgj22ktVqSpAFSMDt7tOwz8+IEedotfqFj5rt3ufgNvGaPtoO0wAnqUx2nVkuVNTl/oEhSugdkWSO+2TV0ew8LXN4rdggoKlmKmbNGsGv6FwajfJJFO3wNRnEt0kBVJXuIW/7JfFb1qsqF3qK0/S6NaBWTt1pRxSz+G3DbBghzka8DzYgdFS5JtE7bPqI99s9YgM3FYbfdWpFA6ex2/LY7DyTbMm8RsKnwAObiuB8Sy9fr094rxPXEEpOWohgOX/paFbkMNv95wFz8PhfAsmWGR4I91z1vhlwXUwOcvhX83g70j9DadJ10MTypGJ22jXQ3AyCpw5ZmcUrvuBtOZ6hefItw3OUgqjAKYODkn6afn5x/VfyDtOQT2eeL6uywAAAABJRU5ErkJggg=='
MOUSETRAP_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAMYAAADGAQAAAACh4MLwAAABpElEQVR4nO2YMW7dQAxEHz8XcLm6gY9C3SBHMnIz6Sj/AAGo8gMUJsV+BQhgF0lhb2E2Wu00A4qcIWXi/ThvHwDwjQBKAM9QQt+kkcior+d2g5BE/9mIAsAl5Qx5uwFmK8f6WHZPbIHD2iczeD/a89m31vNs+H39ZAb/gPTtqxn8hUgbx5tyf8ngWOmqWbjtZga0421cnWa2zMANPWMbZ7/eJ9AQlOESXZ4UAVFdnjPoG0Nsq6u6lBTQVbNo766kHQZ7I+ib3+0lZ6k316bEMyCU4dpmqbfRCF0FLhVBl6aotxvHCuhunuNmB85lhm96A057s4XzVY+FRvh99ZyBG5I8Q1Jd+lbELPWWUYRrc21FKOept6tPtY3xcvTCHLPlc+6lP+kV1EjmDNyk6psyqgvCk+rz+OnTUi/5hWFhM3AbkQBXOzCH1984zMwa4RmPJTx5LjUzcLv2rGLnWM+FmsUXGmAE0H7h+QN2A9cMe337cyp0vqZBNaznBHm7kGOFvbEXeEYd6wTcUMY1wg2JgyF6U3AD8EQZumxrDl+w739c/4X8BiDGN212wLL4AAAAAElFTkSuQmCC'
PARCEL_YARD_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAMYAAADGAQAAAACh4MLwAAABpUlEQVR4nO2YMY4bMQxFn8wBXGqAHGCOwrlBjmT4YAHko+QGVLkABz+FxlU2QZDCVrGsJLB5oPQ/KRXxeRyXPyTgKwMoAEzNJFMDB8Dz/WwXcEnAsZL9NiAVM9TtApSyAwllu9N3elleTPB5LM+FL/lQ/35ssbyW4B/YHh9rUNsSryb4O5tg6bslx0IWp4o+A9sFHqUUcPp+Db8GRyllnYENndFMLYF67ifwEBSetVm4wi1cQdZp2NSoTWpA4go3NcUk3osFZUXBUu/H1hLK1ua4b83GsaopHEicOsuZDiEonNosMLWcop8iydSyKgE8mUsLWTWGEJOGFuaYQ5BkQdY2zCSrBu0UbHEObBbn3cuqWdjUsraErA3cJOo0/tZvCyz4mHiz7+DHOks/tWA0LFOzQNIsHhI+dDoWw0lsFg+RJIVLomq01Fk8JACGpymwcBsFfD/b853VbwrKJiB5XGMOLYSf1nHWDZinbgD0HTg2fWyyeFx/7hPU7Zmp96xt6TuQ7yH4PZ7vLKAX9XWhCP/xLSb4q3nqNBycqpnuW/n64/qvzC/QH0o2e86FKQAAAABJRU5ErkJggg=='
BIG_CHILL_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAMYAAADGAQAAAACh4MLwAAABkklEQVR4nO2YMW7kMAxFn4YCUtJADpCjcG6wR9qraY6yBwhAlwFk/BTyJE2CBbaYZRE1NszmwdT/X1QTX6/j8k0BfiqAEsASJcqYBAAxS7CFJEsASZJMUlZguwCtXXHho7XrscHe+oMJvl79fO7b7Fe4Pc1HE/y94gNiEm9bHbYOCDrR85fp1h1c7BXYLnBrrbFfgb7/tj/Xo7W2VWA7tanEMqaPSawPBXSKMvCBj0lYgss0ZiF/G0okWZ7GW8PfULLMDbCMMxq8SE/BtRpq0nKSKv9NkgRhGdKYLmlYES1IwHSZBq7pwlUq6xfViUeUYcOSlaJaJxBiFtGChmVYxnQpY9HWYVv7f8L0oYzpo4yHhEnLQE73cNXRqSVLnhMWZBm2gQ/L1dD7+FCFbZ1DwhLLFVvU8RA+5qwzIIro9AKxouHY4tg+va7E2TIDYiWCaayGVtlvi+3eUH0M0f+frX++7pvN27HF8aL+WqGn9znL1V85tiQ3uL09Z427mjVnteNFQNt4ykcTfLPazx3XP1XeASOxTk2qxmvZAAAAAElFTkSuQmCC'
RACKETEER_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAMYAAADGAQAAAACh4MLwAAABiUlEQVR4nO2YMW7rQAxEn0wBKakb5Cj0zQLfbHWU3IAqDawxv6DsKml+YxYhhAWkaQbD5ZDUIn6Ox+UXAP4QQAlg0nSZhJeQMd/P7QIhieO6sk92jqtJyia6BYRpWMZ0SbLEsoluZ9w/b/Z9Xbb3MfgNOb4+EmC+jcHPiDTw2yRO0VyzBbdnnWa8HqBHnaIzBq7pYxL13oJbyaVhGUpMUsb0HtykOidMQhmmoRYewtPQXiSHSV3uWzktUQwnNMppBj4gLAMfSkxjttCtkJBu+KhPjw3LDv52wYd9LyvArmR1TXhsPbjB/VP3jfvy9diA3RJ8NOBWfSGgnI0JeJv75lLuSu7b/tjOav3IDjlFGSpD89PfcPXQDWlImi5pWPUsjT7+ZhoQtSlYUlN6C24VCa7KZk3pDbhdOJZlWVbXPBblDqzsPWbL557FjovjWi21R1947lkZNYqX3fWohSfiN9hNY3Wpk7+9dHu1hi6zZYYkk6YP06DX/AZgSSk2ifN8P7fl7x/XfyH/AJzdRRvj2EVpAAAAAElFTkSuQmCC'
SPIRITLAND_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAN4AAADeAQAAAAB6HIMaAAAB6klEQVR4nO2YMY7rMAxEn0L39A32KPTNgtxMPsq/AV0GkDG/kH+22t3qIyxWSBNPMxiQMyM18eU5b19j8Av+BKIEsAzLUAYEPvWOUY7tDUISgPcFpD6OzSRlQW1vQGsb/oAdWI7N1Dna8kZCP4LH/Wz34Y/nSmtbAULfgt7xB8d98T4n+d2EvgSlDrv9ubcVjg3ANd5I6Dtwb61x3AFLLFngbK2tBdmieRJlDMD1OhUd7NjaurcPLbCAcj9XFvazbfW0vQGWKPfBrozW7sC5UtLBkDQIS/AuSep4HzAqZhnKwKW8BtgkvA/vypJsJbxbxnABJlkypuYl2Q7XmDylS1Xvw0uyzWmzIXWp49LsY1W1nXM7iOEa3qVu6laWLWHSuFS9Eq0k2xsw4Nka0D4egzjXAMZRMB1mpYl5d5hWYNIgqLpll195N3X809CKsnXZlREx/45JuCLbkC6//fctTCqbZZYBzFCY5oCraE9QN3Ulpj5muc0wVe0JGTMgcJm6JEuAolt23R1CGYPrNytZPbY3jtZamxcH02PxxwILca4l23jGXLTpt5ZAKCnrYBCmrrlryQDqZlnAVWaUaPYZr+m3n+Bzpa1AXI9g3uvOrV7NVvMKWVLb1/stUrcrI7pllOy37fcl/7+BfwGEFrm6ajIsPQAAAABJRU5ErkJggg=='
REPUBLIC_HOTEL_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAMYAAADGAQAAAACh4MLwAAABl0lEQVR4nO2YPYocMRBGn0YNG2rAB9ijVN9s2SP5AIbqo8wBDNXhQg2fA/V0Yq8DB54KVohG6koen1R/auLP4375xABfFkAB0IMczhAYAJYl2ExSD1M81pKiAtsFaG1lvN+vBrQr7G35zwR/t+xvL/L2+p5PI/jcMvx+pd/enkfw+1gAwcKmveViAEPsFdhOP7VzAlX8dI4wSXlupRJsYQxneA7P4V3q8iyiW1gPFChgOBhYjfiG5ArrYfngTIxR4UwX9lXw8e37ka2GGmhffzyfDUk5xFAPY7gkyXsRX5gJVJ5YDxiaGb8EW9jULYcnBnZ8a7D1MMkfsZfEsoQvoDiEmqfZ5QqqsMmPOQUMm0VmCbbjvrnkYNNt6/gpkNis3HocnluDzXtYl+fw82cZtlmHAHYca1AjhlzYW2ttAYYvACyQwwvUlpd5/8Fgm6Il9NtagA2FgXWJoYQeUKUOOfusder2cUWx6VZBt+Wx2HJZpe1F2/1Vy88ivczs5T2Bofn4UCVnBcBsr3IIZqyrwNa+3rj+yfILLXRIJPUqXcYAAAAASUVORK5CYII='
CORTEFREDA_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAMYAAADGAQAAAACh4MLwAAABoklEQVR4nO2YvW0jQQyFP2oWUDgLuIArhdvBlXRQSdcBVYoLEMANDcziXTCSAuN8wQU2AxMTDZMPbx9/Zk38PY7TBwn4zsCJ3cxs2Tf2bV6ZmdlWgg2XRL8A7NthW5OUFXRbAMMBg2OFHsu+tlsFtkdm/9XSF/z8un0Rwb8yo19aQo8vI3gfCyBYuB4vv48feaxJF3sFNpQALf15APBRgW1GMvCmmGUrqQRbutLBRw96TBmVNXRLHz2UPnBJTXOI1WBT3Hl60NUS8Cq6KSQNfIAUo8f0Xgm2pEngSkaPAZJGL1QLSqSgS7p/1gJsJ+BYsdVt9QHs24CWNXqvpsEAp8e9uZXQbfbegFmnoWT0Qn4DHzC6HqOhTJ1KkughBT2aYk7VImxTtJZI0ZIyfjuxW1OcE+BYeVsxszJ1et9DZlubA6vGzHq8s/Bj9dEvwMJ1+VSCD0M5148Ab8mYg75SD2lJUzTFmJdldkvwpnj2t9FVxW+PaK8G1zfbWl5treC35zuL5eZnXc/5c7ltY6nA9nxn0dJHj/uCVKIW7Psf139l/gBxlzw1RY/RgwAAAABJRU5ErkJggg=='
IQHOTEL_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAMYAAADGAQAAAACh4MLwAAABm0lEQVR4nO2YsW3kQAxFn5YDbDjqYEvhdnAlHbYzqhR3QIUGRvgXjGwHPsPABbcMzEjCTx5IkfzUIv4ex+ULAX4UQAlg0gB6mGYifTyf7QIuiX25pg98cior5O0CLMsd/LjF9eU+9jv70v4zwTfKZslxexzr0wi+VLqOdQPa0wg+RwMEjW20u72s2n/RxV6B7QLbsizsv6/p4A2OZVnWCmxoRropJNn5rgIzBKVLssQkeowepqAXYcMUA5d0UuFV2CTeR65COR+KsIVJo09CVzJ6VGFL6EE/M2bpdCkr7FM0v7EepjAFYOmjxK4/Z4gpxhvq6GFFaipZokSJpZsC3MrUdJYSnB7jrG+NvCWmkMLSlcxuLeMtOVYaHLdHA/pDetTwlih9wOhBF7jS544okrerosEA5QZbm074+WwfPkQKpStdSY28fdxZAPjApycpwPZ2ZwE9dBbXX9cqvQBuCkvmDQhFavqu+ADLzRSjRw1P/qG0Hq3H60rb788h+BSnJ5csmYZk9KiyTxPA0i1dEl1QpE+Xn39c/6T8AVOJRghHuXccAAAAAElFTkSuQmCC'
MELIA_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAPYAAAD2AQAAAADNaUdlAAACVElEQVR4nO2ZQYrcQAxFX00ZelkNc4A5ivpmQ46UG5SPMgcIyMsBmZ+Fyh3IommSkO6CEb2wWwt/q76kL7mIW7a/3HTDl//v/MgBqgQEROu0TstjsXg0vjvwm6SqLnVJ1S2waKqS/PnxL0DBgNJ8f/1O63vrS8B2rj8ej+9+vz4uCwac/CHP/zP/cr0qzfdXYP0sthf7T8//V/x3qno00XpeTML/o/64/fYD5qg/wzqty5Ejt2jj3wnwu0XrGfPApJ4nkq8wAX6JjLZDk9ykLvWaveDR+O7A3+VUJ0jaW94Cc/DfTZLcqhQYICegus3AnxeglLLAXkr1NVoHTs7+1vdyeQp8Ny0JH6MQdY7I0zQHf7J5udXMXB/iLdNhBvw9Ws/gR+vXzK1u0Z6f/2TmglUn8dejnc3Cn4z8r5qDaUiIGfC7BVbVr0JidAT1afCn8pGy8kcbjYAJ+J9+K29atgtYVWcrC1S3eBp8N0xStNF/r7OA3Gg9JuDPC3ByFmC7APsZmmBVjgDPgO+mJe3HKUjVCYAhh2aI/7o0LVthK/t56J8AWJ8E323LyEfrmbxHF+i0KeI/9Bs5sA/905P8c8zv6lnzD+Vz8H8a/cN125lbxBzBYBL9kOZW1Y9C1PMV5uCPA1QN5VmPQTIn4qfH/wImie2yv/X9vAbrZ7mcnMjd4hPgu21yG7IHy0J63T/MML8f+9vtvcZaP4p8pWlfiMWWeDy+e/3tW2zvYPvZUogCn2WW/YPy+1Fq5uqjqM7An+v+GZoSfECuU2aoP+Xr++lD/T8B6iIpTJGI5+8AAAAASUVORK5CYII='

EVENT_QR = [
    ('dinner at the lighterman', ('https://www.thelighterman.co.uk/', LIGHTERMAN_QR_B64)),
    ('dinner at albert schloss', ('https://www.albertsschloss.com/menu/?location=london', ALBERT_SCHLOSS_MENU_QR_B64)),
    ('dinner at hard rock cafe london', ('https://cafe.hardrock.com/menu.aspx', HARD_ROCK_MENU_QR_B64)),
    ('need to be at mousetrap', ('https://stmartinstheatre.co.uk/', MOUSETRAP_QR_B64)),
]

def event_qr_for(name):
    n = name.lower()
    for keyword, val in EVENT_QR:
        if keyword in n:
            return val
    return None

BAR_QR = {
    'The Parcel Yard': PARCEL_YARD_QR_B64,
    'Big Chill Bar': BIG_CHILL_QR_B64,
    'The Racketeer': RACKETEER_QR_B64,
    "Spiritland King's Cross": SPIRITLAND_QR_B64,
}

HOTEL_QR = {
    'The Republic Hotel': REPUBLIC_HOTEL_QR_B64,
    'Hotel Borgo di Cortefreda Relais': CORTEFREDA_QR_B64,
    'iQ Hotel Milano': IQHOTEL_QR_B64,
    'The Level at Melia White House': MELIA_QR_B64,
}

TRAVEL_DOCS_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAN4AAADeAQAAAAB6HIMaAAAB8klEQVR4nO2YQWrlQAxEX/9uyLINc4AcRYY5QI4UcqS5QfsoOcBAe/lBpmYhO2QxIbMZokUaL2xrUxSlUqmL+PAct49r8F38rIgmQJW8S9McvAff5hnRmqQq1WneR9WIT82EaG9AKSv7el9o+7PvawP20r4Q0D8U60R6adhR1hSA/nLa9bLBVrBjgT7a1wH6FK2gYcejYPv5e6mvK13sCdHeYCulAA+va9ufwYCjlLIkRNsIv9q5/5gNjsdf62JhYfmmA5oGVKlOqoam1etPPgdD83o0YlKA0UfN6LdI0rSqUTXoJ7eaRk/JbUwxcHCsXiQn5pY6CTfwrqoRyHOipQ/HpOF9+AlYaVNNRBppgNWTZxLrlsiKdDlEx6V1MPqId3+n25SJkWj/UG9E3NR+Owl4dPmpW3MspRJugAfmSOBwLDS2Y0mYatA8faBK3s81J6tuT24dO5at7c+llPuyPUgpN53g1moskrE/auTNCdOqhmNgdUZOUJ05p8MNuC80oA/vL3SVUo4Fva4ZlRBnnsYLpkiMSXMCxO6g4V1XWsir2yviRrsNx/Lm22lX9LK4Vgq2PSO3b0U7Fo6FUtZjQdPanrDL3u5qqL6toP3pYT6VPpsn3dAlvVshrz09Y6q5PGEiyfuIXvOulLot3zf5/634B7IimfqVQm6jAAAAAElFTkSuQmCC'
CAR_DOCS_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAN4AAADeAQAAAAB6HIMaAAAB9UlEQVR4nO2YMW7kMAxFn4YCUsrAHiBHkW+wRwr2ZpyjzAEC0OUAMv4W0qQbZJvFsAjhwjabB+KJolTE0zgvz3Pwk/wuiQLA5KM5TaOJNuvdRzraC3RJQD12jvIWcOwmKRLW9gKUsgMWSM6x05yj1BcCPY369Xb/5fXz43wPjv2FQP9I+zageQ3O96ivA/qWVlPaAoVRsM+dJo6EtBe4llKgW3SL/hYdOEspW0JatMJNAiQfbf3K18FQ9NHcoktu0RUMmMApaVEwW64CRTc5TSPj7oDkU1rJTT6aLJh/ctJOb0fzwbLCgtGSmjCaA4pu0WmumGNDTto+mh6oGrBqm9PbwAKaFqo0mptE6toypgOBSSYlNUFugclZ9mJS1lV2AWh+37Dbh4IK53a9v/tLgZ7GNOGr30pSdJOS9tvAJMkBmubnPPJkpH1wjiaTSz7os8L5aC/QB+hWgHMDsKByPbec3i4Zpr00l5R5ToA+miSf3s4npbcXjo8BFSroViqcG2WDY89owoyAtpYYzJk8pQkBrN12Tl+KPieHfLSXdVdzlHtZbaHCoI8joQkVKHSaamylqQBcC1j8zkeLoq/jub4mxrkR5zQBgPaHY68wuNptH/M+JB0tiq450K7LBB+Pw1q+2j56wjqdrd6VdXcoPzf5/y35F9YVsOVd3wvZAAAAAElFTkSuQmCC'
ETA_DOCS_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAZoAAAGaAQAAAAAefbjOAAADCklEQVR4nO2cwW3jMBBF36wE+EgDKcCliJ1tTduBWYoLCCAeDUj4eyApK7klDiTHHh50kPzgIUxwZv6nbOLLI/35OgMOOeSQQw455NBzQlZH327nHtIRSNYDuX0g7hKeQ9tDgyRphLIs0hEYRmDQBNBJkvQR2i48h7aHctsAhnE2i+FqFnPPbd9Y7yC/ZE4OfQfqP99IJwHMKJ0mgNkY/v3ANzn0O6DPK0IARniH4WJAeO9F3is8h3aDgqQzANmMYexkduwkXQ6yCEilotgnPIe2hpKZmR3BIp1KrzGMYLE8n0ursVd4Dm2dNdZSdriayLC+8FHrfvA5OXQPROkqa/fZlV9eZ0DnIDGUe13JKaUHPT/4nBy6B2orYmyVwqJMlMs51HssooSviJeAgmQx99TyMkyQTpLFfKgZYxhnryNeAKqJYLUfjFByxXIpD6Cr2cX3iGeGatYg1Lzw4VknSVPNH7fhK+L5IenSU3IFq3pybtYWsBK6f8ecHLqn+zTChMgGMPeCCZHfJpJ1IkUwWJrQB5+TQ/dDOjOb2UliuBxkMZtBuFr1PlsdYXGX8Bza3tcYLuUYBMBsAlVzg/zWxOswbh+eQ5tDi0LVSohST44AoRaVteHwXuMloFUPUW+EqfShpc2ojWfVMX1FPD/UhGluykTbD6oAMdFaD1exXweyCFjMZma3czKa0DkfVGrMImvuEp5D+9QRVY0quaJ6HcXwqGKm+xovBrVDt1WcokiYKzHTfY1XgFZueE0T4WaOr10P3Nd4Deizr9FqzMXzWpqQYTlH4Svi+aG2H0zYX0lmx/a8vLkhqRzA3Cc8h3bwNcroJiUDpdgjcjdVHbMJl+5rvAy0FA437QHChMXQfI1acu4SnkPbQ4vVnU6LJJV7IB9EsmZ87RWeQztD6Qhmp6uRTlcre8Rw6bH4EOE5tCVUXFCo4lRtPKk15k9+k0MPDYVqbpTtIYar3bJGNbnGrr329Uvm5NB3oKZHlLEctaXT6n2NtcbtesSTQ+b/TOaQQw455JBDDn0T+g/R5zGFDCexrAAAAABJRU5ErkJggg=='
INSURANCE_DOCS_QR_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAcIAAAHCAQAAAABUY/ToAAADiklEQVR4nO2cXYqkShBGT1yFfkyhF3CXku5smCXdHehSZgED+tigfPOQP6b2cAeGLrpsIh6KstKDJgQRkV9Glom/s/mfvwTBSSeddNJJJ5108vlIy9ZjZn0ZW82Y029mNq7lrvGT39bJpySjJGkBTQCzmQGdbASkpRPQSZJ0Jj/jbZ18SnKt8SW8mX1bgHnYDdgNwpsBnKLUPefp5MeT/eXa4rIj2HriMiDYe+YRxPpRz3Tyy5OdbKSTjUFiHsC+LWDjI5/p5I3JEoeCIEWa9XVjNhDrAPAiIwgDaAXJe83TyYeTs5mZDeXXuORgRFwA1h5gT8uyj3qmk1+ERGcDOmkKZfkVF5C0Xe/TdK95Ovk4MvkGUSox5xhYOqVlfZSUFv0Elct7zdPJx5HFhxaySDSFjeIq+ZuURreGcB9yslqTxmIKPKCJTm3MgSpDdp7LnLzYkctSFRS15TQ2BSl5U0w6NbU8ch9y8rC0tk8eEn8YsL4K2C3Ji/lbSWPzABanz3pbJ5+XNBvA7F8l9ymDXS6K5mE3opR0x1xd33GeTj6CrLlsI5XOqYjWRpPBCHUUz2VOXu2kCm15+RWrIDQV92n8ytf2Tp6siUMTVRAqrlJcKkuO+Rb3ISdbyx4BZfV+UoVK6xDFkcLmuczJix1xiJTQSlZrPqR66XHIyXdWFMatVjx16KRY51sWr6mdvNpRUzeXsTa/Jo2xpDuPQ06+t9rHuBuEn71BtwneTKyvaUCzAVF7b/HoILrXPJ18HFniUFCrBdWN1yaDTWnY45CTVzvVQ2oTGkCzD+v6kJP/R9pIp3SgLFXS0EQfG8lHOvR92L2P0cmLNdEnbdSHus1RZOtDPSoSkschJxvLLrFAsxprFmd1ryP1xwb3ISev1tRD01FEp8V8VwTspa78vQfNyXd2Wpd1yYfSQFqc1T00wGtqJ39jTQ+aAAw6WVaKXmo3GhAnMMJWDpnda55OPpo8/vfjOFAmLeWA/Tzk3z7ymU5+FbLtp05d1LV7MaWspqdITcXtuczJYiW2rAPE/8AIP03zsMgALC4o5bc5CUMltd1snk4+jrz+74dYX2SEfN5e6eQ95RK8J9/JP5HzANKPeqw+bMDaY1nK7svO2VO8rZNPQL6rh1T6qU+7HkeTrPcPOXm1Zn+Vcrq17Hq0mlGWIQHXh5w8menP9/zW/D/OnXTSSSeddNLJL0L+Arn3cypOrt8/AAAAAElFTkSuQmCC'

WALK_ROUTES = [
    ('dinner at albert schloss', {
        'from': "Albert's Schloss",
        'to': "St Martin's Theatre",
        'to_w3w': 'trains.areas.nights',
        'time': '8 min',
        'distance': '0.3 mile',
        'via': 'Shaftesbury Ave',
    }),
    ('dinner at the lighterman', {
        'from': "The Level at Meliá White House",
        'to': "The Lighterman",
        'to_w3w': 'guides.riots.trader',
        'time': '31 min',
        'distance': '1.4 miles',
        'via': 'Euston Rd',
    }),
    ('arrive at the level', {
        'from': "Great Portland Street Station",
        'to': "The Level at Meliá White House",
        'to_w3w': 'baked.belly.neck',
        'time': '2 min',
        'distance': '0.1 mile',
        'via': 'Albany St',
    }),
]

def walk_route_for(name):
    n = name.lower()
    for keyword, data in WALK_ROUTES:
        if keyword in n:
            return data
    return None

def walk_map_svg(route):
    return (
        f'<svg class="walk-map" viewBox="0 0 320 180" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Walking route from {esc(route["from"])} to {esc(route["to"])}">'
        f'<rect x="0" y="0" width="320" height="180" fill="#eef2e9"/>'
        f'<path d="M42,138 C110,58 214,124 278,42" fill="none" stroke="#1f3864" stroke-width="3" '
        f'stroke-dasharray="7,6" stroke-linecap="round"/>'
        f'<circle cx="42" cy="138" r="8" fill="#c94b3f"/>'
        f'<circle cx="278" cy="42" r="8" fill="#2e6b3e"/>'
        f'<text x="42" y="160" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#262626" text-anchor="middle">{esc(route["from"])}</text>'
        f'<text x="278" y="26" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="#262626" text-anchor="middle">{esc(route["to"])}</text>'
        f'<text x="160" y="94" font-family="Segoe UI, Arial, sans-serif" font-size="20" text-anchor="middle">&#128694;</text>'
        f'</svg>'
    )

def walk_route_html(route):
    svg = walk_map_svg(route)
    text = (
        f'<div class="walk-info">'
        f'<div class="walk-time">&#128694; {esc(route["time"])} walk</div>'
        f'<div class="walk-dist">{esc(route["distance"])} via {esc(route["via"])}</div>'
        f'<div class="walk-note">To {esc(route["to"])} (///{esc(route["to_w3w"])})</div>'
        f'</div>'
    )
    return f'<div class="walk-map-wrap">{svg}{text}</div>'

TRAVEL_OPTIONS = [
    ('dinner at the lighterman', [
        ('A. Uber', 'approx. £8-£13 (UberX, off-peak; more at busy times or in traffic)'),
        ("B. Tube", "Circle/Hammersmith &amp; City/Metropolitan line to King's Cross St Pancras, then ~5 min walk - about 13 min door to door, approx. £3.00 pay-as-you-go"),
    ]),
    ('take the tube from heathrow', [
        ('A. Uber', 'approx. £70-£95 for an UberXL (seats up to 6, fits 4 people + luggage) - book via the app once through arrivals; ~45-60 min depending on traffic, more at peak times'),
        ('B. Black cab', 'approx. £75-£120 metered from the official taxi rank (fits 4 + luggage), or a pre-booked fixed fare from about £45-£70 - ~45-70 min depending on traffic'),
        ('C. Private transfer', 'a pre-booked executive MPV/people-carrier (e.g. Blackberry Cars, Blacklane) runs from about £75-£90 fixed price for 4 people + luggage, with a driver meeting you in the arrivals hall - no queuing, good after a long flight'),
        ('D. Tube (booked plan)', 'Elizabeth line from Terminal 5 to Paddington, then Hammersmith &amp; City/Circle line to Great Portland Street, then ~2-3 min walk - about 50 min total, approx. £15.50pp (~£62 for 4) but every bag has to come on the train'),
    ]),
]

def travel_options_for(name):
    n = name.lower()
    for keyword, opts in TRAVEL_OPTIONS:
        if keyword in n:
            return opts
    return None

def travel_options_html(opts):
    items = ''.join(
        f'<div class="travel-opt"><span class="travel-opt-label">{esc(label)}</span> {detail}</div>'
        for label, detail in opts
    )
    return f'<div class="travel-opts"><div class="travel-opts-title">Other ways to get there:</div>{items}</div>'

EVENT_NOTES = [
    ('dinner at the lighterman', "If we're early, we could grab a quick Gin &amp; Pepsi downstairs first &#128522;"),
]

def event_note_for(name):
    n = name.lower()
    for keyword, note in EVENT_NOTES:
        if keyword in n:
            return note
    return None

DIRECTIONS = [
    ('drive from civitavecchia to talamone', 'https://www.google.com/maps/dir/?api=1&origin=Via%2016%20Settembre%2046%2C%20Civitavecchia%2C%20Italy&destination=Strada%20Vicinale%20delle%20Casacce%2C%2065%2C%2058010%20Talamone%2C%20Orbetello%2C%20Italy&travelmode=driving'),
    ('lunch option: agriturismo buratta', 'https://www.google.com/maps/dir/?api=1&destination=Strada%20Vicinale%20delle%20Casacce%2C%2065%2C%2058010%20Talamone%2C%20Orbetello%2C%20Italy&travelmode=driving'),
    ('drive from talamone to tuscany', 'https://www.google.com/maps/dir/?api=1&origin=Strada%20Vicinale%20delle%20Casacce%2C%2065%2C%2058010%20Talamone%2C%20Orbetello%2C%20Italy&destination=Via%20Roma%20191%2C%2050028%20Tavarnelle%20Val%20di%20Pesa%2C%20Italy&travelmode=driving'),
    ('potential breakfast/coffee: il caff', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%2C%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Via%20Roma%20121%2C%2050028%20Tavarnelle%20Val%20di%20Pesa%2C%20Italy&travelmode=driving'),
    ('potential pastries/coffee: pasticceria la golosa', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%2C%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Via%20Palazzuolo%2C%2050028%20Tavarnelle%20Val%20di%20Pesa%2C%20Italy&travelmode=driving'),
    ('potential restaurant: triocco', "https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%2C%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Via%20Vittorio%20Veneto%2048%2C%2050021%20Barberino%20Val%20d%27Elsa%2C%20Barberino%20Tavarnelle%2C%20Italy&travelmode=driving"),
    ('potential victoria and albert museum', 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Cromwell%20Road%2C%20London%20SW7%202RL%2C%20UK&travelmode=driving'),
    ("potential early lunch at harry's knightsbridge", "https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=27-31%20Basil%20Street%2C%20Knightsbridge%2C%20London%20SW3%201BB%2C%20England&travelmode=driving"),
    ('visit waterstones piccadilly', 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=203-206%20Piccadilly%2C%20London%20W1J%209HD%2C%20UK&travelmode=driving'),
    ('check out of hotel borgo di cortefreda relais & drive to milan', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Via%20Giovanni%20Battista%20Pirelli%2C%205%2C%2020124%20Milan%2C%20Italy&travelmode=driving'),
    ('return hire car - mercedes vito', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Giovanni%20Battista%20Pirelli%2C%205%2C%2020124%20Milan%2C%20Italy&destination=Milan%20Linate%20Airport&travelmode=driving'),
    ('drive to lake como', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Via%20Besana%201%2C%2022012%20Cernobbio%2C%20Italy&travelmode=driving'),
    ('check out of hotel borgo di cortefreda relais & drive to bologna', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Bologna%2C%20Italy&travelmode=driving'),
    ('drive from bologna to como', 'https://www.google.com/maps/dir/?api=1&origin=Bologna%2C%20Italy&destination=Como%2C%20Italy&travelmode=driving'),
    ('drive from como to cernobbio', 'https://www.google.com/maps/dir/?api=1&origin=Piazza%20Alcide%20de%20Gasperi%204%2C%20Como%2C%20Italy&destination=Via%20Besana%201%2C%2022012%20Cernobbio%2C%20Italy&travelmode=driving'),
    ('drive from lake como to milan', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Besana%201%2C%2022012%20Cernobbio%2C%20Italy&destination=Via%20Giovanni%20Battista%20Pirelli%2C%205%2C%2020124%20Milan%2C%20Italy&travelmode=driving'),
    ('drive to maranello', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Via%20Dino%20Ferrari%2043%2C%2041053%20Maranello%2C%20Italy&travelmode=driving'),
    ('drive from maranello to milan', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Dino%20Ferrari%2043%2C%2041053%20Maranello%2C%20Italy&destination=Via%20Giovanni%20Battista%20Pirelli%2C%205%2C%2020124%20Milan%2C%20Italy&travelmode=driving'),
    ('drive to venice', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Piazzale%20Roma%2C%20Venice%2C%20Italy&travelmode=driving'),
    ('drive from venice to milan', 'https://www.google.com/maps/dir/?api=1&origin=Piazzale%20Roma%2C%20Venice%2C%20Italy&destination=Via%20Giovanni%20Battista%20Pirelli%2C%205%2C%2020124%20Milan%2C%20Italy&travelmode=driving'),
    ('arrive venice - park at tronchetto', 'https://www.google.com/maps/search/?api=1&query=Tronchetto+Parking+Venice'),
    ('check out of hotel borgo di cortefreda relais & drive to pisa', 'https://www.google.com/maps/dir/?api=1&origin=Via%20Roma%20191%2C%2050028%20Tavarnelle%20Val%20Di%20Pesa%2C%20Italy&destination=Piazza%20dei%20Miracoli%2C%20Pisa%2C%20Italy&travelmode=driving'),
    ('drive from pisa to como', 'https://www.google.com/maps/dir/?api=1&origin=Piazza%20dei%20Miracoli%2C%20Pisa%2C%20Italy&destination=Via%20Besana%201%2C%2022012%20Cernobbio%2C%20Italy&travelmode=driving'),
]

WEBLINKS_APPEND = [
    ('agriturismo buratta', 'https://www.tripadvisor.co.nz/Restaurant_Review-g194929-d1894984-Reviews-Agriturismo_Buratta-Talamone_Orbetello_Province_of_Grosseto_Tuscany.html'),
    ('il caff', 'https://www.tripadvisor.com/Restaurant_Review-g670654-d3612860-Reviews-Caffe_Degli_Amici-Tavarnelle_Val_di_Pesa_Barberino_Tavarnellle_Tuscany.html'),
    ('la golosa', 'https://www.tripadvisor.com/Restaurant_Review-g670654-d3418380-Reviews-Pasticceria_La_Golosa-Tavarnelle_Val_di_Pesa_Barberino_Tavarnellle_Tuscany.html'),
    ('triocco', 'https://www.tripadvisor.com/Restaurant_Review-g616195-d14128899-Reviews-Triocco-Barberino_Val_d_Elsa_Barberino_Tavarnelle_Tuscany.html'),
    ('wandering around oxford street', 'https://www.oxfordstreet.co.uk/'),
    ('visit waterstones piccadilly', 'https://www.waterstones.com/bookshops/piccadilly'),
    ('dinner at britannia restaurant', 'https://www.cunard.com/en-us/cruise-ships/queen-victoria/9'),
    ('pristine sistine', 'https://www.walksofitaly.com/vatican-tours/pristine-sistine-chapel-tour/'),
    ("colosseum arena floor & vip caesar's palace", 'https://www.walksofitaly.com/rome-tours/rome-caesars-palace-tour-colosseum/'),
    ('marseille and the little train', 'https://www.cunard.com/en-us/shore-excursions'),
    ('monaco and the old town', 'https://www.cunard.com/en-us/shore-excursions'),
    ('discover genoa shore excursion', 'https://www.cunard.com/en-us/shore-excursions'),
    ('easy pisa', 'https://www.cunard.com/en-us/shore-excursions'),
    ('combo: tower of london', 'https://www.headout.com/tower-of-london-tickets/'),
    ('dinner in milan', 'https://www.tripadvisor.com/Restaurants-g187849-Milan_Lombardy.html'),
    ('arrive milan - check-in at iq hotel milano', 'https://www.iqhotelmilano.it/'),
    ("lunch at harry's bar, cernobbio", 'https://www.harrysbarcernobbio.it/en/'),
    ('visit museo ferrari, maranello', 'https://www.ferrari.com/en-EN/museums/ferrari-maranello'),
    ('arrive venice - park at tronchetto', 'https://www.veneziaunica.it/en'),
    ('lunch in venice', 'https://www.tripadvisor.com/Restaurants-g187870-Venice_Veneto.html'),
    ('aroma specialty coffee', 'https://www.ilpiaceredelcaffe.it/'),
    ('arrive como - como-brunate funicular', 'https://www.funicolarecomo.it/'),
    ('gelato with a view at il balcone sul lago', 'https://www.facebook.com/Ilbalconesullago/'),
    ('nightcap drinks at liquido rooftop bar', 'https://www.tripadvisor.com/Restaurant_Review-g187849-d19184966-Reviews-Liquido_Rooftop_Bar-Milan_Lombardy.html'),
    ('pre-dinner drinks - terrazza montemartini', 'http://www.palazzomontemartini.com/'),
    ('lunch at target restaurant', 'https://www.tripadvisor.com/Restaurant_Review-g187791-d967428-Reviews-Target-Rome_Lazio.html'),
    ('skip-the-line leaning tower of pisa', 'https://www.viator.com/tours/Pisa/Skip-the-Line-Leaning-Tower-of-Pisa/d520-36478P5'),
]
WEBLINKS.extend(WEBLINKS_APPEND)

EVENT_PHOTOS = [
    ('nightcap drinks at liquido rooftop bar', 'https://www.iqhotelmilano.it/static/673921934cef5b847413f341bc82c433/b0c6e/0de29cf2-6818-490c-ba2f-1dd8aaa4f4ee.jpg'),
    ('dinner at albert schloss', 'https://assets.albertsschloss.com/content/uploads/2024/01/Schloss-London-Header-1400x788.jpg'),
    ('dinner at the lighterman', 'http://static1.squarespace.com/static/61cc647e2e2bca2f4e1ae1da/t/61cc64ad2e2bca2f4e1ae5e8/1745590094055/WC%2BHeader.png?format=1500w'),
    ('arrive at the level', 'https://commons.wikimedia.org/wiki/Special:FilePath/Great%20Portland%20Street%20underground%20station%20-%20geograph.org.uk%20-%201522059.jpg'),
]

def event_photo_for(name):
    n = name.lower()
    for keyword, url in EVENT_PHOTOS:
        if keyword in n:
            return url
    return None

MENU_LINKS = [
    ('lighterman', 'https://www.thelighterman.co.uk/menus'),
    ('hard rock', 'https://cafe.hardrock.com/menu.aspx'),
    ('albert schloss', 'https://www.albertsschloss.com/menu/?location=london'),
    ("lunch at harry's bar, cernobbio", 'https://www.harrysbarcernobbio.it/en/menu-online/'),
    ('potential restaurant: triocco', 'https://www.borghiditoscana.net/en/restaurant-pizzeria-triocco-in-barberino-val-delsa-florence/il-menu-del-ristorante-triocco-barberino-val-delsa-2/'),
    ('lunch option: agriturismo buratta', 'https://restaurantguru.com/Agriturismo-Buratta-Fonteblanda/menu'),
    ('potential breakfast/coffee: il caff', 'https://weur-cdn.piatti.menu/storage/media/companies_menu_pdf/112559238/il-caffe-degli-amici-tavarnelle-val-di-pesa-piatti.pdf'),
    ('nightcap drinks at liquido rooftop bar', 'https://www.iqhotelmilano.it/static/c1cb719b5ae20721fbd597b4fa1f23c9/Menu%20Beverage%20+%20Food_Liquido.pdf.pdf'),
    ("potential early lunch at harry's knightsbridge", 'https://harrysdolcevita.com/harrys-menu/'),
]

def menu_for(name):
    n = name.lower()
    for keyword, url in MENU_LINKS:
        if keyword in n:
            return url
    return None

EVENT_BOOKING_LINKS = [
    ('dinner at hard rock cafe london', ('Manage on OpenTable', 'https://opentable.com/l/GyRGOnW7p')),
]

def booking_link_for(name):
    n = name.lower()
    for keyword, link in EVENT_BOOKING_LINKS:
        if keyword in n:
            return link
    return None

EVENT_FACTS = [
    ('waterstones piccadilly', "This shop opened in 1936 as Simpsons of Piccadilly, then Britain's largest menswear store, designed by modernist architect Joseph Emberton. Waterstones took it over in 1999 and it's now Europe's largest bookshop, with over 8 miles of shelving across 6 floors.",
     'Wikipedia', 'https://en.wikipedia.org/wiki/Simpsons_of_Piccadilly'),
    ('albert schloss', "Albert's Schloss is one of a small chain of Alpine-Bavarian bier hall/cabaret venues from The New World Trading Company - the original opened in Manchester in 2017, with the Soho branch spread across several floors of a former Soho building near Piccadilly Circus.",
     "Albert's Schloss", 'https://www.albertsschloss.com/location/london/'),
    ('six the musical', "SIX started life as a low-budget student production at Cambridge University in 2017, written by two undergraduates, Toby Marlow and Lucy Moss, who were still in their early twenties. It transferred to the West End in 2019 and has since played on Broadway and around the world.",
     'Wikipedia', 'https://en.wikipedia.org/wiki/Six_(musical)'),
    ("harry's knightsbridge", "Harry's Bar-style venues take their name and dolce vita aesthetic from the original Harry's Bar in Venice, opened in 1931 - said to be where the Bellini cocktail and carpaccio were both invented.",
     'Wikipedia', "https://en.wikipedia.org/wiki/Harry's_Bar"),
]

def event_fact_for(name):
    n = name.lower()
    for keyword, text, source_label, source_url in EVENT_FACTS:
        if keyword in n:
            source_html = f' <span class="fun-fact-source">&mdash; <a href="{source_url}" target="_blank">{esc(source_label)}</a></span>' if source_url else ''
            return f'<div class="place-fact">&#128161; {text}{source_html}</div>'
    return None

def directions_for(name):
    n = name.lower()
    for keyword, url in DIRECTIONS:
        if keyword in n:
            return url
    return None

HRC_LOGO_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 140">
<circle cx="70" cy="70" r="64" fill="#f5c451" stroke="#8a3b23" stroke-width="7"/>
<circle cx="70" cy="70" r="64" fill="none" stroke="#ffffff" stroke-width="2"/>
<text x="70" y="63" font-family="Georgia, 'Times New Roman', serif" font-weight="bold" font-style="italic" font-size="21" fill="#8a3b23" text-anchor="middle">Hard Rock</text>
<text x="70" y="88" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="17" letter-spacing="1" fill="#8a3b23" text-anchor="middle">CAFE</text>
<text x="70" y="112" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="12" letter-spacing="1.5" fill="#8a3b23" text-anchor="middle">LONDON</text>
</svg>'''
HRC_LOGO_B64 = base64.b64encode(HRC_LOGO_SVG.encode('utf-8')).decode('ascii')

def logo_for(name):
    n = name.lower()
    if 'hard rock' in n:
        return f'data:image/svg+xml;base64,{HRC_LOGO_B64}'
    return None

SHOPLISTS = {
    'wandering around oxford street': [
        ('Primark', '14-28 Oxford Street, London W1D 1AR', 'https://www.google.com/maps/search/?api=1&query=Primark+14-28+Oxford+Street+London', 'https://www.primark.com/en-gb/stores/london/14-28-oxford-street'),
        ('Uniqlo', '311 Oxford Street, London W1C 2HP', 'https://www.google.com/maps/search/?api=1&query=Uniqlo+311+Oxford+Street+London', 'https://www.uniqlo.com/uk/en/'),
        ('Selfridges', '400 Oxford Street, London W1A 1AB', 'https://www.google.com/maps/search/?api=1&query=Selfridges+400+Oxford+Street+London', 'https://www.selfridges.com/'),
        ('John Lewis', '300 Oxford Street, London W1C 1DX', 'https://www.google.com/maps/search/?api=1&query=John+Lewis+300+Oxford+Street+London', 'https://www.johnlewis.com/our-shops/oxford-street'),
        ('Hamleys', '188-196 Regent Street, London W1B 5BT', 'https://www.google.com/maps/search/?api=1&query=Hamleys+188-196+Regent+Street+London', 'https://www.hamleys.com/'),
        ('Nike Town London', '236 Oxford Street, London W1C 1DE', 'https://www.google.com/maps/search/?api=1&query=Nike+Town+236+Oxford+Street+London', 'https://www.nike.com/gb/retail/s/niketown-london'),
        ('Adidas Flagship Store', '425 Oxford Street, London W1C 2PG', 'https://www.google.com/maps/search/?api=1&query=Adidas+425+Oxford+Street+London', 'https://www.adidas.co.uk/stores/london-oxford-street-425/9990043889'),
        ('Zara Oxford Street', '460-490 Oxford Street, London W1C 1AT', 'https://www.google.com/maps/search/?api=1&query=Zara+460-490+Oxford+Street+London', 'https://www.zara.com/uk/en/stores-locator/zara-london-oxford-s1377'),
        ('HMV', '363 Oxford Street, London W1C 2LA', 'https://www.google.com/maps/search/?api=1&query=HMV+363+Oxford+Street+London', 'https://hmv.com/'),
        ('Liberty London', 'Great Marlborough St / Regent Street, London W1B 5AH', 'https://www.google.com/maps/search/?api=1&query=Liberty+London+Regent+Street', 'https://www.libertylondon.com/'),
    ],
}

def shoplist_for(name):
    n = name.lower()
    for keyword, shops in SHOPLISTS.items():
        if keyword in n:
            return shops
    return None

def shoplist_html(shops):
    items = ''.join(
        f'<div class="shop-item"><span class="shop-name">{esc(name)}</span>'
        f'<a class="pill" href="{esc(addr_url)}" target="_blank">Address</a>'
        f'<a class="pill pill-website" href="{esc(web_url)}" target="_blank">Website</a>'
        f'<span class="shop-addr-text">{esc(address)}</span></div>'
        for name, address, addr_url, web_url in shops
    )
    return f'<div class="shop-list"><div class="shop-list-title">Potential shops to look at:</div>{items}</div>'

INSTAGRAM = [
    ('hard rock', 'https://www.instagram.com/hardrockcafelondon/'),
    ('lighterman', 'https://www.instagram.com/thelightermankx/'),
    ('albert schloss', 'https://www.instagram.com/albertsschloss/'),
    ('mousetrap', None),
    ('six the musical', 'https://www.instagram.com/sixthemusical/'),
    ('victoria and albert museum', 'https://instagram.com/vamuseum'),
    ("harry's knightsbridge", None),
    ('wandering around oxford street', 'https://www.instagram.com/oxfordstreetw1/'),
    ('drive from civitavecchia', None),
    ('lunch option: agriturismo buratta', None),
    ('drive from talamone', None),
    ('potential breakfast/coffee: il caff', 'https://www.instagram.com/ilcaffedegliamici/'),
    ('potential pastries/coffee: pasticceria la golosa', None),
    ('potential restaurant: triocco', 'https://www.instagram.com/triocco/'),
    ('visit waterstones piccadilly', 'https://www.instagram.com/piccadillywaterstones/'),
    ('dinner at britannia restaurant', 'https://www.instagram.com/cunardline/'),
    ('rhubarb gin & pepsi max at the commodore club', 'https://www.instagram.com/cunardline/'),
    ('pristine sistine', 'https://www.instagram.com/walksofitaly/'),
    ("colosseum arena floor & vip caesar's palace", 'https://www.instagram.com/walksofitaly/'),
    ('marseille and the little train', 'https://www.instagram.com/cunardline/'),
    ('monaco and the old town', 'https://www.instagram.com/cunardline/'),
    ('discover genoa shore excursion', 'https://www.instagram.com/cunardline/'),
    ('easy pisa', 'https://www.instagram.com/cunardline/'),
    ('combo: tower of london', 'https://www.instagram.com/headout/'),
    ('arrive milan - check-in at iq hotel milano', 'https://www.instagram.com/iqhotel_milano/'),
    ("lunch at harry's bar, cernobbio", 'https://www.instagram.com/harrysbarcernobbio/'),
    ('visit museo ferrari, maranello', 'https://www.instagram.com/museiferrari/'),
    ('arrive venice - park at tronchetto', 'https://www.instagram.com/veneziaunica/'),
    ('aroma specialty coffee', 'https://www.instagram.com/aromacoffeelove/'),
]

def instagram_for(name):
    n = name.lower()
    for keyword, url in INSTAGRAM:
        if keyword in n and url:
            return url
    return None

WHERE_FIXUPS = {
    'marseille france': 'Marseille, France',
    'sea day': 'At Sea',
    'arrival in rome': 'Rome',
    'air travel': None,
    'home': None,
}

WHERE_BY_DAYNUM = {}
for t in travel_json:
    try:
        daynum = int(t['date'].split('-')[2])
    except (KeyError, ValueError, IndexError):
        continue
    where = (t.get('where') or '').strip()
    if not where:
        continue
    where = WHERE_FIXUPS.get(where.lower(), where)
    if where:
        WHERE_BY_DAYNUM[daynum] = where

def where_for_day(title):
    m = re.search(r'-\s*(\d{1,2})\s*SEP', title, re.I)
    if not m:
        m = re.search(r'\(DAY\s*(\d{1,2})\)', title, re.I)
    if not m:
        return None
    return WHERE_BY_DAYNUM.get(int(m.group(1)))

HOTEL_INFO = [
    {'name': 'The Republic Hotel', 'address': 'Via Gaeta 61, 185 Rome',
     'full_address': 'Via Gaeta 61, 00185 Rome, Italy',
     'phone': '+39 06 8115 7001', 'email': 'therepublic@aghotels.it',
     'website': 'https://www.therepublichotel.it/',
     'booking_ref': 'Gary &amp; Karen: 5179180 &middot; Deb &amp; Tom: 5179179',
     'mandatory_fee': ('EUR', 'City tourist tax &ndash; &euro;7.50 per person, per night (up to 10 nights), payable directly to the hotel'),
     'dates': '11-14 Sept 2026 (check-out morning of the 14th for Civitavecchia/cruise embarkation)'},
    {'name': 'Hotel Borgo di Cortefreda Relais', 'address': 'Via Roma 191, 50028, Tavarnelle Val Di Pesa',
     'full_address': 'Via Roma 191, 50028 Tavarnelle Val di Pesa (FI), Italy',
     'phone': '+39 055 807 3333', 'email': 'info@borgodicortefreda.com',
     'website': 'https://www.borgodicortefreda.com/',
     'booking_ref': 'Gary &amp; Karen: 900422765 (hotel conf. 45873846) &middot; Deb &amp; Tom: 900422785 (hotel conf. 45873847)',
     'mandatory_fee': ('EUR', 'City tourist tax &ndash; &euro;3.00 per person, per night (up to 7 nights), payable directly to the hotel'),
     'dates': '21-23 Sept 2026 (check-out morning of the 23rd for the drive to Milan)'},
    {'name': 'iQ Hotel Milano', 'address': 'Via Giovanni Battista Pirelli, 5, 20124 Milan',
     'full_address': 'Via Giovanni Battista Pirelli 5, 20124 Milan, Italy',
     'phone': '+39 02 8498 0810', 'email': 'info@iqhotelmilano.it',
     'website': 'https://www.iqhotelmilano.it/',
     'booking_ref': 'Gary &amp; Karen: 9079750869671 (conf. 2385198897) &middot; Deb &amp; Tom: 9074737872483 (conf. 2385198904)',
     'mandatory_fee': ('EUR', 'City tourist tax &ndash; &euro;10.00 per person, per night, payable directly to the hotel'),
     'dates': '23-24 Sept 2026 (check-out morning of the 24th for the flight to London)'},
    {'name': 'The Level at Melia White House', 'address': 'Longford Street, Regents Park, London NW1 3UP',
     'full_address': "Longford Street, Regent's Park, London NW1 3UP, United Kingdom",
     'phone': '+44 20 7391 3000', 'email': 'melia.white.house@melia.com',
     'website': 'https://www.melia.com/en/hotels/united-kingdom/london/the-level-at-melia-white-house',
     'tube': 'Great Portland Street station (Circle, Hammersmith & City, Metropolitan lines) - approx. 2-3 min walk (~0.2 km), directly opposite the hotel',
     'booking_ref': 'Gary &amp; Karen: 702Lb92xxk &middot; Deb &amp; Tom: 702Hpxuze6',
     'dates': '24-27 Sept 2026 (depart Heathrow the night of the 27th)'},
]

HOTEL_ADDRESS = [(h['name'], h['address']) for h in HOTEL_INFO]

def stay_with_address(stay_text):
    for h in HOTEL_INFO:
        if h['name'] in stay_text:
            return f"{stay_text} - {h['address']} ({h['phone']} · {h['email']})"
    return stay_text

CURRENCY_SYMBOL = {'EUR': '&euro;', 'GBP': '&pound;', 'USD': '$', 'NZD': 'NZ$'}

def mandatory_fee_box(currency, text):
    symbol = CURRENCY_SYMBOL.get(currency, currency)
    return f'''
    <div class="mandatory-fee-box">
      <span class="currency-badge" title="Payable in {esc(currency)}">{symbol}</span>
      <span class="mandatory-fee-text"><strong>Mandatory fee:</strong> {text}</span>
    </div>'''

def hotel_directory_cards():
    cards = ''
    for h in HOTEL_INFO:
        tube_html = f'<div class="place-hours">&#128676; {esc(h["tube"])}</div>' if h.get('tube') else ''
        dates_html = f'<div class="place-hours">&#128197; {esc(h["dates"])}</div>' if h.get('dates') else ''
        ref_html = f'<div class="place-hours">&#128203; Booking ref &ndash; {h["booking_ref"]}</div>' if h.get('booking_ref') else ''
        fee_html = mandatory_fee_box(*h['mandatory_fee']) if h.get('mandatory_fee') else ''
        qr_b64 = HOTEL_QR.get(h['name'])
        qr_html = (
            f'<a class="place-qr-corner" href="{esc(h["website"])}" target="_blank" title="Scan or click for hotel website">'
            f'<img src="data:image/png;base64,{qr_b64}" alt="QR code to {esc(h["name"])} website"></a>'
        ) if qr_b64 and h.get('website') else ''
        cards += f'''
        <div class="place-card hotel-card">
          <div class="place-name">{esc(h['name'])}</div>
          <div class="place-addr">{esc(h['full_address'])}</div>
          {dates_html}
          <div class="place-hours">&#128222; {esc(h['phone'])}</div>
          <div class="place-hours">&#9993;&#65039; {esc(h['email'])}</div>
          {tube_html}
          {ref_html}
          {fee_html}
          {qr_html}
        </div>'''
    return cards

HOTEL_DIRECTORY_HTML = hotel_directory_cards()

EMERGENCY_CONTACTS = [
    {
        'title': 'Karen &amp; Gary Nicholson',
        'people': [
            {'name': 'Emma Warmouth', 'phone': '+64 27 848 6867', 'email': 'emma.warmouth@nzdata.co.nz'},
            {'name': 'David Nicholson', 'phone': '+64 27 856 7966', 'email': 'davidnicholson@hotmail.com'},
            {'name': 'Steve Nicholson', 'phone': '+64 27 873 9578', 'email': ''},
            {'name': 'Martina Gyde', 'phone': '+64 27 590 4156', 'email': 'martinag@xtra.co.nz'},
            {'name': 'Gary Nicholson', 'phone': '+64 27 542 7747', 'email': 'gary.nicholson@garrison.co.nz',
             'extra': [('&#128194;', 'International Drivers Licence: IDP196978'),
                       ('&#128194;', 'ETA reference number: 2020-0000-6027-5337')]},
            {'name': 'Karen Nicholson', 'phone': '+64 275 536 746', 'email': 'karen.nicholson@garrison.co.nz',
             'extra': [('&#128194;', 'ETA reference number: 2020-0000-6027-5878')]},
        ],
    },
    {
        'title': 'Deb Gyde &amp; Thomas Akhurst',
        'people': [
            {'name': '', 'phone': '', 'email': ''},
            {'name': '', 'phone': '', 'email': ''},
            {'name': '', 'phone': '', 'email': ''},
            {'name': '', 'phone': '', 'email': ''},
        ],
    },
]

def _emergency_contact_person_html(slot_num, person):
    if person['name']:
        name_html = esc(person['name'])
    else:
        name_html = f'<span class="ec-blank">Person {slot_num} &ndash; (add name)</span>'
    phone_html = (f'<div class="ec-line">&#128222; {esc(person["phone"])}</div>' if person['phone']
                  else '<div class="ec-line ec-blank-line">&#128222; &nbsp;</div>')
    email_html = (f'<div class="ec-line">&#9993;&#65039; {esc(person["email"])}</div>' if person['email']
                  else '<div class="ec-line ec-blank-line">&#9993;&#65039; &nbsp;</div>')
    extra_html = ''.join(f'<div class="ec-line">{icon} {esc(text)}</div>' for icon, text in person.get('extra', []))
    return f'''
        <div class="ec-person">
          <div class="ec-person-name">{name_html}</div>
          {phone_html}
          {email_html}
          {extra_html}
        </div>'''

def _emergency_contacts_box_html(box):
    people_html = ''.join(_emergency_contact_person_html(i + 1, p) for i, p in enumerate(box['people']))
    return f'''
      <div class="ec-box">
        <h3 class="ec-box-title">{box['title']}</h3>
        <div class="ec-people">{people_html}</div>
      </div>'''

EMERGENCY_CONTACTS_HTML = ''.join(_emergency_contacts_box_html(b) for b in EMERGENCY_CONTACTS)

HOTEL_EMAIL_BODY = "Fab 4 Europe Trip - Hotel Addresses\n\n" + "\n\n".join(
    f"{h['name']}\n{h['full_address']}\nDates: {h.get('dates','')}\nPhone: {h['phone']}\nEmail: {h['email']}"
    for h in HOTEL_INFO
)
HOTEL_MAILTO = (
    "mailto:?subject=" + urllib.parse.quote("Fab 4 Europe Trip - Hotel Addresses")
    + "&body=" + urllib.parse.quote(HOTEL_EMAIL_BODY)
)

# ---------- ZTL / Limited Traffic Zones (Italy) ----------

ZTL_CITIES = [
    {'place': 'Rome (Centro Storico)', 'type': "Italy's most famous ZTL &ndash; not on our drive route",
     'address': "Daytime hours Mon&ndash;Fri, with extended evening ZTL in some nightlife sectors on weekends &ndash; camera-enforced across the historic centre.",
     'fact': "We don't collect the hire car until Civitavecchia, so this one's FYI only &ndash; but it's the zone every guide warns about first, and worth knowing about generally."},
    {'place': 'Milan &ndash; Area C', 'type': 'Congestion charge + ZTL ring around the Duomo',
     'address': 'Mon&ndash;Fri 7:30am&ndash;7:30pm, about &euro;7.50/entry (higher on weekends), camera-enforced seven days a week from 2026.',
     'fact': 'The iQ Hotel Milano (Via Pirelli) sits just outside the Area C ring, so arriving/leaving the hotel should be fine &ndash; it only becomes a problem if we drive in towards the Duomo.'},
    {'place': 'Como &amp; Cernobbio (Option A)', 'type': 'Como old town ZTL &ndash; enforced daily, 9am&ndash;10pm',
     'address': 'Covers the walled Citt&agrave; Murata, Piazza Duomo and Via Vittorio Emanuele II. The Cernobbio/Tremezzo lakeside road (SS340) itself is open, but narrow and often busy.',
     'fact': "Best to park in a signed lot outside the old town (e.g. Autosilo Valduce) rather than drive in for Harry's Bar/the lakefront."},
    {'place': 'Bologna (Option B breakfast stop)', 'type': 'ZTL Centro Storico &ndash; every day, 7am&ndash;8pm',
     'address': 'Camera-enforced ("Sirio" system) across the historic centre; a few streets are pedestrian-only around the clock.',
     'fact': 'Our Option B breakfast stop, Aroma Specialty Coffee on Via Portanova, sits inside this zone &ndash; better to park just outside and walk the last few minutes than drive to the door.'},
    {'place': 'Modena &amp; Maranello (Option B)', 'type': "Modena's old town ZTL is effectively permit-holders-only",
     'address': "Modena's historic centre is restricted for most of the day; Maranello itself has no formal ZTL, but very heavy paid parking near the Ferrari Museum.",
     'fact': 'Best to follow the signed ring road/tangenziale around Modena rather than cut through its centre on the way to Maranello.'},
    {'place': 'Florence', 'type': 'ZTL &ndash; 5 sectors, Mon&ndash;Fri 7:30am&ndash;8pm, Sat 7:30am&ndash;4pm',
     'address': 'Free to drive Sundays and public holidays. Covers Piazza del Duomo, Piazza della Signoria and most of the historic core.',
     'fact': "Not on our base route, but easy to stumble into if we detour into central Florence for a look."},
    {'place': 'Siena', 'type': 'Historic centre is effectively car-free',
     'address': 'The whole medieval core sits inside a strict ZTL &ndash; park in one of the signed "parcheggio scambiatore" lots outside the walls and walk in.',
     'fact': 'Relevant if we make the short detour south from our hotel to see the Palio square (Piazza del Campo).'},
    {'place': 'San Gimignano', 'type': 'No visitor cars inside the walls, ever (Apr&ndash;Oct)',
     'address': 'Five paid car parks (P1&ndash;P5) sit just outside the medieval gates &ndash; it\'s a walk up from there, whichever one we use.',
     'fact': "The 'medieval Manhattan' towers from our Day 12 Fun Facts &ndash; a natural detour from our Tuscany hotel, so worth knowing before we drive up."},
    {'place': 'Venice (Option C)', 'type': "No cars at all in the historic centre &ndash; more a total ban than a ZTL",
     'address': "The car has to be left on the mainland at Tronchetto or Piazzale Roma car parks; the centre itself is reached on foot or by vaporetto (water bus).",
     'fact': "Already flagged on our Option C route notes &ndash; the most extreme version of a 'limited traffic zone' in Italy."},
]

def _ztl_card(c):
    return f'''
    <div class="place-card">
      <div class="place-name">{c['place']}</div>
      <div class="place-hours">&#128337; {c['type']}</div>
      <div class="place-addr">{c['address']}</div>
      <div class="place-fact">&#128663; {c['fact']}</div>
    </div>'''

ZTL_CARDS_HTML = ''.join(_ztl_card(c) for c in ZTL_CITIES)

# ---------- Daily Quiz (16 "on the ground" days, 11-26 Sept - excludes pure long-haul travel days) ----------

QUIZ_PEOPLE = ['Gary', 'Karen', 'Deb', 'Tom']
QUIZ_LETTERS = ['A', 'B', 'C', 'D']

DAILY_QUIZ = [
    {'date': 'Fri 11 Sep', 'day_num': 2, 'theme': 'Rome Arrival', 'qs': [
        {'q': 'Which river runs through the middle of Rome?', 'opts': ['The Po', 'The Tiber', 'The Arno', 'The Danube'], 'ans': 1,
         'note': 'The Tiber (Tevere) flows right past our hotel on its way out to the sea at Ostia.'},
        {'q': 'Rome is famously said to be built on how many hills?', 'opts': ['Five', 'Six', 'Seven', 'Nine'], 'ans': 2,
         'note': 'The "Seven Hills of Rome" - Palatine, Capitoline, Aventine, Caelian, Esquiline, Viminal and Quirinal.'},
        {'q': 'What is the name of the independent city-state entirely enclosed within Rome?', 'opts': ['San Marino', 'Monaco', 'Vatican City', 'Andorra'], 'ans': 2,
         'note': "Vatican City - the world's smallest country, and where we're headed tomorrow."},
        {'q': 'Which ancient structure is also known by its Latin name, the Amphitheatrum Flavium?', 'opts': ['The Pantheon', 'The Colosseum', 'The Circus Maximus', 'The Roman Forum'], 'ans': 1,
         'note': "The Colosseum - on the itinerary for Day 4 (Sunday)."},
        {'q': 'Legend says Rome was founded by twin brothers raised by a wolf. What were their names?', 'opts': ['Castor and Pollux', 'Romulus and Remus', 'Brutus and Cassius', 'Titus and Vespasian'], 'ans': 1,
         'note': 'Romulus and Remus - Romulus supposedly founded the city in 753 BC and became its first king.'},
    ]},
    {'date': 'Sat 12 Sep', 'day_num': 3, 'theme': 'Vatican & Sistine Chapel', 'qs': [
        {'q': 'Who painted the ceiling of the Sistine Chapel?', 'opts': ['Leonardo da Vinci', 'Raphael', 'Michelangelo', 'Botticelli'], 'ans': 2,
         'note': 'Michelangelo - he reportedly complained the whole time that he was a sculptor, not a painter.'},
        {'q': 'Roughly how long did it take Michelangelo to paint the Sistine Chapel ceiling?', 'opts': ['About 1 year', 'About 4 years', 'About 10 years', 'About 20 years'], 'ans': 1,
         'note': 'About 4 years, 1508-1512, mostly lying on his back on scaffolding.'},
        {'q': "What is the name of Michelangelo's huge fresco on the Sistine Chapel's altar wall, painted decades after the ceiling?", 'opts': ['The Creation of Adam', 'The Last Supper', 'The Last Judgment', 'The School of Athens'], 'ans': 2,
         'note': 'The Last Judgment, painted 1536-1541 - nearly 30 years after the ceiling.'},
        {'q': "What is the world's smallest country by area, which we're visiting today?", 'opts': ['Monaco', 'Vatican City', 'San Marino', 'Liechtenstein'], 'ans': 1,
         'note': 'Vatican City - about 0.44 sq km, smaller than most golf courses.'},
        {'q': "What is the name of the huge square in front of St Peter's Basilica, ringed by Bernini's colonnades?", 'opts': ['Piazza Navona', 'Piazza del Popolo', "St Peter's Square", 'Piazza di Spagna'], 'ans': 2,
         'note': "St Peter's Square - the colonnade's four rows of columns are designed to line up as a single row from two marked spots in the piazza."},
    ]},
    {'date': 'Sun 13 Sep', 'day_num': 4, 'theme': 'Colosseum', 'qs': [
        {'q': 'In roughly what year did construction of the Colosseum finish?', 'opts': ['80 AD', '200 AD', '30 BC', '500 AD'], 'ans': 0,
         'note': '80 AD, under Emperor Titus - construction had started under his father Vespasian about 8 years earlier.'},
        {'q': 'Roughly how many spectators could the Colosseum hold?', 'opts': ['5,000', '15,000', '50,000-80,000', '200,000'], 'ans': 2,
         'note': 'Around 50,000-80,000 - similar to a large modern stadium.'},
        {'q': 'What was the underground network of tunnels and animal cages beneath the arena floor called?', 'opts': ['The Catacombs', 'The Hypogeum', 'The Forum', 'The Atrium'], 'ans': 1,
         'note': 'The Hypogeum - a two-level maze of passages used to hoist animals and scenery up through trapdoors.'},
        {'q': 'Which Roman emperor commissioned the Colosseum?', 'opts': ['Nero', 'Augustus', 'Vespasian', 'Julius Caesar'], 'ans': 2,
         'note': 'Vespasian, funded partly by treasure from the sack of Jerusalem.'},
        {'q': "What stone makes up most of the Colosseum's outer structure?", 'opts': ['Marble', 'Travertine limestone', 'Granite', 'Brick only'], 'ans': 1,
         'note': 'Travertine limestone, quarried near Tivoli and hauled to Rome along a purpose-built road.'},
    ]},
    {'date': 'Mon 14 Sep', 'day_num': 5, 'theme': 'Rome to the Cruise', 'qs': [
        {'q': "What is the name of the ship we're boarding today?", 'opts': ['Queen Mary 2', 'Queen Elizabeth', 'Queen Victoria', 'Queen Anne'], 'ans': 2,
         'note': 'Queen Victoria - Cunard voyage V618D, our home for the next week.'},
        {'q': 'Which shipping line operates Queen Victoria?', 'opts': ['Cunard', 'P&O', 'Princess Cruises', 'Royal Caribbean'], 'ans': 0,
         'note': 'Cunard - famous for transatlantic ocean liners since the 1840s.'},
        {'q': 'Which Cunard liner sank after being torpedoed in 1915, helping draw the US into WWI?', 'opts': ['Titanic', 'Lusitania', 'Britannic', 'Mauretania'], 'ans': 1,
         'note': 'RMS Lusitania - torpedoed off Ireland; nearly 1,200 died, including 128 Americans.'},
        {'q': 'What year was the Cunard Line founded?', 'opts': ['1740', '1840', '1900', '1950'], 'ans': 1,
         'note': '1840, by Samuel Cunard - making it one of the oldest shipping brands still operating.'},
        {'q': "Which Italian port are we sailing from today?", 'opts': ['Naples', 'Genoa', 'Civitavecchia', 'Livorno'], 'ans': 2,
         'note': "Civitavecchia - Rome's cruise port, about an hour from the city."},
    ]},
    {'date': 'Tue 15 Sep', 'day_num': 6, 'theme': 'Sea Day', 'qs': [
        {'q': 'The Mediterranean Sea connects to the Atlantic Ocean via which strait?', 'opts': ['Strait of Messina', 'Strait of Gibraltar', 'The Bosphorus', 'Strait of Otranto'], 'ans': 1,
         'note': 'The Strait of Gibraltar - only about 13km wide at its narrowest.'},
        {'q': 'Which is the largest island in the Mediterranean?', 'opts': ['Corsica', 'Cyprus', 'Sicily', 'Sardinia'], 'ans': 2,
         'note': 'Sicily - just ahead of Sardinia in size.'},
        {'q': "Approximately how deep is the Mediterranean's deepest point, the Calypso Deep?", 'opts': ['About 500m', 'About 2,000m', 'About 5,200m', 'About 10,000m'], 'ans': 2,
         'note': 'About 5,200m, southwest of Greece.'},
        {'q': 'Which sea connects to the Mediterranean via the Dardanelles and Bosphorus straits?', 'opts': ['The Red Sea', 'The Black Sea', 'The Caspian Sea', 'The Adriatic Sea'], 'ans': 1,
         'note': 'The Black Sea, via Istanbul\'s two famous straits.'},
        {'q': "What unit is traditionally used to measure a ship's speed at sea?", 'opts': ['Miles per hour', 'Knots', 'Fathoms per hour', 'Leagues per hour'], 'ans': 1,
         'note': 'Knots (nautical miles per hour) - one knot is about 1.85 km/h.'},
    ]},
    {'date': 'Wed 16 Sep', 'day_num': 7, 'theme': 'Marseille, France', 'qs': [
        {'q': "Marseille is France's ___ largest city.", 'opts': ['Largest', 'Second-largest', 'Third-largest', 'Fifth-largest'], 'ans': 1,
         'note': 'Second-largest, after Paris.'},
        {'q': 'Marseille was founded by settlers from which ancient civilisation, around 600 BC?', 'opts': ['Romans', 'Phoenicians', 'Greeks (Phocaeans)', 'Etruscans'], 'ans': 2,
         'note': 'Greek settlers from Phocaea - making it one of the oldest cities in France.'},
        {'q': "What is France's national anthem called, named after soldiers from Marseille who sang it marching to Paris in 1792?", 'opts': ['La Vie en Rose', 'La Marseillaise', 'Non, Je Ne Regrette Rien', 'Frère Jacques'], 'ans': 1,
         'note': 'La Marseillaise - now sung at every French sporting event and state occasion.'},
        {'q': 'What is the traditional Provençal fish stew Marseille is famous for?', 'opts': ['Ratatouille', 'Bouillabaisse', 'Cassoulet', 'Coq au vin'], 'ans': 1,
         'note': "Bouillabaisse - originally a fisherman's stew made from the day's unsellable catch."},
        {'q': "What is the fortified hilltop basilica overlooking Marseille's harbour called?", 'opts': ['Notre-Dame de la Garde', 'Sacré-Cœur', 'Notre-Dame de Paris', 'Sainte-Chapelle'], 'ans': 0,
         'note': "Notre-Dame de la Garde - locals call it 'la bonne mère' (the good mother)."},
    ]},
    {'date': 'Thu 17 Sep', 'day_num': 8, 'theme': 'Villefranche & Monaco', 'qs': [
        {'q': 'Monaco is the second-smallest country in the world. Which is the smallest?', 'opts': ['San Marino', 'Vatican City', 'Liechtenstein', 'Malta'], 'ans': 1,
         'note': 'Vatican City - Monaco is second, at about 2.1 sq km.'},
        {'q': 'Which royal family has ruled Monaco for over 700 years?', 'opts': ['The Windsors', 'The Grimaldis', 'The Bourbons', 'The Habsburgs'], 'ans': 1,
         'note': 'The Grimaldis - one of the longest-reigning royal families in the world.'},
        {'q': 'What famous annual motor race runs through the streets of Monaco?', 'opts': ['Le Mans 24 Hours', 'Monaco Grand Prix', 'Dakar Rally', 'Tour de France'], 'ans': 1,
         'note': "The Monaco Grand Prix - one of Formula 1's oldest and most prestigious races."},
        {'q': 'Which Hollywood actress became Princess of Monaco in 1956, marrying Prince Rainier III?', 'opts': ['Audrey Hepburn', 'Grace Kelly', 'Ingrid Bergman', 'Elizabeth Taylor'], 'ans': 1,
         'note': 'Grace Kelly - she gave up her acting career to become Princess Grace.'},
        {'q': 'Monaco residents famously pay no what?', 'opts': ['Council rates', 'Income tax', 'Road tolls', 'Import duty'], 'ans': 1,
         'note': "No personal income tax for residents - part of why it's such an expensive place to live."},
    ]},
    {'date': 'Fri 18 Sep', 'day_num': 9, 'theme': 'Genoa, Italy', 'qs': [
        {'q': 'Which explorer, credited with reaching the Americas in 1492, was born in Genoa?', 'opts': ['Marco Polo', 'Amerigo Vespucci', 'Christopher Columbus', 'Ferdinand Magellan'], 'ans': 2,
         'note': 'Christopher Columbus - born in Genoa around 1451.'},
        {'q': 'Genoa is the capital of which Italian region?', 'opts': ['Tuscany', 'Liguria', 'Piedmont', 'Lombardy'], 'ans': 1,
         'note': 'Liguria - the crescent-shaped region along the Italian Riviera.'},
        {'q': 'Which world-famous basil sauce originated in Genoa?', 'opts': ['Marinara', 'Pesto', 'Alfredo', 'Arrabbiata'], 'ans': 1,
         'note': 'Pesto (alla genovese) - traditionally made with basil, pine nuts, garlic, parmesan and olive oil.'},
        {'q': "Genoa's historic centre is often ranked among Europe's largest what?", 'opts': ['Medieval castles', 'Medieval old towns', 'Cathedrals', 'Palace complexes'], 'ans': 1,
         'note': "Its centro storico is regularly cited as one of the largest and best-preserved medieval old towns in Europe."},
        {'q': 'In the Middle Ages, Genoa was a powerful maritime republic rivalling which other Italian sea power?', 'opts': ['Naples', 'Venice', 'Palermo', 'Bari'], 'ans': 1,
         'note': 'Venice - the two republics fought several wars for control of Mediterranean trade.'},
    ]},
    {'date': 'Sat 19 Sep', 'day_num': 10, 'theme': 'La Spezia & Pisa', 'qs': [
        {'q': 'The Leaning Tower of Pisa started leaning almost immediately, mainly because of what?', 'opts': ['An earthquake', 'Soft, unstable ground', 'A design flaw in the bells', 'War damage'], 'ans': 1,
         'note': "Soft, waterlogged subsoil couldn't support the foundation evenly."},
        {'q': 'How many storeys does the Leaning Tower of Pisa have?', 'opts': ['4', '6', '8', '12'], 'ans': 2,
         'note': '8 storeys, including the belfry at the top.'},
        {'q': 'What type of building is the Leaning Tower actually part of?', 'opts': ['A city hall', "A cathedral bell tower (campanile)", 'A fortress', 'A university'], 'ans': 1,
         'note': "It's the freestanding campanile (bell tower) of Pisa Cathedral."},
        {'q': 'Which scientist, born in Pisa, is said (probably as legend) to have dropped balls from the tower to study gravity?', 'opts': ['Leonardo da Vinci', 'Galileo Galilei', 'Copernicus', 'Archimedes'], 'ans': 1,
         'note': "Galileo Galilei - the story is likely apocryphal, but he did live and study in Pisa."},
        {'q': 'La Spezia sits at the gateway to which colourful stretch of Ligurian coastline, famous for five cliffside villages?', 'opts': ['Amalfi Coast', 'Cinque Terre', 'Costa Smeralda', 'Riviera di Levante'], 'ans': 1,
         'note': "Cinque Terre - literally 'Five Lands': Monterosso, Vernazza, Corniglia, Manarola and Riomaggiore."},
    ]},
    {'date': 'Sun 20 Sep', 'day_num': 11, 'theme': 'Sea Day', 'qs': [
        {'q': 'Which is traditionally considered the longest river in the world?', 'opts': ['Amazon', 'Nile', 'Yangtze', 'Mississippi'], 'ans': 1,
         'note': 'The Nile, by most classic measurements - though some newer surveys argue for the Amazon.'},
        {'q': 'Which is the largest ocean on Earth?', 'opts': ['Atlantic', 'Indian', 'Arctic', 'Pacific'], 'ans': 3,
         'note': 'The Pacific - bigger than all the landmasses on Earth combined.'},
        {'q': 'Which country has the most time zones?', 'opts': ['Russia', 'USA', 'France', 'China'], 'ans': 2,
         'note': 'France - thanks to its overseas territories scattered around the globe (12 in total).'},
        {'q': 'What is the smallest continent by land area?', 'opts': ['Europe', 'Australia/Oceania', 'Antarctica', 'South America'], 'ans': 1,
         'note': 'Australia/Oceania.'},
        {'q': 'Which mountain range forms part of the traditional boundary between Europe and Asia?', 'opts': ['The Alps', 'The Urals', 'The Pyrenees', 'The Carpathians'], 'ans': 1,
         'note': 'The Ural Mountains, running through Russia.'},
    ]},
    {'date': 'Mon 21 Sep', 'day_num': 12, 'theme': 'Tuscany (Talamone & Chianti)', 'qs': [
        {'q': 'What colour is the rooster on the seal of authentic Chianti Classico wine?', 'opts': ['Red', 'White', 'Black', 'Gold'], 'ans': 2,
         'note': 'Black - the "Gallo Nero" seal, only allowed on wine from the original historic Chianti Classico zone.'},
        {'q': 'Which grape variety is Chianti primarily made from?', 'opts': ['Nebbiolo', 'Sangiovese', 'Barbera', 'Montepulciano'], 'ans': 1,
         'note': 'Sangiovese - Italy\'s most widely planted red grape.'},
        {'q': "In Dante's Divine Comedy, which section mockingly mentions Talamone, the port we're passing through today?", 'opts': ['Inferno', 'Purgatorio', 'Paradiso', "It isn't mentioned"], 'ans': 1,
         'note': "Purgatorio - the Sienese had just bought Talamone hoping to build their fortunes there; it never worked out."},
        {'q': "Tuscany's capital and the birthplace of the Renaissance is which city?", 'opts': ['Siena', 'Pisa', 'Florence', 'Lucca'], 'ans': 2,
         'note': 'Florence.'},
        {'q': 'What is the name for the low stone farmhouse-style accommodation common across the Tuscan countryside?', 'opts': ['Villa', 'Agriturismo', 'Palazzo', 'Trattoria'], 'ans': 1,
         'note': "Agriturismo - a working farm offering accommodation and food, like our lunch stop today."},
    ]},
    {'date': 'Tue 22 Sep', 'day_num': 13, 'theme': 'Tuscany Free Day', 'qs': [
        {'q': 'San Gimignano, near our hotel, is famous for its skyline of medieval what?', 'opts': ['Windmills', 'Towers', 'Bridges', 'Domes'], 'ans': 1,
         'note': "Its 'medieval Manhattan' skyline - rival families once competed to build the tallest tower."},
        {'q': "How many of San Gimignano's original ~72 medieval towers still survive today?", 'opts': ['About 3', 'About 14', 'About 40', 'All 72'], 'ans': 1,
         'note': 'About 14 - most were later torn down or collapsed.'},
        {'q': 'Which Renaissance polymath was born in a small Tuscan town near Florence, sharing his name with it?', 'opts': ['Michelangelo Buonarroti', 'Leonardo da Vinci', 'Sandro Botticelli', 'Donatello'], 'ans': 1,
         'note': "Leonardo da Vinci - born in the town of Vinci, in the province of Florence."},
        {'q': 'The Chianti wine region lies roughly between which two famous Tuscan cities?', 'opts': ['Florence and Siena', 'Pisa and Lucca', 'Florence and Rome', 'Siena and Rome'], 'ans': 0,
         'note': 'Florence and Siena.'},
        {'q': 'Which powerful banking family ruled Florence and patronised the Renaissance for generations?', 'opts': ['The Borgias', 'The Medici', 'The Sforza', 'The Visconti'], 'ans': 1,
         'note': 'The Medici family - bankers, popes and patrons of Michelangelo, Botticelli and Galileo.'},
    ]},
    {'date': 'Wed 23 Sep', 'day_num': 14, 'theme': 'Milan (Options Day)', 'qs': [
        {'q': "Roughly how long did Milan's Duomo take to complete, from start to its final touches?", 'opts': ['About 10 years', 'About 50 years', 'Nearly 6 centuries', '100 years'], 'ans': 2,
         'note': "Started in 1386, with its final bronze door only added in 1965 - almost 600 years."},
        {'q': "Leonardo da Vinci's mural The Last Supper is housed in which Milan building?", 'opts': ['Milan Cathedral', 'Santa Maria delle Grazie', 'La Scala', 'Castello Sforzesco'], 'ans': 1,
         'note': 'The refectory of the Santa Maria delle Grazie convent.'},
        {'q': 'Milan is considered, alongside Paris, one of the world capitals of which industry?', 'opts': ['Finance', 'Fashion', 'Film', 'Publishing'], 'ans': 1,
         'note': "Fashion - home to Milan Fashion Week and many major Italian fashion houses."},
        {'q': "What is the name of Milan's world-famous opera house?", 'opts': ['La Fenice', 'La Scala', 'San Carlo', 'Teatro Massimo'], 'ans': 1,
         'note': 'La Scala, opened in 1778.'},
        {'q': "If we take the Como option today, whose famous villa on Lake Como's shore might we spot?", 'opts': ["Elton John's", "George Clooney's", "Tom Cruise's", "Ed Sheeran's"], 'ans': 1,
         'note': "George Clooney's Villa Oleandra in Laglio - he's an honorary citizen of the town."},
    ]},
    {'date': 'Thu 24 Sep', 'day_num': 15, 'theme': 'London Arrival', 'qs': [
        {'q': 'What is the name of the river that flows through London?', 'opts': ['The Severn', 'The Thames', 'The Avon', 'The Mersey'], 'ans': 1,
         'note': 'The Thames - our hotel and The Lighterman both sit right on it near Regent\'s Park/Kings Cross.'},
        {'q': 'Approximately how long is the River Thames?', 'opts': ['50 miles', '100 miles', '215 miles', '400 miles'], 'ans': 2,
         'note': 'About 215 miles (346 km) from its source in Gloucestershire to the North Sea.'},
        {'q': "What is London's famous clock tower usually called, after the bell inside it?", 'opts': ['Big Ben', 'The Shard', 'The Gherkin', 'The Elizabeth Tower'], 'ans': 0,
         'note': "Big Ben is technically the bell - the tower itself is the Elizabeth Tower - but everyone calls the whole thing Big Ben."},
        {'q': 'Which London Underground line is coloured dark blue on the Tube map?', 'opts': ['Circle line', 'Piccadilly line', 'Victoria line', 'Central line'], 'ans': 1,
         'note': 'The Piccadilly line - dark blue, running past Piccadilly Circus.'},
        {'q': "What is the collective name for London's famous red double-decker vehicles?", 'opts': ['Trams', 'Buses', 'Tuk-tuks', 'Trolleys'], 'ans': 1,
         'note': 'Buses - the modern Routemaster is a direct descendant of the original AEC Routemaster.'},
    ]},
    {'date': 'Fri 25 Sep', 'day_num': 16, 'theme': "London (The Mousetrap)", 'qs': [
        {'q': "The Mousetrap, which we're seeing tonight, is the world's longest-running what?", 'opts': ['Musical', 'Play', 'Opera', 'Ballet'], 'ans': 1,
         'note': "It's a play, not a musical - the longest continuously-running show of any kind in the world."},
        {'q': 'Who wrote The Mousetrap?', 'opts': ['Agatha Christie', 'Arthur Conan Doyle', 'Noël Coward', 'J.B. Priestley'], 'ans': 0,
         'note': "Agatha Christie - the undisputed 'Queen of Crime'."},
        {'q': 'Which London theatre district is home to most of the famous long-running shows?', 'opts': ['Shoreditch', 'West End', 'Camden', 'South Bank'], 'ans': 1,
         'note': "The West End - London's answer to Broadway."},
        {'q': 'The Mousetrap first opened in the West End in which decade?', 'opts': ['1930s', '1950s', '1970s', '1990s'], 'ans': 1,
         'note': '1952 - and it has run continuously ever since (apart from a brief COVID closure).'},
        {'q': 'Traditionally, audiences leaving The Mousetrap are asked to do what?', 'opts': ['Sign a guestbook', 'Keep the ending a secret', 'Take a photo with the cast', 'Write a review'], 'ans': 1,
         'note': "Keep the twist ending a secret - a tradition observed by audiences for over 70 years."},
    ]},
    {'date': 'Sat 26 Sep', 'day_num': 17, 'theme': 'London (Tower Bridge & Six)', 'qs': [
        {'q': "How many wives did King Henry VIII have - the subject of tonight's show, Six?", 'opts': ['Four', 'Five', 'Six', 'Seven'], 'ans': 2,
         'note': 'Six - "divorced, beheaded, died, divorced, beheaded, survived", as the old rhyme goes.'},
        {'q': 'Which of his six wives was famously beheaded, and was the second wife?', 'opts': ['Catherine of Aragon', 'Anne Boleyn', 'Jane Seymour', 'Catherine Howard'], 'ans': 1,
         'note': 'Anne Boleyn - executed in 1536; Catherine Howard (wife five) was also later beheaded.'},
        {'q': 'Tower Bridge, which we visit today, is often confused with which other London bridge?', 'opts': ['Millennium Bridge', 'London Bridge', 'Westminster Bridge', 'Blackfriars Bridge'], 'ans': 1,
         'note': "London Bridge - a US buyer once reportedly thought he'd bought Tower Bridge when he actually bought London Bridge."},
        {'q': 'What famous fortress sits beside Tower Bridge, once used as a royal palace and prison?', 'opts': ['Windsor Castle', 'The Tower of London', 'Buckingham Palace', 'Hampton Court'], 'ans': 1,
         'note': 'The Tower of London - nearly 1,000 years old.'},
        {'q': 'What valuable items are famously kept and guarded at the Tower of London?', 'opts': ['The Crown Jewels', 'The original Magna Carta', 'The Domesday Book', "Nelson's flagship"], 'ans': 0,
         'note': 'The Crown Jewels - including the Imperial State Crown, worn at coronations.'},
    ]},
]

def _quiz_screen_day_html(day):
    q_html = ''.join(
        f'<li><div class="quiz-q-text">{q["q"]}</div>'
        f'<div class="quiz-opts">{"&nbsp;&nbsp;&nbsp;".join(f"{QUIZ_LETTERS[i]}) {opt}" for i, opt in enumerate(q["opts"]))}</div></li>'
        for q in day['qs']
    )
    return f'''
    <div class="quiz-day-box">
      <div class="quiz-day-head">Day {day['day_num']} &middot; {day['date']} &middot; {day['theme']}</div>
      <ol class="quiz-q-list">{q_html}</ol>
    </div>'''

QUIZ_SCREEN_HTML = ''.join(_quiz_screen_day_html(d) for d in DAILY_QUIZ)

def _quiz_answer_day_html(day):
    li_html = ''.join(
        f'<li><strong>{QUIZ_LETTERS[q["ans"]]}</strong> &ndash; {q["opts"][q["ans"]]}. <span class="quiz-note">{q["note"]}</span></li>'
        for q in day['qs']
    )
    return f'''
    <div class="quiz-answer-day">
      <h3>Day {day['day_num']} &middot; {day['date']} &middot; {day['theme']}</h3>
      <ol>{li_html}</ol>
    </div>'''

QUIZ_ANSWER_KEY_HTML = ''.join(_quiz_answer_day_html(d) for d in DAILY_QUIZ)

FUN_FACTS = {
    'day-11': ('Villa Borghese Gardens were laid out from 1605 by Cardinal Scipione Borghese &ndash; nephew of Pope Paul V &ndash; as one of the first great "gardens of delight" in Europe, built purely for pleasure, art and parties rather than growing food.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/Villa_Borghese_gardens'),
    'day-12': ("It's a myth that Michelangelo painted the Sistine Chapel ceiling lying flat on his back. He actually designed a custom scaffold and painted standing up, craning his neck backwards for four years &ndash; the \"lying down\" idea came from a mistranslated 1527 biography.",
               'History.com', 'https://www.history.com/articles/7-things-you-may-not-know-about-the-sistine-chapel'),
    'day-13': ('The Colosseum had a retractable fabric awning called the velarium, made of the same sailcloth used on Roman warships. It weighed about 24 tonnes and was rigged and operated by a special detachment of around 1,000 sailors from the Roman navy.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/Velarium'),
    'day-14': ("Civitavecchia, where you'll board Queen Victoria, was built as a Roman port around 103-110 AD on the orders of Emperor Trajan, who commissioned the famous architect Apollodorus of Damascus to design it. It was originally called Centumcellae.",
               'Roman Ports', 'https://www.romanports.org/en/articles/human-interest/137-centumcellae-the-port-of-trajan.html'),
    'day-15': ("Cunard's Golden Lion Pub &ndash; where you'll have pre-dinner drinks tonight &ndash; takes its design cues from the original 1938 launch programme for the RMS Queen Elizabeth, keeping a slice of proper British pub tradition alive in the middle of the ocean.",
               'Cunard', 'https://www.cunard.com/en-us/activity-types/bars-and-lounges/golden-lion-pub'),
    'day-16': ('Marseille, today\'s port of call, is the oldest city in France &ndash; founded around 600 BC by Greek settlers from Phocaea, who named it Massalia. That makes it roughly 2,600 years old.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/Marseille'),
    'day-17': ('Monégasques &ndash; the actual citizens of Monaco &ndash; are legally banned from gambling in their own Monte Carlo Casino, a rule dating back to the mid-1800s. The casino was built specifically to draw money from wealthy foreign visitors instead.',
               'Fact Republic', 'https://factrepublic.com/facts/52517/'),
    'day-18': ('Genoa, today\'s port, is traditionally held to be the birthplace of Christopher Columbus around 1451 &ndash; Columbus himself wrote in his 1498 will "yo nacio en Genoba" ("I was born in Genoa"), though the claim is still debated by historians.',
               'Christopher Columbus', 'https://www.christopher-columbus.eu/who-was-columbus/italy.htm'),
    'day-19': ("The Leaning Tower of Pisa took almost 200 years to build (1173-1372) because construction was interrupted twice by war for decades at a time. Those pauses accidentally saved it &ndash; they gave the soft soil time to settle, which stopped the tower toppling before it was even finished.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Leaning_Tower_of_Pisa'),
    'day-20': ('Queen Victoria &ndash; the ship you\'re sailing on &ndash; was christened in Southampton on 10 December 2007 by Camilla, Duchess of Cornwall. The first champagne bottle swung at the hull famously failed to break (a bad omen, traditionally) before a second bottle did the job.',
               'Travel Weekly', 'https://www.travelweekly.com/Cruise-Travel/Queen-Victoria-christened'),
    'day-21': ("Talamone, where you'll stop for lunch, gets a mocking mention in Dante's Purgatorio. The Sienese had just bought the port for 8,000 florins hoping to build their fortunes there, but it was plagued by silt and malaria and never really worked out.",
               'Princeton Dante Project', 'https://dante.princeton.edu/'),
    'day-22': ('The black rooster on every bottle of Chianti Classico comes from a medieval legend: Florence and Siena settled a border dispute by each sending a knight to ride out at the crow of a rooster. Florence starved theirs so it crowed early in the dark, giving their knight a head start &ndash; and Florence most of Chianti.',
               'Visit Tuscany', 'https://www.visittuscany.com/en/ideas/the-gallo-nero-black-rooster-symbol-of-chianti-between-history-and-legend/'),
    'day-23': ('In the Galleria Vittorio Emanuele II next to the Duomo, tradition says spinning three times on your right heel on a certain mosaic bull\'s more sensitive anatomy brings good luck. It\'s so popular the mosaic has needed repeated restoration from all the grinding heels.',
               'VisitMilano', 'https://visitmilano.org/eng/sightseeing/historic-landmarks-and-buildings/galleria-vittorio-emanuele/'),
    'option-a-23sep': ("Lake Como's Laglio, just along the shore from Harry's Bar Cernobbio, is home to George Clooney's 18th-century Villa Oleandra, bought in 2002 for around $10 million and now estimated at over $100 million. He's become an honorary citizen of the town.",
               'Wevillas', 'https://wevillas.com/news/villa-oleandra-in-laglio-the-summer-home-of-george-clooney-on-como-lake'),
    'option-b-23sep': ("Ferrari's prancing horse logo wasn't Enzo Ferrari's idea originally. It came from WWI flying ace Francesco Baracca, who painted a horse on his fighter plane. After he was killed in 1918, his mother suggested the young racer Enzo Ferrari use it for luck &ndash; he kept the horse but changed its colour to black, in Baracca's memory.",
               'Rosso Automobili', 'https://rossoautomobili.com/blogs/magazine/origin-of-ferrari-prancing-horse-world-war-1-fighter-francesco-baracca'),
    'option-c-23sep': ("Venice has no cars at all in its historic centre &ndash; it's built across 118 small islands linked by more than 400 bridges, and the only way around is on foot or by boat. That's exactly why you'll need to park at Tronchetto or Piazzale Roma before walking in.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Venice'),
    'day-24': ('Tonight\'s dinner spot, The Lighterman, is named after the Victorian "lightermen" who steered flat-bottomed barges (called lighters) along the Regent\'s Canal right outside, ferrying goods through this once-industrial part of King\'s Cross.',
               "King's Cross", 'https://www.kingscross.co.uk/the-lighterman'),
    'day-25': ('The Mousetrap, playing tonight, is the world\'s longest continuously-running play &ndash; it opened in 1952 and passed 30,000 performances in 2025. By long tradition, the audience is asked at the end of every single show never to reveal the killer\'s identity.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/The_Mousetrap'),
    'day-26': ('The original <a href="https://www.hardrock.com/our-history" target="_blank">Hard Rock Cafe</a> in London opened on June 14, 1971, inside a deserted Rolls-Royce dealership. The founders only received a 6-month lease because their landlord did not think an American-style burger joint would last.',
               None, None),
    'day-27': ('When Heathrow first opened to passengers in 1946, the "terminal" was literally a row of ex-military tents along the Bath Road, furnished with floral armchairs, small tables of fresh flowers and even a branch of WH Smith &ndash; 63,000 passengers passed through in its first year.',
               'Business Traveller', 'https://www.businesstraveller.com/news/snapshot-1946-heathrow-opens/'),
}

FUN_FACTS_2 = {
    'day-11': ("The Galleria Borghese inside the gardens holds Bernini's Apollo and Daphne, carved when he was just 24, and a marble statue of Napoleon's sister Pauline Bonaparte reclining semi-nude that scandalised Rome when it was unveiled in 1808.",
               'Galleria Borghese', 'https://galleriaborghese.beniculturali.it/en/'),
    'day-12': ('St Peter\'s Basilica, next to the Sistine Chapel, took 120 years to build (1506-1626) and passed through the hands of 24 different architects, including Bramante, Raphael, Michelangelo and finally Bernini, who added the great colonnaded piazza.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/St._Peter%27s_Basilica'),
    'day-13': ("Beneath the Colosseum's arena floor lies the hypogeum &ndash; a two-level maze of tunnels and animal cages with as many as 80 vertical shafts and lift mechanisms that could hoist lions, bears and other beasts straight up into trapdoors in the arena.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Colosseum'),
    'day-14': ('Civitavecchia handles well over 2 million cruise passengers a year, making it one of the busiest cruise ports in the Mediterranean, despite the town itself having a population of only around 50,000.',
               'Port of Civitavecchia', 'https://en.wikipedia.org/wiki/Port_of_Civitavecchia'),
    'day-15': ("Cunard still keeps up a 'White Star Service' tradition of formal afternoon tea served by white-gloved waiters, a custom traceable back to Samuel Cunard winning the first transatlantic mail contract in 1839.",
               'Cunard', 'https://en.wikipedia.org/wiki/Cunard_Line'),
    'day-16': ('Marseille soap, savon de Marseille, has been made to essentially the same olive-oil recipe since a 1688 royal decree from Louis XIV fixed the exact ingredients allowed to carry the name.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/Savon_de_Marseille'),
    'day-17': ("Monaco is the world's second-smallest country after Vatican City, at just over 2 square kilometres - and it has grown roughly 20% larger since 1861 through land reclaimed from the sea.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Monaco'),
    'day-18': ("Genoa's medieval old town, the caruggi, is one of the largest and best-preserved historic centres in Europe - a dense maze of narrow lanes that helped the city earn UNESCO World Heritage status in 2006.",
               'UNESCO', 'https://whc.unesco.org/en/list/1211/'),
    'day-19': ('Before restoration work in the 1990s-2000s, the Leaning Tower of Pisa was tilting at nearly 5.5 degrees. Engineers carefully removed soil from beneath the raised side to reduce the lean to its current, more stable 3.97 degrees.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/Leaning_Tower_of_Pisa'),
    'day-20': ('Queen Victoria carries a two-deck library stocked with thousands of books, plus a dedicated bookshop, card room and ballroom - deliberately echoing the classic ocean liners of the 1920s and 30s rather than a modern mega-ship.',
               'Cunard', 'https://www.cunard.com/en-us/find-a-cruise/ships/queen-victoria'),
    'day-21': ("Talamone's hilltop Rocca Aldobrandesca fortress, overlooking the harbour where you'll arrive, was refortified by the Sienese in the 1300s and later garrisoned by the Spanish in the 1500s as part of their coastal defences.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Talamone'),
    'day-22': ("Chianti Classico must legally be aged at least a year before release, and the black rooster 'Gallo Nero' seal is only allowed on wine from the original historic Chianti Classico zone - not the wider Chianti region that surrounds it.",
               'Consorzio Vino Chianti Classico', 'https://www.chianticlassico.com/en/'),
    'day-23': ("Milan's Duomo took nearly 600 years to finish, from 1386 to 1965. Napoleon, crowned King of Italy inside it in 1805, ordered the facade rushed to completion and personally financed the work to have it ready in time.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Milan_Cathedral'),
    'option-a-23sep': ('Lake Como is one of the deepest lakes in Europe, plunging to over 400 metres in places - deep enough that its lake bed actually sits below sea level.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/Lake_Como'),
    'option-b-23sep': ('Every Ferrari road car is still largely hand-assembled at the Maranello factory, where fewer than 15 cars typically roll off the line each day - production is deliberately kept scarce.',
               'Ferrari', 'https://www.ferrari.com/en-EN/corporate'),
    'option-c-23sep': ("Venice is slowly sinking at roughly 1-2mm a year while the Adriatic rises around it, which is why the city completed the MOSE flood barrier system in 2020 to hold back high tides during 'acqua alta'.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/MOSE_(Venice)'),
    'day-24': ("Regent's Canal, which runs right past tonight's dinner spot, was built in the 1810s-1820s and named for the Prince Regent (later George IV). It once floated coal and building materials into London before being revived as a leisure towpath.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Regent%27s_Canal'),
    'day-25': ("The V&A Museum was founded in 1852 using profits from the Great Exhibition of 1851, and its collection has since grown to more than 2.8 million objects spanning 5,000 years of art and design.",
               'V&A', 'https://www.vam.ac.uk/info/about-us'),
    'day-26': ('The ravens at the Tower of London have had their wings trimmed since at least the 1600s, following the legend that the kingdom will fall if they ever leave. Traditionally at least six are kept there, plus one in reserve.',
               'Historic Royal Palaces', 'https://www.hrp.org.uk/tower-of-london/history-and-stories/the-ravens/'),
    'day-27': ("The Castle pub in Farringdon (today's Option 1 lunch) is the only pub in London licensed as a pawnbroker - supposedly granted personally by King George IV after he pawned his watch there to settle a gambling debt.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/The_Castle,_Farringdon'),
}

FUN_FACTS_3 = {
    'day-12': ("The Sistine Chapel ceiling you'll see this morning covers roughly 1,100 square metres and features over 300 individual figures - Michelangelo painted it almost entirely solo between 1508 and 1512, with only a handful of assistants mixing plaster and paint.",
               'Vatican Museums', 'https://www.museivaticani.va/content/museivaticani/en/collezioni/musei/cappella-sistina.html'),
    'day-18': ("Genoa's La Lanterna lighthouse, visible from the port today, was first built in 1128 and rebuilt to its current 76-metre form in 1543 - making it one of the oldest lighthouses still operating anywhere in the world.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Lanterna_di_Genova'),
    'day-21': ("Nearby San Gimignano once bristled with as many as 72 stone towers, built by rival medieval families competing to build the tallest as a show of wealth and power. Only 14 towers survive today, giving the town its famous 'medieval Manhattan' skyline.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/San_Gimignano'),
    'day-25': ("The V&A's Cast Courts hold a full plaster cast of Rome's Trajan's Column, taken in the 1860s - it's so tall it had to be split into two pieces just to fit under the gallery ceiling.",
               'V&A', 'https://www.vam.ac.uk/articles/a-history-of-the-cast-courts'),
    'day-27': ("Heathrow, where you'll fly out from tonight, handles more international passengers than any other airport on Earth - despite operating from just two runways, making it one of the busiest dual-runway airports in the world.",
               'Heathrow Airport', 'https://www.heathrow.com/company/about-heathrow'),
}

FUN_FACTS_4 = {
    'day-14': ("Queen Victoria, the ship you'll board today, carries just over 2,000 passengers - modest by modern cruise-ship standards, deliberately built smaller and more traditionally styled than Cunard's flagship Queen Mary 2.",
               'Cunard', 'https://www.cunard.com/en-us/find-a-cruise/ships/queen-victoria'),
    'day-16': ("Marseille's Notre-Dame de la Garde basilica, perched on the city's highest point, is topped by a 9.5-metre gilded statue of the Madonna and Child that has watched over sailors leaving and returning to the port since 1870.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Notre-Dame_de_la_Garde'),
    'day-17': ('The Monaco Grand Prix, first raced in 1929, runs on ordinary public streets barricaded off once a year - drivers reach speeds of over 290 km/h just metres from the harbour where cruise ships dock.',
               'Wikipedia', 'https://en.wikipedia.org/wiki/Monaco_Grand_Prix'),
    'day-22': ("The rows of cypress trees lining Tuscany's hillsides were originally planted as windbreaks and property boundary markers by landowners centuries ago, long before they became the region's postcard image.",
               'Visit Tuscany', 'https://www.visittuscany.com/en/'),
    'day-26': ("Six, the West End musical you're seeing tonight, reimagines the six wives of Henry VIII as a girl-group pop concert. It began life as a student production at Cambridge University in 2017 before transferring to the West End in 2019.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Six_(musical)'),
}

# Print-only fun facts: these do NOT appear in the on-screen fun-fact-box, and are
# hidden from Print Day / Print Book / section prints - they appear ONLY on the
# dedicated "Fun Facts by Day" printable page/section at the bottom of the site.
FUN_FACTS_5 = {
    'day-11': ("Tucked inside Villa Borghese is a curious 1867 water clock, invented by the monk-scientist Giovan Battista Embriaco, which still keeps time today using only the flow and pressure of water &ndash; no electricity or batteries.",
               'Turismo Roma', 'https://www.turismoroma.it/en/news/stories-and-hidden-facts-discovering-villa-borghese-through-educational-panels-and-podcasts'),
    'day-12': ("A ten-year restoration of the Sistine Chapel ceiling, completed in 1990 and sponsored by Japan's Nippon Television, stripped away centuries of soot, glue and candle grease to reveal Michelangelo's original vivid colours hidden underneath.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Restoration_of_the_Sistine_Chapel_frescoes'),
    'day-13': ("The Colosseum's opening games in 80 AD reportedly included a naumachia, a staged naval battle, with the arena flooded for small ships &ndash; once the underground hypogeum was built under Emperor Domitian, further flooding became impossible and the practice stopped.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Colosseum'),
    'day-14': ("Civitavecchia's harbour fortress, Forte Michelangelo, was designed by the architect Bramante in 1508 and completed in 1537 under the supervision of Michelangelo himself, and it still stands guard over the port today.",
               'Port of Rome - Civitavecchia', 'https://www.portofrome.it/history-of-civitavecchia/?lang=en'),
    'day-15': ("Queen Victoria was christened in Southampton on 10 December 2007 by Camilla, Duchess of Cornwall, and set sail on her maiden voyage to the Canary Islands the very next day.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/MS_Queen_Victoria'),
    'day-16': ("Marseille's signature bouillabaisse traces back to a simple fisherman's stew the ancient Greeks called kakavia; in 1980 the city's restaurateurs even drew up an official Bouillabaisse Charter defining the authentic recipe and ingredients.",
               'National Geographic', 'https://www.nationalgeographic.com/travel/article/bouillabaisse-deconstructing-pride-marseille'),
    'day-17': ("In 1297, the Grimaldi family seized Monaco's fortress when François Grimaldi disguised himself as a Franciscan monk to sneak armed men inside &ndash; the origin of the sword-wielding monk still shown on Monaco's coat of arms today.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Fran%C3%A7ois_Grimaldi'),
    'day-18': ("The word \"jeans\" traces back to Genoa itself: French traders called the sturdy cotton fabric woven there for sailors' trousers \"bleu de Gênes\" (blue of Genoa), later shortened to \"jean\".",
               'Merriam-Webster', 'https://www.merriam-webster.com/dictionary/jean'),
    'day-19': ("The tower was already sinking before it even looked crooked: by the time builders reached the second floor in 1178, the soft subsoil beneath its shallow 3-metre foundation had begun to give way, decades before the famous lean became obvious.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Leaning_Tower_of_Pisa'),
    'day-20': ("Queen Victoria was the first Cunard ship to feature West End-style private theatre boxes, in her three-storey Royal Court Theatre &ndash; an innovation later copied on sister ship Queen Elizabeth.",
               'Cunard', 'https://www.cunard.com/en-gb/cunard-stories/queen-victoria-in-numbers'),
    'day-21': ("Talamone's Etruscan temple, built in the 4th century BC to honour the god Tinia, once bore a dramatic terracotta pediment depicting the myth of the \"Seven Against Thebes\"; the surviving reliefs are now housed in Florence's Archaeological Museum.",
               "In Vacanza all'Argentario", 'https://www.invacanzaallargentario.it/en/the-etruscan-pediment-of-talamone/'),
    'day-22': ('The name "Chianti" first appears in writing as early as 1398, in a notarial document referring to wine from the area &ndash; centuries before the modern Chianti Classico appellation existed.',
               'Consorzio Vino Chianti Classico', 'https://www.chianticlassico.com/en/consortium/history-of-chianti-classico/'),
    'day-23': ("The golden Madonnina statue atop Milan's Duomo secretly doubles as a giant lightning rod &ndash; the metal halberd she holds was engineered to protect the cathedral from lightning strikes.",
               'Duomo di Milano', 'https://www.duomomilano.it/en/art-and-culture/the-madonnina/'),
    'option-a-23sep': ('The Roman writer Pliny the Younger owned two villas on Lake Como which he nicknamed "Comedy" and "Tragedy" &ndash; one perched high with sweeping views, the other so close to the water he claimed he could fish from his bedroom window.',
               "Wikipedia", 'https://en.wikipedia.org/wiki/Pliny%27s_Comedy_and_Tragedy_villas'),
    'option-b-23sep': ('The Ferrari Museum in Maranello opened on 18 February 1990 &ndash; deliberately chosen as the birthday of founder Enzo Ferrari, known as "the Drake", who had died two years earlier in 1988.',
               'VisitModena', 'https://www.visitmodena.it/en/discover-modena/motor-valley/explore-motorvalley/motors-ferrari-museum-in-maranello'),
    'option-c-23sep': ("The Republic of Venice was an independent maritime power for more than 1,100 years, from 697 AD until Napoleon deposed the last doge, Ludovico Manin, in 1797.",
               'World History Encyclopedia', 'https://www.worldhistory.org/article/2273/doges-palace-in-venice/'),
    'day-24': ("Regent's Canal, which runs past The Lighterman, was designed by architect John Nash &ndash; the same man behind Regent Street, Regent's Park and Buckingham Palace &ndash; and opened to great fanfare in 1820.",
               "King's Cross", 'https://www.kingscross.co.uk/history-regents-canal'),
    'day-25': ("The Mousetrap began life as a short BBC radio play called 'Three Blind Mice', which Agatha Christie wrote as an 80th-birthday gift for Queen Mary in 1947, before she expanded it into the stage play in 1952.",
               'Agatha Christie', 'https://www.agathachristie.com/theatre/the-mousetrap'),
    'day-26': ("Hard Rock Cafe's now-famous memorabilia collection began right there in London in 1979, when regular customer Eric Clapton gave the cafe a signed Fender guitar; the venue today also houses 'The Vault', London's only rock-and-roll museum.",
               'Hard Rock International', 'https://www.hardrock.com/our-history'),
    'day-27': ("Heathrow handled just 63,000 passengers in its first full year of operation in 1946; by 2025 that figure had grown to a record 84.5 million passengers in a single year.",
               'Aerospace Global News', 'https://aerospaceglobalnews.com/news/london-heathrow-airport-80-anniversary-history/'),
}

FUN_FACTS_6 = {
    'day-11': ("Cardinal Scipione Borghese amassed a private collection of over 800 sculptures and paintings by artists including Caravaggio, Bernini and Titian, which only became the public Galleria Borghese museum after the Italian state bought the estate from the family in 1902.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Galleria_Borghese'),
    'day-12': ("Michelangelo became chief architect of St Peter's Basilica in 1547 at the age of 71, but only lived to see the drum of its dome completed; his design was finished by Giacomo della Porta and Domenico Fontana in 1590, 26 years after his death.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/St._Peter%27s_Basilica'),
    'day-13': ("The amphitheatre wasn't officially called the Colosseum in ancient times &ndash; it was the Flavian Amphitheatre &ndash; and the popular name actually comes from the Colossus of Nero, a giant bronze statue over 30 metres tall that once stood beside it.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Colossus_of_Nero'),
    'day-14': ("In 1696, Pope Innocent XII declared Civitavecchia a free port, exempting trading ships from certain taxes &ndash; a status that helped it grow into Rome's principal seaport.",
               'Britannica', 'https://www.britannica.com/place/Civitavecchia'),
    'day-15': ("The custom of afternoon tea dates back to the 1840s, credited to Anna, 7th Duchess of Bedford, who began taking tea and a light snack in her rooms to bridge the gap between lunch and dinner &ndash; a habit Queen Victoria herself later helped make fashionable.",
               'British Museum', 'https://www.britishmuseum.org/blog/tea-rific-history-victorian-afternoon-tea'),
    'day-16': ("Marseille's Vieux Port was once spanned by a pioneering transporter bridge, inaugurated in 1905, which carried passengers and vehicles across the harbour entrance on a suspended gondola until German forces destroyed it in 1944.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Marseille_Transporter_Bridge'),
    'day-17': ("Prince Rainier III's 1956 marriage to Hollywood actress Grace Kelly at Monaco's Saint Nicholas Cathedral was watched by more than 30 million television viewers worldwide, dubbed the 'wedding of the century'.",
               'History.com', 'https://www.history.com/this-day-in-history/april-19/grace-kelly-and-prince-rainier-marry'),
    'day-18': ("From the 11th century until Napoleon dissolved it in 1797, Genoa was the seat of its own maritime superpower, the Republic of Genoa, whose fleets and banks once rivalled Venice's.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Republic_of_Genoa'),
    'day-19': ("Legend says Galileo Galilei, who lived in Pisa, dropped two cannonballs of different masses from the tower around 1589-92 to prove they fall at the same speed &ndash; but the only source is a biography written by his student decades later, and historians still dispute whether it happened.",
               'Wikipedia', 'https://en.wikipedia.org/wiki/Leaning_Tower_of_Pisa'),
    'day-20': ("Each year, guests and crew aboard Queen Victoria get through around 1.5 million fresh eggs and close to a million cups of tea.",
               'Cunard', 'https://www.cunard.com/en-gb/cunard-stories/queen-victoria-in-numbers'),
    'day-21': ("San Gimignano grew rich on saffron: medieval merchants exported its \"red gold\" as far as Alexandria and Damietta, and the profits helped fund the stone tower-houses that still define the skyline.",
               'Visit Tuscany', 'https://www.visittuscany.com/en/flavors/san-gimignano-saffron-dop/'),
    'day-22': ("In 1716, Grand Duke Cosimo III de' Medici issued a decree formally defining the boundaries of the Chianti wine-producing zone, making it one of the earliest legally delimited wine regions in the world.",
               'Consorzio Vino Chianti Classico', 'https://www.chianticlassico.com/en/consortium/history-of-chianti-classico/'),
    'day-23': ("From 1939, Milan's golden Madonnina was covered in grey-green camouflage cloth for five years during the Second World War, so Allied bombers couldn't use her golden glint to pinpoint the city.",
               'Duomo di Milano', 'https://www.duomomilano.it/en/art-and-culture/the-madonnina/'),
    'option-a-23sep': ('Julius Caesar conquered the Como area in 49 BC and resettled it with 5,000 colonists, founding "Novum Comum"; the Romans named the lake itself "Larius", the root of its modern name, Como.',
               'Lake Como Tours', 'https://www.lakecomo.tours/a-brief-history-of-the-lake-como-area/'),
    'option-b-23sep': ("Enzo Ferrari personally test-drove every car his factory produced, but for his own daily journeys he had a soft spot for four-seaters &ndash; a preference that ran from the 1960 250 GT 2+2 to the 456 GT he approved in 1988.",
               'Ferrari.com', 'https://www.ferrari.com/en-EN/museums/driven-by-enzo'),
    'option-c-23sep': ("The enclosed Bridge of Sighs, built around 1600, connects the Doge's Palace interrogation rooms to the old prisons; its name comes from the sighs of condemned prisoners glimpsing their last view of Venice through its stone-barred windows.",
               'Britannica', 'https://www.britannica.com/topic/Bridge-of-Sighs'),
    'day-24': ("Granary Square, where The Lighterman sits, was once a Victorian canal basin where barges unloaded wheat for London's bakers; today the same spot features over 1,000 individually choreographed fountains.",
               "King's Cross", 'https://www.kingscross.co.uk/granary-square'),
    'day-25': ("The V&A's National Art Library holds more than 750,000 books, photographs and drawings, including works connected to Leonardo da Vinci's notebooks.",
               'Victoria and Albert Museum', 'https://www.vam.ac.uk/info/national-art-library'),
    'day-26': ("Six the Musical's writers modelled each of Henry VIII's wives on a real pop star &ndash; Catherine of Aragon channels Beyoncé, Anne Boleyn is Avril Lavigne/Lily Allen, Jane Seymour is Adele, Anne of Cleves is Nicki Minaj/Rihanna, and Katherine Howard is Ariana Grande/Britney Spears.",
               'BBC Newsbeat', 'https://feeds.bbci.co.uk/news/newsbeat-45739935'),
    'day-27': ("The Castle's current building on Cowcross Street, Farringdon, is Grade II listed and dates to 1865, sitting just off historic Smithfield Market in the City of London's square mile.",
               'CAMRA', 'https://camra.org.uk/pubs/castle-london-156309'),
}

# Extra quirky/offbeat print-only facts - same rules as FUN_FACTS_5/6 (print-only,
# never shown on screen or in Print Day/Book/section prints). Counts vary per day
# since some quirky angles found in research turned out to duplicate facts already
# used elsewhere on the page and were dropped rather than force a duplicate in.
FUN_FACTS_QUIRKY = {
    'day-11': [
        ("Villa Borghese has a hydraulic 'water clock' (the Pincio Clepsydra) built in 1867-73 that has run continuously ever since, powered only by two seesawing basins of flowing water &ndash; it never needs winding.",
         'Through Eternity Tours', 'https://www.througheternity.com/rome/water-clock-villa-borghese-pincio'),
        ("Cardinal Scipione Borghese was such a ruthless art collector that he once had the painter Domenichino thrown in prison until he handed over a painting the cardinal wanted for his gallery.",
         'RomeHints', 'https://www.romehints.com/en/the-story-of-galleria-borghese-private-collection-then-museum-hosting-caravaggio-raffaello-and-bernini-works/'),
        ("Caravaggio's Madonna and Child with St Anne was rejected by St Peter's Basilica because church officials thought the Madonna looked too much like a real woman off the street &ndash; Cardinal Scipione Borghese snapped it up for his own collection instead.",
         'Sightseeing Experience Magazine', 'https://www.sightseeing-experience.com/magazine/galleria-borghese-rome-bernini-caravaggio-masterpieces/'),
        ("The building now known as Casa del Cinema inside the gardens was once a dairy serving cream and custard, before it became a glitzy 1930s restaurant and later a Dolce Vita-era dance club called 'La Lucciola'.",
         'Turismo Roma', 'https://www.turismoroma.it/en/news/stories-and-hidden-facts-discovering-villa-borghese-through-educational-panels-and-podcasts'),
    ],
    'day-12': [
        ("Michelangelo hated painting the Sistine Chapel ceiling so much he wrote a grumbling poem about it, complaining his stomach was 'squashed under his chin' and that he'd grown a goiter from the strain of looking up for months.",
         'Dutch Fine Paintings', 'https://dutchfinepaintings.com/michelangelos-sistine-chapel-ceiling-fun-facts/'),
        ("A later painter named Daniele da Volterra was hired to paint loincloths and drapery over the nude figures in Michelangelo's Last Judgment &ndash; earning him the permanent nickname 'Il Braghettone', or 'The Breeches-Maker'.",
         'Wikipedia', 'https://en.wikipedia.org/wiki/Daniele_da_Volterra'),
        ("In 1972 a man attacked Michelangelo's Pietà in St Peter's Basilica with a hammer, shouting he was Jesus Christ; the statue was restored and now sits behind bulletproof glass.",
         'EWTN Vatican', 'https://ewtnvatican.com/articles/10-surprising-facts-about-st-peters-basilica-and-the-vatican-3817'),
        ("The gold letters running around the base of St Peter's dome look like modest, ordinary lettering from the floor &ndash; each one is actually about 7 feet tall, roughly the height of an adult man.",
         'EWTN Vatican', 'https://ewtnvatican.com/articles/10-surprising-facts-about-st-peters-basilica-and-the-vatican-3817'),
    ],
    'day-13': [
        ("Beneath the Colosseum's arena floor was the hypogeum, a maze of tunnels and cages with pulley-operated lifts &ndash; gladiators and wild animals could pop up through trapdoors, seemingly out of nowhere, right in front of the crowd.",
         'Through Eternity Tours', 'https://www.througheternity.com/rome/8-fascinating-facts-about-the-colosseum-you-might-not-know'),
        ("Before the underground hypogeum existed, the Colosseum could be flooded for mock naval battles called naumachiae, with small warships fighting it out in a man-made lake inside the arena.",
         'National Geographic', 'https://www.nationalgeographic.com/history/history-magazine/article/roman-mock-naval-sea-battles-naumachia'),
        ("In one bizarre event, the arena floor was landscaped like a forest and stocked with deer, boar and ostriches &ndash; spectators were handed tickets and let loose to hunt the animals themselves and take the meat home.",
         "All That's Interesting", 'https://allthatsinteresting.com/venatio'),
        ("The Colosseum we see today is a bare stone skeleton, but in Roman times it was covered in polished marble and bronze details, making it gleam rather than look like a ruin.",
         'The Colosseum', 'https://www.thecolosseum.org/facts/'),
    ],
    'day-14': [
        ("The French novelist Stendhal &ndash; famous for giving his name to 'Stendhal syndrome', the fainting fits caused by overwhelming art &ndash; once served as the French consul in Civitavecchia.",
         'Roma Experience', 'https://www.romaexperience.com/post/civitavecchia-the-city-port'),
        ("Civitavecchia's harbour fortress is popularly called 'Fort Michelangelo', but that was never its official name &ndash; it was christened Fortress Giulia after Pope Julius II, who commissioned it; Michelangelo is only credited with the top tower.",
         'Cabinet', 'https://www.cabinet.ox.ac.uk/forte-michelangelo-civitavecchia-roma-1508-1535'),
        ("In 1972, workers in Civitavecchia found frescoes hidden under layers of lime and wallpaper that turned out to be near-exact copies of Raphael's frescoes from the Vatican's Room of Heliodorus &ndash; nobody has ever figured out why they're there.",
         'Port Mobility Civitavecchia', 'https://civitavecchia.portmobility.it/en/10-things-maybe-you-dont-know-about-civitavecchia-and-port'),
        ("When Queen Victoria was officially named by the Duchess of Cornwall in 2007, the champagne bottle swung at the bow refused to smash &ndash; considered a maritime bad omen &ndash; so a backup bottle had to be released to finish the job.",
         'UPI', 'https://www.upi.com/Entertainment_News/2007/12/11/Camilla-has-unlucky-break-at-ship-launch/94141197425702/'),
    ],
    'day-15': [
        ("The roaring lion on the Golden Lion pub's signage traces back to the artwork on the launch programme for the original Queen Elizabeth in 1938 &ndash; Cunard's mascot has been guarding the ship's pub ever since.",
         "Paul's Beer & Travel Blog", 'https://baileysbeerblog.blogspot.com/2022/07/gold-red-black-at-queen-mary-2s-golden.html'),
        ("The Golden Lion pubs on Cunard ships serve beers brewed exclusively for the line, including an odd one called 'Breakfast' &ndash; a biscotti-flavoured stout.",
         "Paul's Beer & Travel Blog", 'https://baileysbeerblog.blogspot.com/2022/07/gold-red-black-at-queen-mary-2s-golden.html'),
        ("Tucked among Cunard's white-tie ballrooms and formal dining rooms is a proper English pub complete with a dartboard, karaoke nights and pub quizzes &ndash; a deliberately unpretentious contrast to the rest of the ship.",
         'Cunard', 'https://www.cunard.com/en-us/activity-types/bars-and-lounges/golden-lion-pub'),
    ],
    'day-16': [
        ("There's a Marseille saying that 'it was the sardine that blocked the port' &ndash; a real 1780 incident where a warship called the Sartine ran aground at the harbour mouth got garbled over time into a legend about a giant fish plugging the port.",
         'Connexion France', 'https://www.connexionfrance.com/magazine/when-and-why-do-we-say-cest-la-sardine-qui-a-bouche-le-port-de-marseille/395138'),
        ("Coffee first entered France through Marseille in 1644, and the city opened its first coffeehouse in 1671 &ndash; a full year before Paris got one.",
         'All About Coffee', 'https://ukersallaboutcoffee.wordpress.com/chapter5/'),
    ],
    'day-17': [
        ("Monaco has no airport, so getting there means arriving by helicopter, superyacht or train &ndash; yet the tiny 2-square-kilometre country still packs in a network of public tunnels, escalators and lifts to move people up and down its cliffside terrain.",
         'Trafalgar', 'https://www.trafalgar.com/real-word/11-crazy-facts-billionaires-playground-monaco/'),
        ("Monaco's royal couple are both genuine Olympians &ndash; Prince Albert II competed in bobsleigh at five consecutive Winter Olympics, while Princess Charlene won swimming medals for South Africa before becoming a princess.",
         'Trafalgar', 'https://www.trafalgar.com/real-word/11-crazy-facts-billionaires-playground-monaco/'),
        ("Monaco is watched over by more than 560 CCTV cameras and has roughly one police officer for every 60 residents, giving it one of the highest security-personnel densities of any country on Earth.",
         'Trafalgar', 'https://www.trafalgar.com/real-word/11-crazy-facts-billionaires-playground-monaco/'),
    ],
    'day-18': [
        ("Genoa's medieval cathedral, San Lorenzo, still has an unexploded WWII naval shell embedded in its side wall &ndash; it crashed through during a 1941 bombardment and simply never went off.",
         'Atlas Obscura', 'https://www.atlasobscura.com/things-to-do/genoa-italy/architecture'),
        ("Beneath Genoa's streets lies a hidden network of WWII-era escape tunnels and bomb shelters, including a 150-metre passage burrowed under the Doge's Palace.",
         'myCityHunt', 'https://www.mycityhunt.com/explorer-blog/10-facts-about-genoa-you-didnt-know-519'),
        ("Genoa's harbour lighthouse, La Lanterna, can claim the title of the tallest traditional lighthouse in the world, depending on how you measure it.",
         'Atlas Obscura', 'https://www.atlasobscura.com/things-to-do/genoa-italy/architecture'),
        ("Palazzo San Giorgio, once home to one of the oldest banks in the world, is also where Marco Polo is said to have dictated his famous travel memoirs.",
         'Atlas Obscura', 'https://www.atlasobscura.com/places/palazzo-san-giorgio'),
    ],
    'day-19': [
        ("The Leaning Tower of Pisa's largest bell weighs around 3,600kg &ndash; about the same as a full-grown female African elephant.",
         'The Fact Site', 'https://www.thefactsite.com/pisa-tower-facts/'),
        ("In 1944, a 23-year-old American sergeant was ordered to check the tower for German snipers before possibly calling in an artillery strike &ndash; he couldn't bring himself to destroy something so beautiful, and the tower survived the war.",
         'The Fact Site', 'https://www.thefactsite.com/pisa-tower-facts/'),
        ("Pisa's famous tilt isn't unique &ndash; the bell tower of the nearby Church of St Nicola leans too, thanks to the same soft ground.",
         'Fact City', 'https://facts.uk/facts-about-the-leaning-tower-of-pisa/'),
        ("The tower's bells haven't rung properly in over 100 years &ndash; partly because one of them, the 'Bell of the Traitor', traditionally tolled whenever a criminal was executed.",
         'Fact City', 'https://facts.uk/facts-about-the-leaning-tower-of-pisa/'),
    ],
    'day-20': [
        ("Queen Victoria has the first two-storey library ever built at sea, stocked with around 6,000 books, journals and periodicals.",
         "Chris Frame's Cunard Page", 'https://www.chriscunard.com/queenvictoria/qv-facts/'),
        ("The ship's Winter Garden has a retractable glass roof that can be opened to the sky &ndash; a colonial-style conservatory built right into a working ocean liner.",
         "Chris Frame's Cunard Page", 'https://www.chriscunard.com/queenvictoria/qv-facts/'),
        ("Queen Victoria's six main suites are each named after a historic Cunard liner &ndash; Mauretania, Laconia, Aquitania, Berengaria, Carpathia and Caronia.",
         "Chris Frame's Cunard Page", 'https://www.chriscunard.com/queenvictoria/qv-facts/'),
    ],
    'day-21': [
        ("The 1280 Torre Chigi in San Gimignano has its front door on the first floor &ndash; residents climbed a ladder to get in and pulled it up at night so rival families couldn't attack them in their sleep.",
         'Torciano Magazine', 'https://magazine.torciano.com/en/san-gimignano-towers-torre-chigi/'),
        ("Talamone doubled as a Tuscan hideaway in the James Bond film Quantum of Solace &ndash; 007 arrives by boat near the medieval Torre di Talamonaccio on the coast.",
         'James Bond Lifestyle', 'https://www.jamesbondlifestyle.com/product/villa-le-torre-talamone-southern-tuscany-italy'),
        ("Admiral Horatio Nelson dropped anchor off Talamone in June 1798 while hunting for Napoleon's fleet, just weeks before his decisive victory at the Battle of the Nile.",
         'My Kind of Italy', 'https://www.mykindofitaly.com/post/talamone-tuscany'),
    ],
    'day-22': [
        ("Renaissance master Giorgio Vasari painted the black rooster into his 1565 'Allegory of Chianti' ceiling panel in Florence's Palazzo Vecchio, cementing it as the region's symbol centuries before it appeared on a wine label.",
         'Chianti Classico Consorzio', 'https://www.chianticlassico.com/en/trademark/history-of-the-black-rooster/'),
        ("The Chianti Classico black rooster trademark is so tightly policed that, since 2005, a bottle without the rooster on its label legally isn't allowed to call itself Chianti Classico at all.",
         'Chianti Classico Consorzio', 'https://www.chianticlassico.com/en/trademark/history-of-the-black-rooster/'),
    ],
    'day-23': [
        ("The Galleria's floor mosaics depict four cities of the newly unified Kingdom of Italy as animals &ndash; Turin as a bull, Rome as a wolf, Florence as a lily, and Milan as its own red cross.",
         'The Art Post Blog', 'https://www.theartpostblog.com/en/bull-galleria-milan/'),
    ],
    'option-a-23sep': [
        ("Villa d'Este in Cernobbio started life in 1568 as a cardinal's summer retreat, later passed through the hands of a ballerina, a Napoleonic general and an exiled queen, and only became a hotel in 1873.",
         'Historic Hotels of the World', 'http://www.historichotelsthenandnow.com/villaestecernobbio.html'),
        ("From parts of Cernobbio you genuinely can't tell where Italy ends and Switzerland begins &ndash; the town blends into Chiasso just across the invisible border on the forested slopes of Mount Bisbino.",
         'Lake Como Travel', 'https://lakecomotravel.com/cernobbio/'),
        ("Harry's Bar in Cernobbio was opened in 1973 by Piero Sacchi, who wanted to bring the American cocktail-bar trend to Lake Como &ndash; its decor has barely changed since.",
         "Harry's Bar Cernobbio", 'https://www.harrysbarcernobbio.it/en/about-us/'),
    ],
    'option-b-23sep': [
        ("The Ferrari Museum's futuristic entrance was designed by Renzo Piano, the same architect behind the Pompidou Centre in Paris &ndash; a design flourish for a factory that started out with a modest 1947 gate.",
         'Ferrari.com', 'https://www.ferrari.com/en-EN/museums/ferrari-maranello'),
        ("Next to the museum runs the 'Strada della Storia' (History Trail), a red pedestrian path through the park with plaques tracing a decade of Ferrari and Maranello history each.",
         'Maranello Plus', 'https://www.maranelloplus.com/en/places/il-museo-ferrari/'),
        ("Visitors to the museum can try a real Formula 1 pit-stop wheel change against the clock &ndash; the same task F1 crews do in under 2-3 seconds during a race.",
         'Ferrari.com Museums', 'https://www.ferrari.com/en-EN/museums'),
        ("Maranello sits deep in Italy's balsamic vinegar country, and several local tour operators combine a Ferrari Museum visit with a traditional balsamic vinegar tasting tour &ndash; supercars and 12-year-aged vinegar, back to back.",
         'Expedia', 'https://www.expedia.com.my/things-to-do/maranello-ferrari-museum-balsamic-vinegar-tour.a514248.activity-details'),
    ],
    'option-c-23sep': [
        ("Venice's Acqua Alta bookshop keeps its stock safe from flooding canals by storing books inside full-size gondolas, bathtubs and even a rowing boat &ndash; when the water rises, the 'shelves' simply float.",
         'Rosemary and Pork Belly', 'https://rosemaryandporkbelly.co.uk/quirky-venice/'),
        ("The city is built on more than 100 small islands, held up by wooden piles driven into the lagoon mud &ndash; starved of oxygen, the wood never rotted and instead petrified into something as hard as stone over the centuries.",
         'Our Escape Clause', 'https://www.ourescapeclause.com/fun-facts-about-venice-interesting/'),
        ("Tucked in Venice is the Scala Contarini del Bovolo, a spiralling external staircase so distinctive it gave the noble family who built it the nickname 'Bovolo' &ndash; Venetian dialect for 'snail'.",
         'Atlas Obscura', 'https://www.atlasobscura.com/users/blackbolt616/lists/venice-italy'),
        ("Lazzaretto Nuovo, one of Venice's lagoon islands, was used as a plague quarantine station centuries ago and is linked to local legend of the so-called 'Vampire of Venice' &ndash; a skeleton found buried with a brick wedged in its jaw.",
         'Atlas Obscura', 'https://www.atlasobscura.com/users/blackbolt616/lists/venice-italy'),
    ],
    'day-24': [
        ("In 1874 a barge loaded with gunpowder exploded under Macclesfield Bridge on Regent's Canal, killing four people, destroying the bridge and reportedly terrifying the animals at nearby London Zoo.",
         'London Museum', 'https://www.londonmuseum.org.uk/collections/london-stories/regents-canal/'),
        ("The Coal Drops Yard arches near King's Cross weren't always shops and restaurants &ndash; in the Victorian era, gangs of famously tough, muscular women worked there unloading up to 30 wagon-loads of glass bottles a day for a bottle merchant.",
         "King's Cross", 'https://www.kingscross.co.uk/meet-mr-coal-drops'),
        ("Long before its boutique-shop makeover, the grimy Victorian coal-drop arches were home to the nightclub Bagley's, which packed in up to 2,500 clubbers on a Saturday night at the height of London's warehouse rave scene.",
         "King's Cross", 'https://www.kingscross.co.uk/meet-mr-coal-drops'),
    ],
    'day-25': [
        ("In March 1974 The Mousetrap moved from the Ambassadors Theatre to the St Martin's Theatre next door &ndash; and pulled off the entire transfer over a single weekend without missing one single performance.",
         'Wikipedia', 'https://en.wikipedia.org/wiki/The_Mousetrap'),
        ("Agatha Christie was so sure The Mousetrap wouldn't last that she predicted it might run eight months. It has now passed 30,000 performances and is still the longest-running show of any kind in the world.",
         'Wikipedia', 'https://en.wikipedia.org/wiki/The_Mousetrap'),
        ("The V&A's collection includes an antique French chair reputed to be haunted &ndash; visitors and staff have long claimed its cushion mysteriously deflates several times a day, as if someone invisible keeps sitting down.",
         'Time Out London', 'https://www.timeout.com/london/blog/ten-weird-and-fascinating-things-every-londoner-needs-to-see-at-the-victoria-albert-museum-103116'),
        ("Among the V&A's oddest objects is Tippoo's Tiger, a life-size 18th-century wooden automaton of a tiger mauling a British soldier &ndash; originally fitted with an organ mechanism that made the soldier's arm flail and produced groaning sounds.",
         'Time Out London', 'https://www.timeout.com/london/blog/ten-weird-and-fascinating-things-every-londoner-needs-to-see-at-the-victoria-albert-museum-103116'),
    ],
    'day-26': [
        ("The Tower of London's ravens are technically enlisted members of the armed forces and can be formally 'dismissed' for misconduct &ndash; Raven George was sacked in 1986 for destroying television aerials and exiled to a zoo in Wales.",
         'Wikipedia', 'https://en.wikipedia.org/wiki/Ravens_of_the_Tower_of_London'),
        ("Anne Boleyn's now-iconic space buns in Six the Musical weren't scripted &ndash; original West End cast member Millie O'Connell simply wore her hair that way at a 2018 preview, the creative team loved it, and it became the character's permanent look.",
         'Beano', 'https://www.beano.com/facts/music/six-the-musical-facts'),
    ],
    'day-27': [
        ("Despite terminals numbered 2 through 5, Heathrow has no Terminal 1 in use today &ndash; it opened in 1968 and was permanently closed in 2015 after 47 years of service.",
         'Fact City', 'https://facts.uk/interesting-facts-about-london-heathrow-airport/'),
        ("If Heathrow's control tower ever went out of action, a secret windowless backup replica of the tower's visual control room, hidden away from the airfield, can take over and keep up to 70% of flights running.",
         'Surrey Live', 'https://www.getsurrey.co.uk/news/local-news/heathrow-airport-fascinating-secret-facts-18565532'),
        ("Heathrow's Animal Reception Centre processes an extraordinary menagerie every year &ndash; around 28,000 fish, 2,000 birds and up to 200,000 reptiles pass through the airport.",
         'Surrey Live', 'https://www.getsurrey.co.uk/news/local-news/heathrow-airport-fascinating-secret-facts-18565532'),
        ("Nearby Farringdon has an oddly split identity: since 1394 it's been divided into 'Farringdon Within' and 'Farringdon Without', depending on which side of the old Roman London Wall each half fell on.",
         'London x London', 'https://www.londonxlondon.com/london-area-guides/farringdon/'),
    ],
}

FUN_FACTS_PAGE_ORDER = [
    'day-11', 'day-12', 'day-13', 'day-14', 'day-15', 'day-16', 'day-17', 'day-18', 'day-19', 'day-20',
    'day-21', 'day-22', 'day-23',
    'option-a-23sep', 'option-b-23sep', 'option-c-23sep',
    'day-24', 'day-25', 'day-26', 'day-27',
]

OPTION_FUN_FACT_LABELS = {
    'option-a-23sep': "Option A &ndash; Lake Como &amp; Harry's Bar",
    'option-b-23sep': 'Option B &ndash; Ferrari Maranello',
    'option-c-23sep': 'Option C &ndash; Venice',
}

def fun_facts_day_label(day_id):
    m = re.match(r'day-(\d{1,2})$', day_id)
    if m:
        dom = int(m.group(1))
        d = datetime.date(2026, 9, dom)
        trip_day = dom - (TRIP_START_DATE.day - 1)
        return f'{d.strftime("%A")} {_ordinal(dom)} September (Day {trip_day})'
    if day_id in OPTION_FUN_FACT_LABELS:
        return f'Wednesday 23rd September (Day 14) &ndash; {OPTION_FUN_FACT_LABELS[day_id]}'
    return day_id

def fun_facts_print_only(day_id):
    facts = [f for f in (FUN_FACTS_5.get(day_id), FUN_FACTS_6.get(day_id)) if f]
    facts.extend(FUN_FACTS_QUIRKY.get(day_id, []))
    return facts

def fun_facts_page_html():
    blocks = []
    for did in FUN_FACTS_PAGE_ORDER:
        facts = fun_facts_print_only(did)
        if not facts:
            continue
        facts_html = ''.join(_one_fact_html(f) for f in facts)
        blocks.append(f'''
      <div class="ffp-day">
        <h3 class="ffp-day-title">{fun_facts_day_label(did)}</h3>
        {facts_html}
      </div>''')
    return ''.join(blocks)

def _one_fact_html(fact):
    text, source_label, source_url = fact
    source_html = f' <span class="fun-fact-source">&mdash; <a href="{source_url}" target="_blank">{esc(source_label)}</a></span>' if source_url else ''
    return f'<div class="fun-fact-text">{text}{source_html}</div>'

def fun_fact_box(day_id):
    facts = [f for f in (FUN_FACTS.get(day_id), FUN_FACTS_2.get(day_id), FUN_FACTS_3.get(day_id), FUN_FACTS_4.get(day_id)) if f]
    if not facts:
        return ''
    facts_html = ''.join(_one_fact_html(f) for f in facts)
    return f'''
    <div class="fun-fact-box">
      <div class="fun-fact-label">&#127881; Fun Fact{'s' if len(facts) > 1 else ''}</div>
      {facts_html}
    </div>'''

def day_card(day, theme, day_id=None, day_map=None, dinner_html=None, quicklink_html=None, option_html=None):
    blocks = collapse_events(day['events'])
    rows = ''
    for b in blocks:
        addr = f'<div class="ev-addr">{esc(b["address"])}</div>' if b['address'] else ''
        weblink_url = weblink_for(b['name'])
        weblink_btn = f'<a class="pill pill-website" href="{esc(weblink_url)}" target="_blank">Website</a>' if weblink_url else ''
        directions_url = directions_for(b['name'])
        directions_btn = f'<a class="pill pill-directions" href="{esc(directions_url)}" target="_blank">Directions</a>' if directions_url else ''
        instagram_url = instagram_for(b['name'])
        instagram_btn = f'<a class="pill pill-instagram" href="{esc(instagram_url)}" target="_blank" title="Instagram link">I</a>' if instagram_url else ''
        menu_url = menu_for(b['name'])
        menu_btn = f'<a class="pill pill-weblink" href="{esc(menu_url)}" target="_blank">Menu</a>' if menu_url else ''
        tripadvisor_url = tripadvisor_for(b['name'])
        tripadvisor_btn = f'<a class="pill pill-review" href="{esc(tripadvisor_url)}" target="_blank">TripAdvisor</a>' if tripadvisor_url else ''
        booking_link = booking_link_for(b['name'])
        booking_btn = f'<a class="pill pill-booking" href="{esc(booking_link[1])}" target="_blank">{esc(booking_link[0])}</a>' if booking_link else ''
        link_row = weblink_btn + menu_btn + tripadvisor_btn + booking_btn + directions_btn + instagram_btn
        logo_url = logo_for(b['name'])
        logo_html = f'<img class="ev-logo" src="{logo_url}" alt="Hard Rock Cafe London logo">' if logo_url else ''
        shops = shoplist_for(b['name'])
        shops_html = shoplist_html(shops) if shops else ''
        if shops:
            shops_html += ROLLING_STONES_HTML
        photo_url = event_photo_for(b['name'])
        photo_html = (
            f'<img class="ev-photo" src="{esc(photo_url)}" alt="{esc(b["name"])}" '
            f'loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">'
        ) if photo_url else ''
        walk_route = walk_route_for(b['name'])
        walk_html = walk_route_html(walk_route) if walk_route else ''
        if photo_html or walk_html:
            photo_html = f'<div class="ev-photo-row">{photo_html}{walk_html}</div>'
        travel_opts = travel_options_for(b['name'])
        travel_opts_html = travel_options_html(travel_opts) if travel_opts else ''
        ev_fact_html = event_fact_for(b['name']) or ''
        ev_phone = event_phone_for(b['name'])
        ev_w3w = event_w3w_for(b['name'])
        w3w_html = f'<a class="w3w-badge" href="https://what3words.com/{esc(ev_w3w)}" target="_blank" title="what3words location">///{esc(ev_w3w)}</a>' if ev_w3w else ''
        ev_phone_html = f'<div class="ev-addr">&#128222; {esc(ev_phone)} {w3w_html}</div>' if ev_phone else (f'<div class="ev-addr">{w3w_html}</div>' if w3w_html else '')
        ev_note = event_note_for(b['name'])
        ev_note_html = f'<div class="ev-note">({ev_note})</div>' if ev_note else ''
        ev_qr = event_qr_for(b['name'])
        ev_qr_html = (
            f'<div class="ev-qr"><a href="{esc(ev_qr[0])}" target="_blank" title="Scan or click for website">'
            f'<img src="data:image/png;base64,{ev_qr[1]}" alt="QR code to website" width="88" height="88"></a>'
            f'<div class="ev-qr-label">Website</div></div>'
        ) if ev_qr else ''
        rows += f'''
        <div class="ev-row">
          <div class="ev-time">{esc(b['time_display'])}</div>
          <div class="ev-body">
            <div class="ev-name">{esc(b['name'])} {badge(b['status'])} {logo_html}</div>
            {addr}
            {ev_phone_html}
            {ev_note_html}
            {f'<div class="ev-link">{link_row}</div>' if link_row else ''}
            {ev_qr_html}
            {shops_html}
            {photo_html}
            {travel_opts_html}
            {ev_fact_html}
          </div>
        </div>'''
    stay = f'<div class="ev-stay">\U0001F3E8 {esc(stay_with_address(day["stay"]))}</div>' if day.get('stay') else ''
    where = where_for_day(day['title'])
    where_html = f'<span class="day-loc">{esc(where)}</span>' if where else ''
    print_day_btn = f'<button class="print-mini print-day-btn no-print" onclick="printDay(\'{day_id}\')">Print Day</button>' if day_id else ''
    day_id_attr = f' data-day-id="{day_id}"' if day_id else ''
    map_html = day_map_box(day_map) if day_map else ''
    fact_html = fun_fact_box(day_id) if day_id else ''
    return f'''
    <div class="day-card theme-{theme}"{day_id_attr}>
      <div class="day-head"><span class="day-title">{esc(day_heading_display(day['title']))}</span><span class="day-head-right">{print_day_btn}{where_html}</span></div>
      <div class="day-body">
        {fact_html}
        {quicklink_html or ''}
        {rows if rows else '<div class="ev-empty">Free / unplanned time</div>'}
        {option_html or ''}
        {dinner_html or ''}
        {stay}
        {map_html}
      </div>
    </div>'''

def day_map_box(day_map):
    n = len(day_map['stops'])
    items = ''
    for i, stop in enumerate(day_map['stops']):
        items += f'''
        <div class="dm-stop">
          <div class="dm-dot"></div>
          <div class="dm-stop-body">
            <div class="dm-name">{esc(stop['name'])}</div>
            {f'<div class="dm-note">{esc(stop.get("note"))}</div>' if stop.get('note') else ''}
          </div>
        </div>'''
        if i < n - 1:
            leg = day_map['legs'][i]
            items += f'''
        <div class="dm-leg">
          <div class="dm-leg-line"></div>
          <div class="dm-leg-body">
            <div class="dm-leg-head">{esc(stop['name'])} &rarr; {esc(day_map['stops'][i+1]['name'])}</div>
            <div class="dm-leg-text">{esc(leg['time'])} &middot; {esc(leg['distance'])} &middot; {esc(leg['method'])}</div>
          </div>
        </div>'''
    return f'''
    <div class="day-map-box">
      <div class="day-map-title">{esc(day_map.get('title') or "Today's Places & Suggested Routes")}</div>
      <div class="day-map-timeline">{items}</div>
      <div class="day-map-caption">Schematic order of the day &ndash; not to scale. Times/distances/routes are estimates; check live transit apps on the day.</div>
    </div>'''

def place_card(p, with_review=False):
    photo = p.get('photo')
    website_target = p.get('menu') or p.get('website')
    links = ''
    if not photo and p.get('website'):
        links += f'<a class="pill pill-website" href="{esc(p["website"])}" target="_blank">Website</a>'
    if p.get('menu'):
        links += f'<a class="pill pill-weblink" href="{esc(p["menu"])}" target="_blank">Menu</a>'
    if p.get('gmap'):
        links += f'<a class="pill" href="{esc(p["gmap"])}" target="_blank">Map</a>'
    if with_review and p.get('review'):
        links += f'<a class="pill pill-review" href="{esc(p["review"])}" target="_blank">Reviews</a>'
    if p.get('instagram'):
        links += f'<a class="pill pill-instagram" href="{esc(p["instagram"])}" target="_blank" title="Instagram link">I</a>'
    photo_block = ''
    if photo:
        website_btn = f'<a class="pill place-website-btn" href="{esc(website_target)}" target="_blank">Website</a>' if website_target else ''
        photo_block = (
            f'<img class="place-photo" src="{esc(photo)}" alt="{esc(p["place"])}" '
            f'loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">'
            f'<div class="place-photo-btn">{website_btn}</div>'
        )
    fact_html = f'<div class="place-fact">&#128161; {esc(p["fact"])}</div>' if p.get('fact') else ''
    hours_html = f'<div class="place-hours">&#128337; {esc(p["hours"])}</div>' if p.get('hours') else ''
    phone_html = f'<div class="place-hours">&#128222; {esc(p["phone"])}</div>' if p.get('phone') else ''
    email_html = f'<div class="place-hours">&#9993;&#65039; {esc(p["email"])}</div>' if p.get('email') else ''
    w3w_html = f'<a class="w3w-badge" href="https://what3words.com/{esc(p["w3w"])}" target="_blank" title="what3words location">///{esc(p["w3w"])}</a>' if p.get('w3w') else ''
    return f'''
    <div class="place-card">
      {photo_block}
      <div class="place-name">{esc(p['place'])} {w3w_html}</div>
      <div class="place-type">{esc(p.get('type') or '')}</div>
      <div class="place-addr">{esc(p.get('address') or '')}</div>
      {hours_html}
      {phone_html}
      {email_html}
      <div class="place-links">{links}</div>
      {fact_html}
    </div>'''

ROLLING_STONES_SHOP = {
    'place': 'RS No.9 Carnaby (Official Rolling Stones Store)',
    'type': "The Rolling Stones' official flagship store - clothing, vinyl and memorabilia, plus a Ronnie Wood art exhibition in the basement (~12 min walk via Regent Street/Carnaby Street)",
    'address': '9 Carnaby St, Carnaby, London W1F 9PE',
    'hours': 'Mon-Sat 11am-7pm, Sun 12pm-6pm',
    'website': 'https://therollingstonesshop.com/pages/rs-no-9',
    'gmap': 'https://www.google.com/maps/dir/?api=1&destination=9%20Carnaby%20St%2C%20Carnaby%2C%20London%20W1F%209PE&travelmode=walking',
    'photo': 'https://therollingstonesshop.com/cdn/shop/files/133_2Q6A0102-Gavsy-Media.jpg',
    'w3w': 'catch.future.librarian',
}
ROLLING_STONES_HTML = f'''
<div class="shop-list" style="margin-top:14px;">
  <div class="shop-list-title">Also worth a look:</div>
  <div class="place-grid" style="max-width:340px;">{place_card(ROLLING_STONES_SHOP)}</div>
</div>'''

def ttc_row(t):
    todo_btn = '<span class="pill pill-todo">TO DO</span>' if t.get('status') in ('To Book', 'To Confirm') else ''
    return f'''
    <tr>
      <td class="ttc-day">{esc(t['day'])}</td>
      <td>{esc(t['item'])} {todo_btn}</td>
      <td>{badge(t['status'])}</td>
      <td class="ttc-notes">{esc(t.get('notes') or '')}</td>
    </tr>'''

def ntb_row(n):
    web = f'<a class="pill" href="{esc(n["website"])}" target="_blank">Visit</a>' if n.get('website') else ''
    review = f'<a class="pill pill-review" href="{esc(n["review"])}" target="_blank">Reviews</a>' if n.get('review') else ''
    flag_html = f'<div class="ntb-flag">{esc(n["flag"])}</div>' if n.get('flag') else ''
    w3w_html = f'<a class="w3w-badge" href="https://what3words.com/{esc(n["w3w"])}" target="_blank" title="what3words location">///{esc(n["w3w"])}</a>' if n.get('w3w') else ''
    return f'''
    <tr>
      <td class="ntb-date">{esc(n['date'])}</td>
      <td>{esc(n['item'])} {w3w_html}</td>
      <td>{badge(n['status'])}</td>
      <td class="ntb-notes">{esc(n.get('notes') or '')}{flag_html}</td>
      <td class="ntb-tick"><span class="tickbox"></span></td>
      <td>{web}{review}</td>
    </tr>'''

def tt_row(t, idx):
    tt_id = f"tt-{idx}-{re.sub(r'[^a-z0-9]+', '-', t['item'].lower()).strip('-')}"
    return f'''
    <tr>
      <td>{esc(t['item'])}</td>
      <td class="tt-tick"><input type="checkbox" class="tt-check" id="{tt_id}" data-tt-id="{tt_id}"></td>
    </tr>'''

italy_days = sched['italy']
rome_days = italy_days[0:3]
cruise_days = italy_days[3:10]
tuscany_days = italy_days[10:12]
milan_days = italy_days[12:13]
london_days = sched['london']

def dinner_box(title, options):
    cards = ''.join(place_card(p, with_review=True) for p in options)
    return f'''
    <div class="dinner-box">
      <div class="day-map-title">{esc(title)}</div>
      <div class="place-grid">{cards}</div>
    </div>'''

DINNER_11SEP = [
    {'place': 'Trimani Il Winebar', 'type': "Rome's original wine bar (est. 1821 as a wine merchant) - simple Roman menu, huge wine list, fair prices",
     'address': 'Via Cernaia 37 - ~3 min walk', 'website': 'http://www.trimani.com/',
     'hours': 'Mon-Sat 11:30am-3pm & 5:30pm-midnight (closed Sun)',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d798184-Reviews-Trimani_Il_Winebar-Rome_Lazio.html',
     'fact': "Trimani started life in 1821 as a family wine merchant business - it's still run by the same Trimani family six generations later, and was the first place in the world to actually call itself a \"Wine Bar\"."},
    {'place': 'Rifugio Romano', 'type': 'Cosy trattoria a couple of minutes from Termini - classic Roman pastas, friendly service',
     'address': 'Via Volturno 12 - ~6 min walk', 'website': 'https://www.thefork.it/ristorante/rifugio-romano',
     'hours': 'Tue-Sun 12:30pm-11pm (closed Mon)',
     'review': 'https://www.tripadvisor.com/RestaurantsNear-g187791-d246155-Piazza_della_Repubblica-Rome_Lazio.html'},
    {'place': 'Osteria Quarantaquattro', 'type': 'Relaxed osteria near Piazza della Repubblica - Roman staples, good value set menus',
     'address': 'Via Volturno area - ~6 min walk', 'website': 'https://www.thefork.it/',
     'hours': 'Check ahead - hours not consistently published',
     'review': 'https://www.tripadvisor.com/RestaurantsNear-g187791-d246155-Piazza_della_Repubblica-Rome_Lazio.html'},
    {'place': 'Pizzeria Ristoro Est! Est!! Est!!!', 'type': "Rome's oldest pizzeria (since 1905) - thin-crust Roman-style pizza, great old-school atmosphere",
     'address': 'Via Genova 32 - ~8 min walk', 'website': 'https://pizzeriaristoroestestest.com/en/',
     'hours': 'Check ahead - typically lunch & dinner daily',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d696551-Reviews-Pizzeria_Ristoro_Est_Est_Est-Rome_Lazio.html',
     'fact': 'The odd name comes from a medieval legend: a bishop travelling to Rome sent his servant ahead to chalk "Est!" (Latin for "it is [good]") on the doors of inns with good wine. At Montefiascone the wine was so good the servant wrote "Est! Est!! Est!!!" three times - the bishop loved it so much he settled there for the rest of his life.'},
    {'place': 'Osteria Barberini', 'type': 'Cosy osteria near Piazza Barberini - known for truffle dishes and classic Roman cuisine',
     'address': 'Via della Purificazione 21 - ~17 min walk', 'website': 'https://www.osteriabarberini.it/',
     'hours': 'Mon-Sat 12:30-2:30pm & 7-11pm (closed Sun)',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1573090-Reviews-Osteria_Barberini-Rome_Lazio.html'},
    {'place': "Trattoria dell'Omo", 'type': 'Probably the closest proper trattoria to Termini - traditional Roman menu that changes by the day (gnocchi on Thursdays)',
     'address': 'Via Vicenza 18 - ~5 min walk', 'website': None,
     'hours': 'Daily 12pm-3pm & 7pm-10:45pm',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d2324300-Reviews-Trattoria_dell_Omo-Rome_Lazio.html'},
    {'place': 'La Matriciana dal 1870', 'type': 'Rome institution since 1870 opposite the Opera House - the amatriciana it\'s named after, plus classic carbonara',
     'address': 'Via del Viminale 44 - ~10 min walk', 'website': 'https://www.lamatriciana.it/en/',
     'hours': 'Sun-Fri 12:15-3pm & 7:15-11pm (closed Sat)',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1086681-Reviews-La_Matriciana-Rome_Lazio.html'},
    {'place': 'Trattoria Monti', 'type': 'Long-running family trattoria near Piazza Vittorio serving Le Marche regional dishes - olive ascolane, tortello al rosso d\'uovo. Book ahead, it\'s popular',
     'address': 'Via di San Vito 13 - ~12 min walk', 'website': None,
     'hours': 'Check ahead - reservations recommended',
     'review': 'https://www.tripadvisor.com/Restaurants-g187791-zfn7230918-Rome_Lazio.html'},
]

DINNER_12SEP = [
    {'place': 'Ai Tre Scalini - Bottiglieria dal 1895', 'type': 'Historic Monti wine bar (since 1895) - great wines by the glass, traditional small plates, lively atmosphere',
     'address': 'Via Panisperna 251, Monti - ~15 min walk', 'website': None,
     'hours': 'Daily 12pm-10pm',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1187387-Reviews-Ai_Tre_Scalini_Bottiglieria_dal_1895-Rome_Lazio.html',
     'fact': 'The name means "at the three steps" - a nod to the three little steps down into its cosy, cellar-like wine bar, which has barely changed since it opened in 1895.'},
    {'place': 'La Carbonara', 'type': 'Rome institution since 1906, famous for its namesake dish - carbonara, amatriciana, cacio e pepe',
     'address': 'Via Panisperna 214, Monti - ~15 min walk', 'website': None,
     'hours': 'Mon-Sat 12:30-2:30pm & 7-11pm (closed Sun)',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1016936-Reviews-La_Carbonara-Rome_Lazio.html',
     'fact': "Ironically, this restaurant opened in 1906 - decades before food historians think the dish carbonara was even invented (most trace it to Rome in the 1940s, possibly influenced by American GI rations of eggs and bacon)."},
    {'place': 'Al Vino al Vino', 'type': 'Intimate Monti enoteca (since 1999) - excellent wine list by the glass, sweet-and-sour eggplant caponata',
     'address': 'Via dei Serpenti 19, Monti - ~14 min walk', 'website': None,
     'hours': 'Mon-Thu & Sun 7pm-midnight, Fri-Sat 7pm-1:30am',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1063520-Reviews-Al_Vino_al_Vino-Rome_Lazio.html'},
    {'place': 'La Taverna dei Monti', 'type': 'Popular traditional trattoria - carbonara, cacio e pepe and other Roman staples done well',
     'address': 'Via del Boschetto 41, Monti - ~15 min walk', 'website': None,
     'hours': 'Tue-Sun 12:30pm-11pm (closed Mon)',
     'review': 'https://www.tripadvisor.com/RestaurantsNear-g187791-d6704256-Rione_Monti-Rome_Lazio.html'},
    {'place': 'Alle Carrette', 'type': 'One of the best-loved pizzerias in Monti - good prices, lovely courtyard seating out back',
     'address': 'Vicolo delle Carrette, Monti - ~16 min walk', 'website': None,
     'hours': 'Check ahead - published hours conflict between sources',
     'review': 'https://www.tripadvisor.com/RestaurantsNear-g187791-d6704256-Rione_Monti-Rome_Lazio.html'},
    {'place': 'Maharajah', 'type': 'Well-rated Indian restaurant in the middle of Monti - good change of pace if craving something other than Italian',
     'address': 'Via dei Serpenti 124, Monti - ~14 min walk', 'website': 'https://www.maharajah1.com/index-en.html',
     'hours': 'Mon-Thu 12:30-3pm & 7:30pm-midnight (check ahead for weekends)',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d795697-Reviews-Maharajah-Rome_Lazio.html'},
    {'place': 'Temakinho', 'type': 'Fun Brazilian-Japanese fusion (sushi meets caipirinha) - colourful spot a few steps from the Colosseum end of Monti',
     'address': 'Via dei Serpenti 16, Monti - ~13 min walk', 'website': 'https://www.temakinho.com/',
     'hours': 'Daily 12-3:30pm & 7-11:30pm',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d5612568-Reviews-Temakinho_Rome_Monti-Rome_Lazio.html'},
    {'place': 'Taverna Romana', 'type': 'Popular family-run local spot known for authentic Roman cuisine and reasonable prices - book ahead as it fills fast',
     'address': 'Via della Madonna dei Monti 79, Monti - ~14 min walk', 'website': None,
     'hours': 'Mon-Sat 12-3pm & 7:30-11pm (closed Sun)',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1943547-Reviews-Taverna_Romana-Rome_Lazio.html'},
]

DINNER_13SEP = [
    {'place': 'Hostaria al Boschetto', 'type': 'Warm, cosy Roman comfort food - a Monti favourite, fair prices',
     'address': 'Via del Boschetto, Monti - ~15 min walk', 'website': None,
     'hours': 'Check ahead - hours not consistently published',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1067222-Reviews-Hostaria_Al_Boschetto-Rome_Lazio.html'},
    {'place': 'Urbana 47', 'type': 'Farm-to-table Italian - seasonal, organic produce with a modern twist on Roman classics',
     'address': 'Via Urbana 47, Monti - ~15 min walk', 'website': 'https://urbana47.com/?lang=en',
     'hours': 'Daily 8:30am-midnight',
     'review': None},
    {'place': 'La Bottega del Caffè', 'type': 'Lively bar/trattoria right on the prettiest square in Monti - good for a relaxed evening',
     'address': 'Piazza Madonna dei Monti 5, Monti - ~16 min walk', 'website': None,
     'hours': 'Mon-Sat 8am-2am, Sun 9am-2am',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1150937-Reviews-Bottega_del_Caffe-Rome_Lazio.html'},
    {'place': 'Ornelli Black Angus Steakhouse', 'type': "TripAdvisor 4.8★ - top-rated steakhouse, handy since it's right near where today's Colosseum tour finishes",
     'address': 'Via Merulana 224 - ~20 min walk from hotel, ~5 min from the Colosseum', 'website': None,
     'hours': 'Closed Mondays - check ahead for exact times',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d2206695-Reviews-Ornelli_Black_Angus_Steakhouse-Rome_Lazio.html'},
    {'place': 'Cuoco & Camicia', 'type': 'TripAdvisor 4.5★ - relaxed elegance, modern Italian cuisine, near the Colosseum end of the tour',
     'address': 'Near Cavour/Colosseum - ~22 min walk from hotel, ~5 min from the Colosseum', 'website': 'https://www.cuocoecamicia.it/en/',
     'hours': 'Check ahead - hours not consistently published',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d2391713-Reviews-Cuoco_Camicia-Rome_Lazio.html'},
    {'place': 'Trattoria Vecchia Roma', 'type': "Traveller's Choice 2025 winner, est. 1916 - famous for its Amatriciana Flambé, near Piazza Vittorio",
     'address': 'Via Ferruccio 12B/C, Esquilino - ~18 min walk', 'website': None,
     'hours': 'Mon-Sat 12:30-3pm & 7-11pm (closed Sun)',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1584357-Reviews-Trattoria_Vecchia_Roma-Rome_Lazio.html'},
    {'place': 'Le Caveau', 'type': "Traveller's Choice-rated Italian restaurant near Piazza Vittorio - fried baby octopus, burrata, good all-rounder",
     'address': 'Via Conte Verde 6, Esquilino - ~15 min walk', 'website': None,
     'hours': 'Daily 12pm-11pm',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1583145-Reviews-Le_Caveau-Rome_Lazio.html'},
    {'place': 'Hostaria Al Gladiatore', 'type': "Over 200 years serving Roman classics right on Piazza del Colosseo - come for the Colosseum view as much as the carbonara",
     'address': 'Piazza del Colosseo 5 - ~20 min walk from hotel, on the Colosseum square', 'website': None,
     'hours': 'Daily 7am-midnight',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1012381-Reviews-Hostaria_al_Gladiatore-Rome_Lazio.html'},
]

dinner_box_11sep = dinner_box('Dinner Suggestions (8 ideas, within ~20 min walk of the hotel)', DINNER_11SEP)
dinner_box_12sep = dinner_box('8 More Dinner Suggestions (no repeats from the 11th)', DINNER_12SEP)
dinner_box_13sep = dinner_box('8 More Dinner Suggestions (no repeats - handy for after the Colosseum tour)', DINNER_13SEP)

AFTERNOON_12SEP = [
    {'place': 'Trevi Fountain', 'type': 'Iconic baroque fountain - toss a coin in for luck (~15 min walk from hotel)',
     'address': 'Piazza di Trevi, Rome', 'website': None, 'review': None, 'w3w': 'wiped.school.dreaming'},
    {'place': 'Spanish Steps & Piazza di Spagna', 'type': 'Famous steps, great people-watching and shopping nearby (~20 min walk)',
     'address': 'Piazza di Spagna, Rome', 'website': None, 'review': None, 'w3w': 'rungs.diverts.tractor'},
    {'place': 'Pantheon', 'type': 'Best-preserved ancient Roman building, free entry (~20-25 min walk)',
     'address': 'Piazza della Rotonda, Rome', 'website': None, 'review': None, 'w3w': 'strictly.into.evolves'},
    {'place': 'Piazza Navona', 'type': "Grand baroque square with Bernini's Fountain of the Four Rivers, lively cafes (~25-30 min walk or short taxi)",
     'address': 'Piazza Navona, Rome', 'website': None, 'review': None, 'w3w': 'drank.navy.scanning'},
    {'place': 'Galleria Borghese', 'type': 'World-class Bernini/Caravaggio art collection - needs a pre-booked timed entry ticket, so only if booked in advance',
     'address': 'Piazzale Scipione Borghese 5, Rome', 'website': 'https://galleriaborghese.beniculturali.it/en/', 'review': None, 'w3w': 'detained.planting.describe'},
    {'place': "Vatican Necropolis (Scavi Tour) - Tomb of St Peter", 'type': 'Guided tour through the ancient necropolis beneath St Peter\'s Basilica, ending at the tomb believed to hold St Peter\'s remains - must be booked well in advance, no photos allowed, small groups only',
     'address': 'Meet at the Ufficio Scavi (Excavations Office), Piazza San Pietro, Vatican City',
     'website': 'https://www.basilicasanpietro.va/en/products/the-necropolis',
     'review': 'https://www.tripadvisor.com/Attraction_Review-g187793-d195269-Reviews-Necropolis_of_Saint_Peter-Vatican_City_Lazio.html',
     'w3w': 'searched.circling.supposed'},
]
afternoon_box_12sep = dinner_box('Saturday Afternoon Suggestions (6 ideas, after lunch)', AFTERNOON_12SEP)

LUNCH_13SEP = [
    {'place': 'Il Salotto del Colosseo', 'type': 'TripAdvisor 4.7★ - "great lunch by the Colosseum", cosy hidden gem',
     'address': 'Via di S. Giovanni in Laterano 42, Rome - ~2 min from Piazza del Colosseo', 'website': 'https://ilsalottodelcolosseo.it/en/',
     'hours': 'Daily 11am-11:30pm',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d23737738-Reviews-Il_Salotto_Del_Colosseo-Rome_Lazio.html'},
    {'place': 'Fuorinorma', 'type': 'TripAdvisor 4.8★ - "best panini in Rome", fresh charcuterie boards, quick and casual',
     'address': 'Via dei Serpenti 178, Monti - ~10 min walk to Colosseo', 'website': None,
     'hours': 'Mon-Sat 11:30am-11:30pm (closed Sun)',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d12729060-Reviews-Fuorinorma-Rome_Lazio.html'},
    {'place': 'Trattoria Luzzi', 'type': "Bustling local trattoria/pizzeria, a few blocks from the Colosseum - good value, always busy",
     'address': 'Via di San Giovanni in Laterano 88, Rome', 'website': None,
     'hours': 'Mon, Tue, Thu-Sun 12pm-midnight (closed Wed)',
     'review': None},
    {'place': 'Coming Out', 'type': 'TripAdvisor 4.6★ - relaxed all-day cafe/bar right by the Colosseum, big varied menu',
     'address': 'Via San Giovanni in Laterano 8, Rome', 'website': None,
     'hours': 'Check ahead - known for long/late hours but not consistently published',
     'review': None},
    {'place': 'Le Naumachie (Naumachia)', 'type': "Long-running Roman/Tuscan institution near the Colosseum, grilled mains",
     'address': 'Via Celimontana 7, Rome', 'website': 'https://www.naumachiaroma.com/',
     'hours': 'Daily 11am-11:30pm',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1601155-Reviews-Naumachia-Rome_Lazio.html'},
    {'place': 'Cafè Cafè', 'type': 'Relaxed bistro/wine bar near the Colosseum - smoothies, salads and sandwiches, good for a lighter lunch',
     'address': 'Via dei Santi Quattro 44, Rome', 'website': 'https://www.cafecafebistrot.it',
     'hours': 'Mon & Wed-Sun 9:30am-7:45pm, Tue 9:30am-4:15pm',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d1070852-Reviews-Cafe_Cafe-Rome_Lazio.html'},
    {'place': 'Terre e Domus', 'type': "Enoteca run by the Province of Rome next to Trajan's Column - ingredients sourced entirely from the Lazio region",
     'address': 'Foro Traiano 82, Rome', 'website': None,
     'hours': 'Daily 9am-midnight',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d10201057-Reviews-Terre_e_Domus-Rome_Lazio.html'},
    {'place': 'La Taverna dei Quaranta', 'type': 'Family-run local trattoria near the Colosseum, serving since 1984 - authentic Roman classics',
     'address': 'Via Claudia 24, Rome', 'website': 'https://www.latavernadeiquaranta.com/en/',
     'hours': 'Mon-Wed 12-3:30pm & 7:30pm-midnight',
     'review': 'https://www.tripadvisor.com/Restaurant_Review-g187791-d3162638-Reviews-La_Taverna_Dei_Quaranta-Rome_Lazio.html'},
]
lunch_box_13sep = dinner_box('Lunch Suggestions Near Piazza del Colosseo (8 ideas, before the tour)', LUNCH_13SEP)

EXTRA_BOX_BY_DAY = {
    '11 SEP': dinner_box_11sep,
    '12 SEP': afternoon_box_12sep + dinner_box_12sep,
    '13 SEP': lunch_box_13sep + dinner_box_13sep,
}

def dinner_box_for(title):
    for tag, box in EXTRA_BOX_BY_DAY.items():
        if tag in title:
            return box
    return None

def day_id_for(title):
    m = re.search(r'-\s*(\d{1,2})\s*SEP', title, re.I)
    if not m:
        m = re.search(r'\(DAY\s*(\d{1,2})\)', title, re.I)
    if m:
        return f'day-{m.group(1)}'
    if 'OPTION A' in title.upper():
        return 'option-a-23sep'
    if 'OPTION B' in title.upper():
        return 'option-b-23sep'
    if 'OPTION C' in title.upper():
        return 'option-c-23sep'
    return None

TRIP_START_DATE = datetime.date(2026, 9, 10)  # Thu 10 Sept = Trip Day 1

def trip_day_number(d):
    """Given a date (datetime.date or ISO string), return the trip day number (10 Sept = Day 1)."""
    if isinstance(d, str):
        d = datetime.date.fromisoformat(d)
    return (d - TRIP_START_DATE).days + 1

def trip_day_title(title):
    """Rewrite a '(DAY N)' label in a schedule title from the date-of-month number to the trip day number (10 Sept = Day 1), leaving everything else (weekday, '- N SEP' etc) untouched."""
    m = re.search(r'\(DAY\s*(\d{1,2})\)', title, re.I)
    if not m:
        return title
    date_of_month = int(m.group(1))
    trip_day = date_of_month - (TRIP_START_DATE.day - 1)
    return re.sub(r'\(DAY\s*\d{1,2}\)', f'(DAY {trip_day})', title, count=1, flags=re.I)

def _ordinal(n):
    if 11 <= (n % 100) <= 13:
        return f'{n}th'
    return f'{n}' + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')

def day_heading_display(title):
    """Build the full-date day-card heading, e.g. 'Thursday 24th September (Day 15)',
    from a schedule title like 'THURSDAY (DAY 24)' or 'FRIDAY (DAY 11) - 11 SEP'.
    Falls back to trip_day_title()'s output for titles that don't match the weekday+(DAY N) pattern
    (e.g. the Option A/B/C/D headings for 23 Sept)."""
    m = re.match(r'([A-Za-z]+)\s*\(DAY\s*(\d{1,2})\)', title.strip(), re.I)
    if not m:
        return trip_day_title(title)
    weekday, date_of_month = m.group(1).capitalize(), int(m.group(2))
    trip_day = date_of_month - (TRIP_START_DATE.day - 1)
    return f'{weekday} {_ordinal(date_of_month)} September (Day {trip_day})'

FUN_FACTS_PAGE_HTML = fun_facts_page_html()

DAY24_MAP = {
    'title': "Thursday 24 Sept - Today's Places & Suggested Routes",
    'stops': [
        {'name': 'iQ Hotel Milano', 'note': 'Start of day - check out'},
        {'name': 'Milan Linate Airport', 'note': '12:00pm - Return hire car'},
        {'name': 'London Heathrow Airport (Terminal 5)', 'note': '4:50pm - Arrive on flight BA575'},
        {'name': 'The Level at Melia White House', 'note': '6:00pm - Arrive, check in / drop bags'},
        {'name': 'Tapas & Gin for Deb', 'note': 'Tight connection before dinner - venue not yet booked, see Things to Do'},
        {'name': 'The Lighterman, Granary Square', 'note': '6:30pm - Dinner'},
        {'name': 'The Level at Melia White House', 'note': 'Return for the night'},
    ],
    'legs': [
        {'time': '~20 min', 'distance': '~8 km', 'method': 'Drive: iQ Hotel Milano to Milan Linate Airport (car return)'},
        {'time': '~1h 55m flight (dep 3:55pm, arr 4:50pm)', 'distance': '~1,000 km', 'method': 'Flight BA575 (British Airways), Milan Linate to London Heathrow (T5) (~55 min apart on local clocks due to the UK/Italy time difference)'},
        {'time': '~25 min', 'distance': 'n/a', 'method': 'Immigration/border and baggage at Heathrow T5, then meet the Luxury Private Vehicle driver at Meeting Point South, by Caffè Nero'},
        {'time': '~45 min drive', 'distance': '~24 km', 'method': 'Luxury Private Vehicle transfer (The Traveling Group / London Travel In, ref 190826), Heathrow T5 direct to The Level at Meliá White House'},
        {'time': 'Tight - likely won\'t fit', 'distance': 'TBC', 'method': 'Venue not yet booked, and with the corrected BA575/transfer timing there\'s only ~30 min before the 6:30pm Lighterman booking – see Audit/Things to Do'},
        {'time': '~20 min', 'distance': '~1 mile', 'method': 'Walk towards King’s Cross/Granary Square (estimate assumes the Tapas & Gin venue ends up near the hotel – recheck once booked)'},
        {'time': '~20 min', 'distance': '~1.6 km', 'method': 'Walk back via Euston Road (or ~10 min taxi)'},
    ],
}

DAY25_MAP = {
    'title': "Friday 25 Sept - Today's Places & Suggested Routes",
    'stops': [
        {'name': 'The Level at Melia White House', 'note': 'Start of day - Breakfast 8:00am'},
        {'name': 'V&A Museum', 'note': '9:30am'},
        {'name': "Harry's Knightsbridge", 'note': '12:00pm - Early lunch'},
        {'name': 'Oxford Street', 'note': '1:00pm - Free time / shopping'},
        {'name': 'Albert Schloss, Shaftesbury Avenue', 'note': '4:30pm - Dinner'},
        {'name': "St Martin's Theatre", 'note': '6:30pm - The Mousetrap'},
        {'name': 'The Level at Melia White House', 'note': 'Return for the night (after 10:00pm)'},
    ],
    'legs': [
        {'time': '~30-35 min', 'distance': '~6.5 km', 'method': 'Bakerloo line to Piccadilly Circus, change to Piccadilly line to South Kensington, then ~5 min walk (or Circle line via Baker Street, one change)'},
        {'time': '~12-15 min', 'distance': '~1.1 km', 'method': 'Walk via Brompton Road, or 1 stop on the Piccadilly line, South Kensington to Knightsbridge'},
        {'time': '~10-12 min', 'distance': '~3.2 km', 'method': 'Piccadilly line to Green Park, change to Victoria line to Oxford Circus'},
        {'time': '~15 min', 'distance': '~1.3 km', 'method': 'Walk down Regent Street/Shaftesbury Avenue, or 1 stop Central line to Tottenham Court Road + short walk'},
        {'time': '~6-8 min', 'distance': '~0.5 km', 'method': 'Walk along Shaftesbury Avenue'},
        {'time': '~20-25 min', 'distance': '~3.3 km', 'method': "Piccadilly line: Leicester Square to Piccadilly Circus, change to Bakerloo line to Regent's Park, then ~5 min walk"},
    ],
}

DAY26_MAP = {
    'title': "Saturday 26 Sept - Today's Places & Suggested Routes",
    'stops': [
        {'name': 'The Level at Melia White House', 'note': 'Start of day - Longford Street, Regents Park'},
        {'name': 'Tower of London', 'note': '9:00am - Crown Jewels + River Tour'},
        {'name': 'Vaudeville Theatre, Strand', 'note': '3:00pm - Six the Musical'},
        {'name': 'Waterstones Piccadilly', 'note': '5:30pm'},
        {'name': 'Hard Rock Cafe London, Old Park Lane', 'note': '6:45pm - Dinner'},
        {'name': 'The Level at Melia White House', 'note': 'Return for the night'},
    ],
    'legs': [
        {'time': '~30-35 min', 'distance': '~5.7 km', 'method': 'Circle line: Great Portland Street to Tower Hill'},
        {'time': '~20 min', 'distance': '~2.9 km', 'method': 'Circle/District line: Tower Hill to Embankment, then ~5 min walk up the Strand'},
        {'time': '~12-15 min', 'distance': '~1.1 km', 'method': 'Walk via Trafalgar Square/Haymarket, or Covent Garden to Piccadilly Circus (1 stop, Piccadilly line) + short walk'},
        {'time': '~12-15 min', 'distance': '~1.3 km', 'method': 'Walk along Piccadilly towards Hyde Park Corner, or Piccadilly Circus to Hyde Park Corner (1 stop, Piccadilly line) + short walk'},
        {'time': '~20-25 min', 'distance': '~3.4 km', 'method': "Piccadilly line: Hyde Park Corner to Piccadilly Circus, change to Bakerloo line to Regent's Park, then ~5 min walk"},
    ],
}

def simplify_stop_name(name):
    return re.sub(r'\s*\([^()]*\)\s*$', '', name).strip()

def day_route_title(title):
    m = re.search(r'([A-Z]+)\s*\(DAY\s*\d+\)\s*-\s*(\d{1,2})\s*([A-Z]+)', title, re.I)
    if not m:
        return "Today's Places & Suggested Route"
    weekday = m.group(1).capitalize()
    daynum = m.group(2)
    month = m.group(3).capitalize()[:3]
    return f"{weekday} {daynum} {month} - Today's Places & Suggested Route"

def hotel_match(stay_text):
    stay_text = stay_text or ''
    for name, addr in HOTEL_ADDRESS:
        if name in stay_text:
            return name, addr
    return None, None

def auto_day_map(day, theme, prev_stay=None):
    blocks = collapse_events(day['events'])
    stops_src = [b for b in blocks if b.get('address')]
    if len(stops_src) < 2:
        return None
    start_hotel_name, start_hotel_addr = hotel_match(prev_stay)
    end_hotel_name, end_hotel_addr = hotel_match(day.get('stay'))
    is_cruise = theme == 'cruise'
    is_port_day = is_cruise and any('in port' in b['name'].lower() for b in blocks)
    stops = []
    if start_hotel_name and not is_cruise:
        stops.append({'name': start_hotel_name, 'note': f'Start of day - {start_hotel_addr}'})
    for b in stops_src:
        note = b['time_display']
        if b.get('address'):
            note += f" - {b['address']}"
        stops.append({'name': simplify_stop_name(b['name']), 'note': note})
    if end_hotel_name and not is_cruise and simplify_stop_name(stops[-1]['name']) != end_hotel_name:
        stops.append({'name': end_hotel_name, 'note': 'Return for the night'})
    if len(stops) < 2:
        return None
    legs = []
    for i in range(len(stops) - 1):
        if is_cruise and is_port_day:
            legs.append({'time': 'Estimate', 'distance': 'Estimate', 'method': "Ashore in port - taxi, shore excursion coach or walk; confirm with your tour operator or the ship's shore excursion desk"})
        elif is_cruise:
            legs.append({'time': 'Onboard', 'distance': 'Onboard', 'method': 'No transfer needed - both are on the ship'})
        else:
            legs.append({'time': 'Estimate', 'distance': 'Estimate', 'method': 'Walk, taxi or local transport - check live maps for the exact route'})
    return {'title': day_route_title(day['title']), 'stops': stops, 'legs': legs}

DAY_MAPS = {'(DAY 24)': DAY24_MAP, '(DAY 25)': DAY25_MAP, '(DAY 26)': DAY26_MAP}

def day_map_for(title, day=None, theme=None, prev_stay=None):
    for tag, dm in DAY_MAPS.items():
        if tag in title:
            return dm
    if day is not None:
        return auto_day_map(day, theme, prev_stay=prev_stay)
    return None

def sequence_with_prev(days, first_prev=None):
    out = []
    prev = first_prev
    for d in days:
        out.append((d, prev))
        prev = d.get('stay')
    return out

rome_days_html = ''.join(
    day_card(d, 'italy', day_id=day_id_for(d['title']), dinner_html=dinner_box_for(d['title']),
             day_map=day_map_for(d['title'], d, 'italy', prev_stay=prev))
    for d, prev in sequence_with_prev(rome_days)
)
QV_CABIN_BOX_HTML = '''
<div class="cabin-box">
  <div class="cabin-box-title">&#128274; Our Staterooms &ndash; Queen Victoria (Deck 8, Balcony)</div>
  <div class="cabin-row"><span class="cabin-num">8118</span><span class="cabin-who">Gary &amp; Karen</span></div>
  <div class="cabin-row"><span class="cabin-num">8112</span><span class="cabin-who">Deb &amp; Tom</span></div>
  <div class="cabin-note">See the Deck 8 plan above for exact locations.</div>
</div>'''

cruise_days_html = ''.join(
    (QV_CABIN_BOX_HTML if 'DAY 14' in d['title'].upper() else '') +
    day_card(d, 'cruise', day_id=day_id_for(d['title']), day_map=day_map_for(d['title'], d, 'cruise', prev_stay=prev))
    for d, prev in sequence_with_prev(cruise_days, first_prev=rome_days[-1].get('stay') if rome_days else None)
)
tuscany_days_html = ''.join(
    day_card(d, 'tuscany2', day_id=day_id_for(d['title']), day_map=day_map_for(d['title'], d, 'tuscany2', prev_stay=prev))
    for d, prev in sequence_with_prev(tuscany_days, first_prev=cruise_days[-1].get('stay') if cruise_days else None)
)
milan_days_html = ''.join(
    day_card(d, 'milan2', day_id=day_id_for(d['title']), day_map=day_map_for(d['title'], d, 'milan2', prev_stay=prev))
    for d, prev in sequence_with_prev(milan_days, first_prev=tuscany_days[-1].get('stay') if tuscany_days else None)
)
LONDON_QUICKLINKS = (
    '<div class="ev-link london-quicklinks">'
    '<a class="pill pill-directions" href="#melia20">&#128694; Sites within 20m</a>'
    '<a class="pill pill-directions" href="#shops20">&#128722; Shops within 20m</a>'
    '</div>'
)

def bar_card(name, ctype, address, dist1_label, dist1_text, dist2_label, dist2_text, gmap_url, website=None, menu=None, tripadvisor=None, w3w=None, qr=None):
    links = f'<a class="pill" href="{esc(gmap_url)}" target="_blank">Map</a>'
    if website:
        links += f'<a class="pill pill-website" href="{esc(website)}" target="_blank">Website</a>'
    if menu:
        links += f'<a class="pill pill-weblink" href="{esc(menu)}" target="_blank">Menu</a>'
    if tripadvisor:
        links += f'<a class="pill pill-review" href="{esc(tripadvisor)}" target="_blank">TripAdvisor</a>'
    w3w_html = f'<a class="w3w-badge" href="https://what3words.com/{esc(w3w)}" target="_blank" title="what3words location">///{esc(w3w)}</a>' if w3w else ''
    qr_target = website or menu
    qr_html = (
        f'<a class="place-qr-corner" href="{esc(qr_target)}" target="_blank" title="Scan or click for website">'
        f'<img src="data:image/png;base64,{qr}" alt="QR code to {esc(name)} website"></a>'
    ) if qr and qr_target else ''
    return f'''
    <div class="place-card">
      <div class="place-name">{esc(name)} {w3w_html}</div>
      <div class="place-type">{esc(ctype)}</div>
      <div class="place-addr">{esc(address)}</div>
      <div class="place-hours">&#128694; {esc(dist1_label)}: {esc(dist1_text)}</div>
      <div class="place-hours">&#128694; {esc(dist2_label)}: {esc(dist2_text)}</div>
      <div class="place-links">{links}</div>
      {qr_html}
    </div>'''

HRC_BARS = [
    bar_card('Rivoli Bar at The Ritz', 'Art Deco hotel cocktail bar - Ritz signature serves, entered via the main lobby',
             '150 Piccadilly, London W1J 9BR',
             'From Hard Rock', '~15 min walking',
             'To The Melia', '~25 min - walk to Green Park, Piccadilly/Victoria line to Oxford Circus, change to Bakerloo, then ~5 min walk',
             'https://www.google.com/maps/dir/?api=1&origin=150%20Old%20Park%20Lane%2C%20Mayfair%2C%20London%20W1K%201QZ&destination=150%20Piccadilly%2C%20London%20W1J%209BR&travelmode=walking',
             website='https://www.theritzlondon.com/dine-with-us/rivoli-bar/',
             tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d3172284-Reviews-The_Rivoli_Bar-London_England.html',
             w3w='jazz.choice.factories'),
    bar_card('The Connaught Bar', "World-famous cocktail bar - a Mayfair institution, book ahead",
             'Carlos Pl, Mayfair, London W1K 2AL',
             'From Hard Rock', '~12 min walking',
             'To The Melia', '~25 min - walk to Bond Street, Central line to Oxford Circus, change to Bakerloo, then ~5 min walk',
             'https://www.google.com/maps/dir/?api=1&origin=150%20Old%20Park%20Lane%2C%20Mayfair%2C%20London%20W1K%201QZ&destination=Carlos%20Pl%2C%20Mayfair%2C%20London%20W1K%202AL&travelmode=walking',
             website='https://www.maybourne.com/en/hotels/the-connaught/restaurants-bars/connaught-bar',
             tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d6519169-Reviews-The_Connaught_Bar-London_England.html',
             w3w='tamed.zooms.pest'),
    bar_card('Dukes Bar', "Legendary martini bar (since 1908) - birthplace of the 'Vesper' martini style",
              "35 St James's Pl, London SW1A 1NY",
              'From Hard Rock', '~15 min walking',
              'To The Melia', '~30 min - walk to Green Park, Piccadilly line to Piccadilly Circus, change to Bakerloo, then ~5 min walk',
              'https://www.google.com/maps/dir/?api=1&origin=150%20Old%20Park%20Lane%2C%20Mayfair%2C%20London%20W1K%201QZ&destination=35%20St%20James%27s%20Place%2C%20London%20SW1A%201NY&travelmode=walking',
              website='https://www.dukeshotel.com/dukes-bar/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d1014398-Reviews-DUKES_Bar-London_England.html',
              w3w='less.candy.award'),
    bar_card('Blue Bar at The Berkeley', 'Sophisticated hotel cocktail bar in Knightsbridge, David Collins-designed interior',
              'Wilton Pl, Knightsbridge, London SW1X 7RL',
              'From Hard Rock', '~26 min walking',
              'To The Melia', '~30 min - walk to Hyde Park Corner, Piccadilly line to Piccadilly Circus, change to Bakerloo, then ~5 min walk',
              'https://www.google.com/maps/dir/?api=1&origin=150%20Old%20Park%20Lane%2C%20Mayfair%2C%20London%20W1K%201QZ&destination=Wilton%20Place%2C%20Knightsbridge%2C%20London%20SW1X%207RL&travelmode=walking',
              website='https://www.the-berkeley.co.uk/blue-bar',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d23586783-Reviews-Blue_Bar_The_Berkeley-London_England.html',
              w3w='flame.fears.retail'),
]

MELIA_BARS = [
    bar_card('The Lucky Pig', 'Speakeasy-style basement cocktail bar, just off Great Portland Street',
              '5 Clipstone St, London W1W 6BB',
              'From The Melia', '~6 min walking',
              "To Hard Rock", "~25 min - Bakerloo line from Regent's Park/Great Portland Street to Piccadilly Circus, change to Piccadilly line to Hyde Park Corner, then ~5 min walk",
              'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=5%20Clipstone%20St%2C%20London%20W1W%206BB&travelmode=walking',
              website='https://www.theluckypig.co.uk/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d2659449-Reviews-The_Lucky_Pig_Cocktail_Bar-London_England.html'),
    bar_card('The George, Fitzrovia', 'Grade II listed 18th-century corner pub with an ornate Italianate facade',
              '55 Great Portland St, London W1W 7LQ',
              'From The Melia', '~5 min walking',
              "To Hard Rock", "~25 min - Bakerloo line from Regent's Park/Great Portland Street to Piccadilly Circus, change to Piccadilly line to Hyde Park Corner, then ~5 min walk",
              'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=55%20Great%20Portland%20St%2C%20London%20W1W%207LQ&travelmode=walking',
              website='https://thegeorge.london/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d6405157-Reviews-The_George-London_England.html',
              w3w='moss.fend.agrees'),
    bar_card('Artesian at The Langham', "Multi-award-winning hotel cocktail bar - voted World's Best Bar for years running",
              '1c Portland Pl, London W1B 1JA',
              'From The Melia', '~13 min walking',
              "To Hard Rock", "~20 min - Bakerloo line from Regent's Park/Great Portland Street to Piccadilly Circus, change to Piccadilly line to Hyde Park Corner, then ~5 min walk",
              'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=1c%20Portland%20Place%2C%20London%20W1B%201JA&travelmode=walking',
              website='https://www.artesian-bar.co.uk/', menu='https://www.artesian-bar.co.uk/menus/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d730307-Reviews-Artesian-London_England.html',
              w3w='nights.truly.squad'),
    bar_card('The Social', 'Long-running Fitzrovia bar and music venue, intimate upstairs bar plus basement gigs/DJ sets',
              '5 Little Portland St, London W1W 7JD',
              'From The Melia', '~9 min walking',
              "To Hard Rock", "~25 min - Bakerloo line from Regent's Park/Great Portland Street to Piccadilly Circus, change to Piccadilly line to Hyde Park Corner, then ~5 min walk",
              'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=5%20Little%20Portland%20St%2C%20London%20W1W%207JD&travelmode=walking',
              website='https://www.thesocial.com/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d5220327-Reviews-The_Social-London_England.html'),
]

LIGHTERMAN_BARS = [
    bar_card('The Parcel Yard', "Grade I listed Fuller's pub inside King's Cross station itself",
              "King's Cross Station, London N1 9AL",
              'From The Lighterman', '~8 min walking',
              'To The Melia', "~15 min - Circle/Hammersmith & City/Metropolitan line direct from King's Cross St Pancras to Great Portland Street (2 stops), then ~3 min walk",
              'https://www.google.com/maps/dir/?api=1&origin=3%20Granary%20Square%2C%20London%20N1C%204BH&destination=King%27s%20Cross%20Station%2C%20London%20N1%209AL&travelmode=walking',
              website='https://www.parcelyard.co.uk/', menu='https://www.parcelyard.co.uk/food/menus',
              tripadvisor='https://www.tripadvisor.co.uk/Restaurant_Review-g186338-d2690666-Reviews-The_Parcel_Yard_King_s_Cross-London_England.html',
              qr=BAR_QR['The Parcel Yard']),
    bar_card('Big Chill Bar', 'Three-storey bar/club with a roof terrace, near the station',
              '257-259 Pentonville Rd, London N1 9NL',
              'From The Lighterman', '~10 min walking',
              'To The Melia', "~15 min - Circle/Hammersmith & City/Metropolitan line direct from King's Cross St Pancras to Great Portland Street (2 stops), then ~3 min walk",
              'https://www.google.com/maps/dir/?api=1&origin=3%20Granary%20Square%2C%20London%20N1C%204BH&destination=257-259%20Pentonville%20Rd%2C%20London%20N1%209NL&travelmode=walking',
              website='https://www.bigchillbar.com/kings-cross',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d1906552-Reviews-Big_Chill_Kings_Cross-London_England.html',
              qr=BAR_QR['Big Chill Bar']),
    bar_card('The Racketeer', 'Independent, family-run cocktail and wine bar',
              "105 King's Cross Rd, London WC1X 9LR",
              'From The Lighterman', '~12 min walking',
              'To The Melia', "~15 min - Circle/Hammersmith & City/Metropolitan line direct from King's Cross St Pancras to Great Portland Street (2 stops), then ~3 min walk",
              'https://www.google.com/maps/dir/?api=1&origin=3%20Granary%20Square%2C%20London%20N1C%204BH&destination=105%20King%27s%20Cross%20Rd%2C%20London%20WC1X%209LR&travelmode=walking',
              website='https://www.theracketeer.co.uk/', menu='https://www.theracketeer.co.uk/menu',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d12608553-Reviews-The_Racketeer-London_England.html',
              qr=BAR_QR['The Racketeer']),
    bar_card('Spiritland King\'s Cross', 'Music-focused listening bar with a serious sound system and a well-executed cocktail list',
              '9-10 Stable St, London N1C 4AB',
              'From The Lighterman', '~2 min walking',
              'To The Melia', "~15 min - Circle/Hammersmith & City/Metropolitan line direct from King's Cross St Pancras to Great Portland Street (2 stops), then ~3 min walk",
              'https://www.google.com/maps/dir/?api=1&origin=3%20Granary%20Square%2C%20London%20N1C%204BH&destination=9-10%20Stable%20St%2C%20London%20N1C%204AB&travelmode=walking',
              website='https://spiritland.com/location/spiritland-kings-cross/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d11718544-Reviews-Spiritland_King_s_Cross-London_England.html',
              qr=BAR_QR["Spiritland King's Cross"]),
]

MOUSETRAP_BARS = [
    bar_card('Covent Garden Social Club', "Original London Cocktail Club venue, now independent",
              '6-7 Great Newport St, London WC2H 7JB',
              "From St Martin's Theatre", '~2 min walking',
              'To The Melia', "~25 min - Piccadilly line from Leicester Square to Piccadilly Circus, change to Bakerloo to Great Portland Street, then ~3 min walk",
              "https://www.google.com/maps/dir/?api=1&origin=West%20Street%2C%20London%20WC2H%209NZ&destination=6-7%20Great%20Newport%20St%2C%20London%20WC2H%207JB&travelmode=walking",
              website='https://coventgardensocialclub.co.uk/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d27287603-Reviews-Covent_Garden_Social_Club-London_England.html',
              w3w='begins.jumpy.bake'),
    bar_card('Phoenix Artist Club', 'Theatrical cocktail bar and cabaret club beneath the Phoenix Theatre',
              '1 Phoenix St, London WC2H 8BU',
              "From St Martin's Theatre", '~3 min walking',
              'To The Melia', "~25 min - Piccadilly line from Leicester Square to Piccadilly Circus, change to Bakerloo to Great Portland Street, then ~3 min walk",
              "https://www.google.com/maps/dir/?api=1&origin=West%20Street%2C%20London%20WC2H%209NZ&destination=1%20Phoenix%20St%2C%20London%20WC2H%208BU&travelmode=walking",
              website='https://phoenixartsclub.com/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d1389726-Reviews-Phoenix_Arts_Club-London_England.html',
              w3w='meant.costs.defend'),
    bar_card("The Alchemist St Martin's Lane", 'Theatrical cocktails and post-theatre menu, right around the corner',
              "63-66 St Martin's Ln, London WC2N 4JS",
              "From St Martin's Theatre", '~4 min walking',
              'To The Melia', "~25 min - Piccadilly line from Leicester Square to Piccadilly Circus, change to Bakerloo to Great Portland Street, then ~3 min walk",
              "https://www.google.com/maps/dir/?api=1&origin=West%20Street%2C%20London%20WC2H%209NZ&destination=63-66%20St%20Martin%27s%20Lane%2C%20London%20WC2N%204JS&travelmode=walking",
              website='https://thealchemistbars.com/venues/london/st-martins-lane/',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d15321975-Reviews-The_Alchemist_St_Martins_Lane-London_England.html'),
    bar_card('American Bar at The Savoy', "The original 1893 cocktail bar - a London institution, book ahead",
              'The Savoy, Strand, London WC2R 0EU',
              "From St Martin's Theatre", '~10 min walking',
              'To The Melia', "~25 min - Piccadilly line from Covent Garden to Piccadilly Circus, change to Bakerloo to Great Portland Street, then ~3 min walk",
              "https://www.google.com/maps/dir/?api=1&origin=West%20Street%2C%20London%20WC2H%209NZ&destination=The%20Savoy%2C%20Strand%2C%20London%20WC2R%200EU&travelmode=walking",
              website='https://www.thesavoylondon.com/restaurants-and-bars/american-bar',
              tripadvisor='https://www.tripadvisor.com/Restaurant_Review-g186338-d1010143-Reviews-American_Bar-London_England.html'),
]

SAT26_BARS_HTML = f'''
<div class="dinner-box">
  <div class="day-map-title">After Hard Rock: Nightcap Options</div>
  <p class="lede" style="margin:0 0 10px;">Estimates only &ndash; check live transit apps on the day.</p>
  <div class="option-box-sub"><strong>4 bars near Hard Rock Cafe:</strong></div>
  <div class="place-grid">{''.join(HRC_BARS)}</div>
  <div class="option-box-sub" style="margin-top:14px;"><strong>4 bars near The Melia:</strong></div>
  <div class="place-grid">{''.join(MELIA_BARS)}</div>
</div>'''

THU24_BARS_HTML = f'''
<div class="dinner-box">
  <div class="day-map-title">After The Lighterman: Nightcap Options</div>
  <p class="lede" style="margin:0 0 10px;">Estimates only &ndash; check live transit apps on the day.</p>
  <div class="place-grid">{''.join(LIGHTERMAN_BARS)}</div>
  <div class="travel-opts" style="margin-top:16px;">
    <div class="travel-opts-title">Getting back to The Melia (approx, from the King's Cross area):</div>
    <div class="travel-opt"><span class="travel-opt-label">Uber</span> approx. £8-£14 (UberX, ~10-15 min depending on traffic; more at busy times)</div>
    <div class="travel-opt"><span class="travel-opt-label">Tube</span> Circle/Hammersmith &amp; City/Metropolitan line direct from King's Cross St Pancras to Great Portland Street (2 stops), then ~3 min walk - about 15 min total, approx. £3.00 pay-as-you-go</div>
    <div class="travel-opt"><span class="travel-opt-label">Walking</span> approx. 25-30 min, ~1.3 miles via Euston Road</div>
  </div>
</div>'''

FRI25_BARS_HTML = f'''
<div class="dinner-box">
  <div class="day-map-title">After The Mousetrap: Nightcap Options</div>
  <p class="lede" style="margin:0 0 10px;">Estimates only &ndash; check live transit apps on the day.</p>
  <div class="place-grid">{''.join(MOUSETRAP_BARS)}</div>
</div>'''

LONDON_TUBE_INFO_HTML = '''
<div class="option-box tube-info-box">
  <div class="option-box-title">Getting Around: Tube Map &amp; Travel Pass</div>
  <div class="option-box-sub"><strong>Nearest station to the hotel:</strong> Great Portland Street (Circle, Hammersmith &amp; City, Metropolitan lines) &ndash; approx. 2-3 min walk (~0.2 km), directly opposite The Level at Meli&aacute; White House.</div>
  <div class="ev-link" style="margin:6px 0 12px;">
    <a class="pill pill-directions" href="https://content.tfl.gov.uk/standard-tube-map.pdf" target="_blank">&#128506;&#65039; CLICK HERE for the Official TfL Tube Map (PDF)</a>
  </div>
  <div class="option-box-sub"><strong>Getting a travel pass for the few days:</strong></div>
  <p class="lede" style="margin:4px 0;"><strong>Contactless bank card / Apple Pay / Google Pay</strong> &ndash; simplest option for most visitors. Just tap in and out at the yellow readers on the Tube, buses, DLR, Overground and Elizabeth line &ndash; no need to buy anything in advance. Fares are automatically capped at around &pound;8.90/day for Zones 1-2 (2026 rate), so a few days of sightseeing between Zone 1 (central London) and Zone 2 (Regent's Park/Camden area) should never cost more than the daily cap, even if you tap in and out a lot. Check your bank doesn't charge foreign transaction fees before relying on this.</p>
  <p class="lede" style="margin:4px 0;"><strong>Visitor Oyster card</strong> &ndash; order online before you fly (from about &pound;5 plus however much credit you preload) or buy a standard Oyster card at any station on arrival (&pound;7 refundable deposit). Works exactly like contactless with the same daily cap, and avoids any card fees or acceptance issues. Top up at station machines or the TfL Oyster app.</p>
  <p class="lede" style="margin:4px 0;"><strong>7 Day Travelcard</strong> &ndash; only worth considering if doing lots of travel every single day; for a 4-day stay like this one, pay-as-you-go (contactless or Oyster) with the daily cap works out cheaper and more flexible.</p>
  <div class="ev-link">
    <a class="pill" href="https://visitorshop.tfl.gov.uk/" target="_blank">Order a Visitor Oyster Card</a>
    <a class="pill" href="https://tfl.gov.uk/fares/find-fares/tube-and-rail-fares" target="_blank">Current TfL Fares</a>
  </div>
</div>'''

CASTLE_PHOTO = 'https://commons.wikimedia.org/wiki/Special:FilePath/The%20Castle%2C%20Farringdon%20-%20geograph.org.uk%20-%205107529.jpg'
SIR_JOHN_OLDCASTLE_PHOTO = 'https://www.jdwetherspoon.com/wp-content/uploads/2024/03/430-feature.jpg'
CASTLE_W3W = 'range.return.colleague'
SIR_JOHN_OLDCASTLE_W3W = 'twin.milk.hurry'
CASTLE_W3W_HTML = f'<a class="w3w-badge" href="https://what3words.com/{esc(CASTLE_W3W)}" target="_blank" title="what3words location">///{esc(CASTLE_W3W)}</a>' if CASTLE_W3W else ''
SIR_JOHN_OLDCASTLE_W3W_HTML = f'<a class="w3w-badge" href="https://what3words.com/{esc(SIR_JOHN_OLDCASTLE_W3W)}" target="_blank" title="what3words location">///{esc(SIR_JOHN_OLDCASTLE_W3W)}</a>' if SIR_JOHN_OLDCASTLE_W3W else ''
CASTLE_OPTION1_HTML = f'''
<div class="option-box">
  <div class="option-box-title">Option 1: Lunch at The Castle or The Sir John Oldcastle, Farringdon</div>
  <div class="option-box-sub">Two pub options right by Farringdon station &ndash; a laid-back lunch stop before heading to the airport.</div>
  <div class="option-box-sub"><strong>Getting there:</strong> Great Portland Street &rarr; Farringdon on the Metropolitan/Circle/Hammersmith &amp; City line, direct (no change), ~6 min journey, then ~2-3 min walk from Farringdon station to either pub.</div>
  <div class="place-grid place-grid-wide">
    <div class="place-card">
      <img class="place-photo" src="{esc(CASTLE_PHOTO)}" alt="The Castle, Farringdon" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display='none'">
      <div class="place-name">The Castle {CASTLE_W3W_HTML}</div>
      <div class="place-type">Grade II listed pub &amp; restaurant, est. 1865 &ndash; British pub food, craft beer, full bar, only pawnbroker's licence in London</div>
      <div class="place-addr">34-35 Cowcross St, Farringdon, London EC1M 6DB</div>
      <div class="place-hours">&#128337; Sun 12pm-10:30pm (check ahead for any Sept 2026 changes)</div>
      <div class="place-hours">&#128222; +44 20 7553 7621</div>
      <div class="place-links">
        <a class="pill pill-website" href="https://www.thecastlefarringdon.co.uk" target="_blank">Website</a>
        <a class="pill pill-weblink" href="https://www.thecastlefarringdon.co.uk/food" target="_blank">Menu</a>
        <a class="pill" href="https://www.google.com/maps/dir/?api=1&amp;origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&amp;destination=34-35%20Cowcross%20St%2C%20Farringdon%2C%20London%20EC1M%206DB&amp;travelmode=transit" target="_blank">Map</a>
        <a class="pill pill-instagram" href="https://www.instagram.com/castleec1/" target="_blank" title="Instagram link">I</a>
      </div>
    </div>
    <div class="place-card">
      <img class="place-photo" src="{esc(SIR_JOHN_OLDCASTLE_PHOTO)}" alt="The Sir John Oldcastle, Farringdon" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display='none'">
      <div class="place-name">The Sir John Oldcastle {SIR_JOHN_OLDCASTLE_W3W_HTML}</div>
      <div class="place-type">JD Wetherspoon pub, named after the historical figure said to have inspired Shakespeare's Falstaff &ndash; British pub food, full bar, right next to Farringdon station</div>
      <div class="place-addr">29-35 Farringdon Rd, Farringdon, London EC1M 3JF</div>
      <div class="place-hours">&#128337; Sun 8am-11:30pm (check ahead for any Sept 2026 changes)</div>
      <div class="place-hours">&#128222; 020 7242 1013</div>
      <div class="place-links">
        <a class="pill pill-website" href="https://www.jdwetherspoon.com/pubs/the-sir-john-oldcastle-farringdon/" target="_blank">Website</a>
        <a class="pill" href="https://www.google.com/maps/dir/?api=1&amp;origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&amp;destination=29-35%20Farringdon%20Rd%2C%20Farringdon%2C%20London%20EC1M%203JF&amp;travelmode=transit" target="_blank">Map</a>
        <a class="pill pill-review" href="https://www.tripadvisor.com/Restaurant_Review-g186338-d2708382-Reviews-The_Sir_John_Oldcastle-London_England.html" target="_blank">TripAdvisor</a>
      </div>
    </div>
  </div>
</div>'''

LONDON_OPTION_HTML = {
    'SUNDAY (DAY 27)': CASTLE_OPTION1_HTML,
}
LONDON_DINNER_HTML = {
    'THURSDAY (DAY 24)': THU24_BARS_HTML,
    'FRIDAY (DAY 25)': FRI25_BARS_HTML,
    'SATURDAY (DAY 26)': SAT26_BARS_HTML,
}
london_days_html = ''.join(
    day_card(d, 'london', day_id=day_id_for(d['title']), day_map=day_map_for(d['title'], d, 'london', prev_stay=prev),
             quicklink_html=LONDON_QUICKLINKS,
             option_html=LONDON_OPTION_HTML.get(d['title']),
             dinner_html=LONDON_DINNER_HTML.get(d['title']))
    for d, prev in sequence_with_prev(london_days, first_prev=milan_days[-1].get('stay') if milan_days else None)
)

MELIA_20 = [
    {'place': "The Regent's Park", 'type': 'Royal park right across the road - gardens, boating lake, rose garden (~1-2 min walk)',
     'address': 'Chester Rd, London NW1 4NR',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Chester%20Rd%2C%20London%20NW1%204NR&travelmode=walking'},
    {'place': 'London Zoo', 'type': "World-famous zoo, inside Regent's Park (~15 min walk)",
     'address': "Outer Circle, Regent's Park, London NW1 4RY", 'website': 'https://www.zsl.org/zsl-london-zoo',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Outer%20Circle%2C%20Regent%27s%20Park%2C%20London%20NW1%204RY&travelmode=walking'},
    {'place': "Regent's Park Open Air Theatre", 'type': 'Outdoor theatre - plays, concerts, events, seasonal (~15 min walk)',
     'address': "Inner Circle, Regent's Park, London NW1 4NU", 'website': 'https://openairtheatre.com/',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Inner%20Circle%2C%20Regent%27s%20Park%2C%20London%20NW1%204NU&travelmode=walking'},
    {'place': 'Sherlock Holmes Museum', 'type': "Recreated Victorian rooms at the famous '221B' address (~10 min walk)",
     'address': '221b Baker St, London NW1 6XE', 'website': 'https://www.sherlock-holmes.co.uk/',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=221b%20Baker%20St%2C%20London%20NW1%206XE&travelmode=walking'},
    {'place': 'Madame Tussauds London', 'type': 'Waxworks - celebrities, royals, film characters (~10 min walk)',
     'address': 'Marylebone Rd, London NW1 5LR', 'website': 'https://www.madametussauds.com/london/',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Marylebone%20Rd%2C%20London%20NW1%205LR&travelmode=walking'},
    {'place': 'Baker Street', 'type': 'Iconic street, tube station, shops and cafes (~9 min walk)',
     'address': 'Baker St, London NW1',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Baker%20St%2C%20London%20NW1&travelmode=walking'},
    {'place': 'Marylebone High Street', 'type': "Boutique shops, cafes and Daunt Books' famous store (~14 min walk)",
     'address': 'Marylebone High St, London W1U',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Marylebone%20High%20St%2C%20London%20W1U&travelmode=walking'},
    {'place': 'The Wallace Collection', 'type': 'Free national museum - art, armour and furniture (~16 min walk)',
     'address': 'Hertford House, Manchester Square, London W1U 3BN', 'website': 'https://www.wallacecollection.org/',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Hertford%20House%2C%20Manchester%20Square%2C%20London%20W1U%203BN&travelmode=walking'},
    {'place': 'BBC Broadcasting House', 'type': 'Iconic Art Deco home of the BBC (~9 min walk)',
     'address': 'Portland Pl, London W1A 1AA',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Portland%20Pl%2C%20London%20W1A%201AA&travelmode=walking'},
    {'place': 'All Souls Church, Langham Place', 'type': "Nash's striking circular church next to the BBC (~9 min walk)",
     'address': '2 All Souls Pl, London W1B 3DA',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=2%20All%20Souls%20Pl%2C%20London%20W1B%203DA&travelmode=walking'},
    {'place': 'RIBA (Royal Institute of British Architects)', 'type': 'Free exhibitions, cafe and bookshop (~8 min walk)',
     'address': '66 Portland Pl, London W1B 1AD', 'website': 'https://www.architecture.com/',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=66%20Portland%20Pl%2C%20London%20W1B%201AD&travelmode=walking'},
    {'place': 'Great Portland Street shops & cafes', 'type': 'Right outside the hotel - cafes, restaurants, shops (~1-2 min walk)',
     'address': 'Great Portland St, London W1W',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Great%20Portland%20St%2C%20London%20W1W&travelmode=walking'},
    {'place': 'Charlotte Street, Fitzrovia', 'type': 'Buzzy strip of restaurants and bars (~15 min walk)',
     'address': 'Charlotte St, London W1T',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Charlotte%20St%2C%20London%20W1T&travelmode=walking'},
    {'place': "Regent's Canal towpath", 'type': "Scenic canal walk along the edge of Regent's Park (~12 min walk)",
     'address': "Regent's Canal, London NW1",
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Regent%27s%20Canal%2C%20London%20NW1&travelmode=walking'},
    {'place': 'Euston Square & UCL area', 'type': 'University quarter with green squares (~10 min walk)',
     'address': 'Euston Square Gardens, London NW1 2EF',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Euston%20Square%20Gardens%2C%20London%20NW1%202EF&travelmode=walking'},
    {'place': 'Wellcome Collection', 'type': 'Free museum exploring medicine, art and science (~10 min walk)',
     'address': '183 Euston Rd, London NW1 2BE', 'website': 'https://wellcomecollection.org/',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=183%20Euston%20Rd%2C%20London%20NW1%202BE&travelmode=walking'},
    {'place': 'London Central Mosque', 'type': "Striking gold-domed mosque on the edge of Regent's Park (~14 min walk)",
     'address': '146 Park Rd, London NW8 7RG',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=146%20Park%20Rd%2C%20London%20NW8%207RG&travelmode=walking'},
    {'place': 'Cumberland Terrace', 'type': "One of Regent's Park's grandest Nash terraces (~12 min walk)",
     'address': 'Cumberland Terrace, London NW1 4HE',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Cumberland%20Terrace%2C%20London%20NW1%204HE&travelmode=walking'},
    {'place': 'Oxford Circus & top of Oxford Street', 'type': 'Flagship shopping - Regent Street meets Oxford Street (~17 min walk)',
     'address': 'Oxford Circus, London W1B',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Oxford%20Circus%2C%20London%20W1B&travelmode=walking'},
    {'place': 'Primrose Hill', 'type': 'Park hill with panoramic skyline views over London (~19 min walk)',
     'address': 'Primrose Hill, London NW1 4NR',
     'gmap': 'https://www.google.com/maps/dir/?api=1&origin=Longford%20Street%2C%20Regents%20Park%2C%20London%20NW1%203UP%2C%20UK&destination=Primrose%20Hill%2C%20London%20NW1%204NR&travelmode=walking'},
]

def wm(filename):
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(filename)

MELIA_PHOTOS = {
    "The Regent's Park": wm("The Inner Circle, Regent's Park, London - DSCF0451.JPG"),
    'London Zoo': wm('Entrance to London Zoo - geograph.org.uk - 2271535.jpg'),
    "Regent's Park Open Air Theatre": wm("Regent's Park Open Air Theatre Auditorium.JPG"),
    'Sherlock Holmes Museum': wm('221B Baker Street, London - Sherlock Holmes Museum.jpg'),
    'Madame Tussauds London': wm('Madame Tussauds London.jpg'),
    'Baker Street': wm('Baker Street Sign.jpg'),
    'Marylebone High Street': wm('The Marylebone pub.JPG'),
    'The Wallace Collection': wm('Wallace Collection across Manchester Square.jpg'),
    'BBC Broadcasting House': wm('BBC Broadcasting House Portland Place.jpg'),
    'All Souls Church, Langham Place': wm('The Church of All Souls, Langham Place (5990857632).jpg'),
    'RIBA (Royal Institute of British Architects)': wm('RIBA, 66 Portland Place, London.jpg'),
    'Great Portland Street shops & cafes': wm('Great Portland Street underground station - geograph.org.uk - 1522059.jpg'),
    'Charlotte Street, Fitzrovia': wm('Charlotte Place, Fitzrovia.jpg'),
    "Regent's Canal towpath": wm("Regent's Canal Towpath by Lisson Grove - geograph.org.uk - 1388145.jpg"),
    'Euston Square & UCL area': wm('Euston Square Gardens - geograph.org.uk - 3152505.jpg'),
    'Wellcome Collection': wm('The Wellcome Building, Euston Road, London.jpg'),
    'London Central Mosque': wm('London central mosque.JPG'),
    'Cumberland Terrace': wm("Cumberland Terrace, Regent's Park - geograph.org.uk - 1297192.jpg"),
    'Oxford Circus & top of Oxford Street': wm('Oxford Circus tube station, London.JPG'),
    'Primrose Hill': wm('Primrose Hill Panorama, London - April 2011.jpg'),
}
for _p in MELIA_20:
    if _p['place'] in MELIA_PHOTOS:
        _p['photo'] = MELIA_PHOTOS[_p['place']]

MELIA_PHONES = {
    "The Regent's Park": '0300 061 2300',
    'London Zoo': '0344 225 1826',
    "Regent's Park Open Air Theatre": '0333 400 3562',
    'Sherlock Holmes Museum': '020 7224 3688',
    'Madame Tussauds London': '0207 487 0350',
    'The Wallace Collection': '020 7563 9500',
    'BBC Broadcasting House': '0370 010 0222',
    'All Souls Church, Langham Place': '020 7580 3522',
    'RIBA (Royal Institute of British Architects)': '+44 (0)20 7307 5355',
    'Wellcome Collection': '020 7611 2222',
    'London Central Mosque': '020 7725 2152',
}
for _p in MELIA_20:
    if _p['place'] in MELIA_PHONES:
        _p['phone'] = MELIA_PHONES[_p['place']]
melia20_html = ''.join(place_card(p, with_review=True) for p in MELIA_20)

def gsearch(q):
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(q)

SHOPS_20 = [
    ('Harrods', 'Flagship luxury department store, iconic since 1834', '87-135 Brompton Rd, Knightsbridge, London SW1X 7XL',
     'https://www.harrods.com', 'Mon-Sat 10am-9pm, Sun 11:30am-6pm', '+44 (0)20 7730 1234'),
    ('Selfridges', 'Legendary Oxford Street department store', '400 Oxford St, London W1A 1AB',
     'https://www.selfridges.com', 'Mon-Fri 10am-10pm, Sat 10am-9pm, Sun 11:30am-6pm', '020 7160 6222'),
    ('Liberty London', "Tudor-revival department store, famous for its prints", 'Great Marlborough St, London W1B 5AH',
     'https://www.libertylondon.com', 'Mon-Sat 10am-8pm, Sun 12pm-6pm', '020 7734 1234'),
    ('Fortnum & Mason', 'Royal grocer since 1707 - hampers, tea, food halls', '181 Piccadilly, London W1A 1ER',
     'https://www.fortnumandmason.com', 'Mon-Sat 10am-8pm, Sun 11:30am-6pm', '020 7734 8040'),
    ('Hamleys', "World's oldest and largest toy shop", '188-196 Regent St, London W1B 5BT',
     'https://www.hamleys.com', 'Mon-Sat 10am-9pm, Sun 12pm-6pm', '0371 704 1977'),
    ('John Lewis Oxford Street', 'Flagship department store', '300 Oxford St, London W1C 1DX',
     'https://www.johnlewis.com', 'Mon-Wed & Fri-Sat 9:30am-8pm, Thu 9:30am-9pm, Sun 12pm-6pm', '0345 608 0677'),
    ('Daunt Books Marylebone', 'Beautiful Edwardian travel bookshop', '83 Marylebone High St, London W1U 4QW',
     'https://www.dauntbooks.co.uk', 'Mon-Sat 9am-7:30pm, Sun 11am-6pm', '020 7224 2295'),
    ('Waterstones Piccadilly', "Europe's largest bookshop", '203-206 Piccadilly, London W1J 9HD',
     'https://www.waterstones.com/bookshops/piccadilly', 'Mon-Sat 9am-10pm, Sun 12pm-6:30pm', '020 7851 2400'),
    ('Burlington Arcade', 'Historic covered luxury shopping arcade', '51 Piccadilly, London W1J 0QJ',
     'https://www.burlingtonarcade.com', 'Mon-Sat 8am-8pm, Sun 11am-6pm', '020 7493 1764'),
    ('Regent Street', 'Iconic curved shopping street, flagship stores', 'Regent St, London W1B',
     'https://www.regentstreetonline.com', 'Varies by store (most 10am-7/8pm, Sun 12pm-6pm)', 'Varies by store'),
    ('Camden Market', 'Alternative fashion, crafts and street food stalls', 'Camden Lock Pl, London NW1 8AF',
     'https://www.camdenmarket.com', 'Daily 10am-6pm (some stalls/evenings vary)', '020 3763 9999'),
    ('Portobello Road Market', 'Antiques, vintage and fashion market', 'Portobello Rd, London W11 1LJ',
     'https://www.visitportobello.com', 'Mon-Sat approx. 8am-7pm (Sat is main trading day)', '020 7727 7684'),
    ('Borough Market', 'Historic food market', '8 Southwark St, London SE1 1TL',
     'https://www.boroughmarket.org.uk', 'Mon-Fri 10am-5pm (limited), Sat 8am-5pm, Sun 10am-3pm', '020 7407 1002'),
    ('Covent Garden Market', 'Boutiques, crafts market, street performers', 'The Piazza, Covent Garden, London WC2E 8RF',
     'https://www.coventgarden.london', 'Mon-Fri 10am-8pm, Sat 9am-8pm, Sun 12pm-6pm', '020 7395 3765'),
    ('New Bond Street', 'Luxury flagship boutiques - Chanel, Tiffany & more', 'New Bond St, London W1S',
     'https://www.newbondstreet.co.uk', 'Varies by store (most 10am-6/7pm, Sun 12pm-6pm)', 'Varies by store'),
    ('Foyles Charing Cross Road', 'Famous independent bookshop', '107 Charing Cross Rd, London WC2H 0DT',
     'https://www.foyles.co.uk', 'Mon-Sat 9:30am-9pm, Sun 11:30am-6pm', '020 7437 5660'),
    ("M&M's World", 'Multi-storey confectionery flagship store', '1 Swiss Ct, London W1D 6AP',
     'https://www.mms.com/en-gb/explore/mms-stores/london', 'Mon-Sat 10am-9pm, Sun 12pm-6pm', '020 7025 7171'),
    ('LEGO Store Leicester Square', 'Flagship LEGO store', '3 Swiss Ct, London W1D 6AP',
     'https://www.lego.com/en-gb/stores/store/lsq', 'Mon-Sat 10am-10pm, Sun 12pm-6pm', '020 7839 3480'),
    ('Apple Store Regent Street', 'Flagship Apple store in a historic building', '235 Regent St, London W1B 2EL',
     'https://www.apple.com/uk/retail/regentstreet', 'Mon-Fri 10am-9pm, Sat 10am-8pm, Sun 10am-6pm', '020 7153 9000'),
    ('Primark Oxford Street', "World's largest Primark store", '14-28 Oxford St, Fitzrovia, London W1D 1AU',
     'https://www.primark.com/en-gb/stores/london/14-28-oxford-street', 'Mon-Sat 8am-10pm, Sun 11:30am-6pm', '020 7580 5510'),
]

SHOP_PHOTOS = {
    'Harrods': wm('Harrods (London).jpg'),
    'Selfridges': wm('Selfridges Oxford Street.jpg'),
    'Liberty London': wm('Liberty department store London.jpg'),
    'Fortnum & Mason': wm('Fortnum and Mason.jpg'),
    'Hamleys': wm("Hamley's (Regent's Street - London).jpg"),
    'John Lewis Oxford Street': wm('Oxford Street - John Lewis.jpg'),
    'Daunt Books Marylebone': wm('Daunt Books Marylebone W1.jpg'),
    'Waterstones Piccadilly': wm('Simpsons of Piccadilly 1.jpg'),
    'Burlington Arcade': wm('Burlington Arcade, shops.jpg'),
    'Regent Street': wm('London - Regent Street - View East.jpg'),
    'Camden Market': wm('Camden markets entrance.JPG'),
    'Portobello Road Market': wm('Portobello market.JPG'),
    'Borough Market': wm('Borough Market - Southwark Street London SE1 1TL.jpg'),
    'Covent Garden Market': wm('East Piazza, Covent Garden.jpg'),
    'New Bond Street': wm('New Bond Street, Mayfair - geograph.org.uk - 966302.jpg'),
    'Foyles Charing Cross Road': wm('Foyles Bookstore.jpg'),
    "M&M's World": wm("M&M's World London.JPG"),
    'LEGO Store Leicester Square': wm('Lego Store Leicester Square London Lester.jpg'),
    'Apple Store Regent Street': wm('Apple Store, 235 Regent Street - geograph.org.uk - 2346324.jpg'),
    'Primark Oxford Street': wm('Primark in Oxford Street - geograph.org.uk - 1053122.jpg'),
}
shops20_html = ''.join(
    place_card({'place': p, 'type': t, 'address': a, 'gmap': gsearch(a), 'website': w, 'hours': h, 'phone': ph,
                'photo': SHOP_PHOTOS.get(p)})
    for p, t, a, w, h, ph in SHOPS_20
)

PICC_SHOPS_20 = [
    ('Fortnum & Mason', 'Royal grocer since 1707 - hampers, tea, food halls (~2 min walk)', '181 Piccadilly, London W1A 1ER',
     'https://www.fortnumandmason.com', 'Mon-Sat 10am-8pm, Sun 11:30am-6pm', '020 7734 8040'),
    ('Hatchards', "UK's oldest bookshop (est. 1797), five floors, right next to Fortnum's (~2 min walk)", '187 Piccadilly, London W1J 9LE',
     'https://www.hatchards.co.uk', 'Mon-Sat 9:30am-8pm, Sun 10:30am-6pm', None),
    ('Waterstones Piccadilly', "Europe's largest bookshop (~3 min walk)", '203-206 Piccadilly, London W1J 9HD',
     'https://www.waterstones.com/bookshops/piccadilly', 'Mon-Sat 9am-10pm, Sun 12pm-6:30pm', '020 7851 2400'),
    ('Burlington Arcade', 'Historic 1819 covered luxury shopping arcade with uniformed Beadles (~4 min walk)', '51 Piccadilly, London W1J 0QJ',
     'https://www.burlingtonarcade.com', 'Mon-Sat 8am-8pm, Sun 11am-6pm', '020 7493 1764'),
    ("Penhaligon's", 'British perfumer established 1870, inside Burlington Arcade (~4 min walk)', '16-17 Burlington Arcade, London W1J 0PL',
     'https://www.penhaligons.com', 'Check ahead - hours vary', '020 7629 1416'),
    ("Prince's Arcade", 'Victorian shopping arcade linking Piccadilly to Jermyn Street (~4 min walk)', "8-10 Prince's Arcade, Piccadilly, London SW1Y 6DS",
     None, 'Varies by store', None),
    ('Lillywhites', 'Flagship five-floor sports store, oldest in the UK (est. 1863), right on Piccadilly Circus (~1 min walk)', '24-36 Regent St, London SW1Y 4QF',
     'https://www.lillywhites.com', 'Mon-Sat 9:30am-10pm, Sun 12pm-6pm', '0844 332 5602'),
    ('Hamleys', "World's oldest and largest toy shop (~7 min walk)", '188-196 Regent St, London W1B 5BT',
     'https://www.hamleys.com', 'Mon-Sat 10am-9pm, Sun 12pm-6pm', '0371 704 1977'),
    ('Apple Store Regent Street', 'Flagship Apple store in a historic building (~9 min walk)', '235 Regent St, London W1B 2EL',
     'https://www.apple.com/uk/retail/regentstreet', 'Mon-Fri 10am-9pm, Sat 10am-8pm, Sun 10am-6pm', '020 7153 9000'),
    ('Liberty London', "Tudor-revival department store, famous for its prints (~8 min walk)", 'Great Marlborough St, London W1B 5AH',
     'https://www.libertylondon.com', 'Mon-Sat 10am-8pm, Sun 12pm-6pm', '020 7734 1234'),
    ('Regent Street', 'Iconic curved shopping street, flagship stores end to end (~1-9 min walk)', 'Regent St, London W1B',
     'https://www.regentstreetonline.com', 'Varies by store (most 10am-7/8pm, Sun 12pm-6pm)', None),
    ('Carnaby Street', "Swinging-60s fashion street, now independent boutiques and big brands (~8 min walk)", 'Carnaby St, London W1F',
     'https://www.carnaby.co.uk', 'Varies by store (most 10am-7pm, Sun 12-6pm)', None),
    ('Jermyn Street', "London's shirtmaking street - Turnbull & Asser and other historic tailors (~5 min walk)", '71-72 Jermyn St, London SW1Y 6PF',
     'https://turnbullandasser.com/pages/jermyn', 'Mon-Fri 9am-6pm, Sat 9:30am-6pm (closed Sun)', '020 7808 3000'),
    ('Savile Row', "The world-famous bespoke tailoring street (~10 min walk)", '32 Old Burlington St / 17 Clifford St, London W1S',
     'https://www.anderson-sheppard.co.uk', 'Mon-Fri 8:30am-5pm (haberdashery also open Sat 10:30am-4pm)', None),
    ('M&M\'s World', 'Multi-storey confectionery flagship store, Leicester Square (~6 min walk)', '1 Swiss Ct, London W1D 6AP',
     'https://www.mms.com/en-gb/explore/mms-stores/london', 'Mon-Sat 10am-9pm, Sun 12pm-6pm', '020 7025 7171'),
    ('LEGO Store Leicester Square', 'Flagship LEGO store (~6 min walk)', '3 Swiss Ct, London W1D 6AP',
     'https://www.lego.com/en-gb/stores/store/lsq', 'Mon-Sat 10am-10pm, Sun 12pm-6pm', '020 7839 3480'),
    ('Foyles Charing Cross Road', 'Famous independent bookshop, five floors (~9 min walk)', '107 Charing Cross Rd, London WC2H 0DT',
     'https://www.foyles.co.uk', 'Mon-Sat 9:30am-9pm, Sun 11:30am-6pm', '020 7437 5660'),
    ('Covent Garden Market', 'Boutiques, craft market, street performers (~10 min walk)', 'The Piazza, Covent Garden, London WC2E 8RF',
     'https://www.coventgarden.london', 'Mon-Fri 10am-8pm, Sat 9am-8pm, Sun 12pm-6pm', '020 7395 3765'),
    ('New Bond Street', 'Luxury flagship boutiques - Chanel, Tiffany & more (~10 min walk)', 'New Bond St, London W1S',
     'https://www.newbondstreet.co.uk', 'Varies by store (most 10am-6/7pm, Sun 12pm-6pm)', None),
    ('St James\'s Market', 'Small modern food-and-shopping precinct behind Waterstones (~4 min walk)', "St James's Market, London SW1Y 4AH",
     None, 'Varies by outlet', None),
]
PICC_SHOP_PHOTOS = {
    'Fortnum & Mason': SHOP_PHOTOS.get('Fortnum & Mason'),
    'Waterstones Piccadilly': SHOP_PHOTOS.get('Waterstones Piccadilly'),
    'Burlington Arcade': SHOP_PHOTOS.get('Burlington Arcade'),
    'Hamleys': SHOP_PHOTOS.get('Hamleys'),
    'Apple Store Regent Street': SHOP_PHOTOS.get('Apple Store Regent Street'),
    'Liberty London': SHOP_PHOTOS.get('Liberty London'),
    'Regent Street': SHOP_PHOTOS.get('Regent Street'),
    "M&M's World": SHOP_PHOTOS.get("M&M's World"),
    'LEGO Store Leicester Square': SHOP_PHOTOS.get('LEGO Store Leicester Square'),
    'Foyles Charing Cross Road': SHOP_PHOTOS.get('Foyles Charing Cross Road'),
    'Covent Garden Market': SHOP_PHOTOS.get('Covent Garden Market'),
    'New Bond Street': SHOP_PHOTOS.get('New Bond Street'),
}
piccshops20_html = ''.join(
    place_card({'place': p, 'type': t, 'address': a, 'gmap': gsearch(a), 'website': w, 'hours': h, 'phone': ph,
                'photo': PICC_SHOP_PHOTOS.get(p)})
    for p, t, a, w, h, ph in PICC_SHOPS_20
)

PICC_THINGS_20 = [
    {'place': 'Piccadilly Circus & the Shaftesbury Memorial (Eros)', 'type': "The famous statue and video-screen hub itself - starting point for everything below",
     'address': 'Piccadilly Circus, London W1J', 'gmap': gsearch('Piccadilly Circus, London'), 'w3w': 'tidy.loyal.public'},
    {'place': "St James's Church Piccadilly", 'type': "Wren-designed church (1684) with a leafy courtyard and craft/antiques market most days",
     'address': '197 Piccadilly, London W1J 9LL', 'website': 'https://www.sjp.org.uk/', 'gmap': gsearch("St James's Church Piccadilly, London")},
    {'place': 'Royal Academy of Arts', 'type': 'Major art exhibitions inside historic Burlington House - free courtyard and permanent collection displays',
     'address': 'Burlington House, Piccadilly, London W1J 0BD', 'website': 'https://www.royalacademy.org.uk/',
     'hours': 'Tue-Thu & Sun 10am-6pm, Fri-Sat 10am-9pm (closed Mon)', 'phone': '020 7300 8090',
     'gmap': gsearch('Royal Academy of Arts, Piccadilly, London')},
    {'place': 'Leicester Square', 'type': 'Cinemas, half-price theatre ticket booth (TKTS) and street entertainers',
     'address': 'Leicester Square, London WC2H 7NA', 'gmap': gsearch('Leicester Square, London')},
    {'place': 'Chinatown London', 'type': 'Pagoda gates, dim sum and Chinese bakeries around Gerrard Street',
     'address': 'Gerrard St, London W1D 5PW', 'gmap': gsearch('Chinatown London Gerrard Street')},
    {'place': 'Soho Square', 'type': 'Small leafy square in the heart of Soho, good for a sit-down break',
     'address': 'Soho Square, London W1D 3QP', 'gmap': gsearch('Soho Square, London')},
    {'place': 'Trafalgar Square', 'type': "Nelson's Column, the four bronze lions and the famous fourth plinth artwork",
     'address': 'Trafalgar Square, London WC2N 5DN', 'gmap': gsearch('Trafalgar Square, London')},
    {'place': 'National Gallery', 'type': 'World-class collection of Western European paintings - free entry to the permanent collection',
     'address': 'Trafalgar Square, London WC2N 5DN', 'website': 'https://www.nationalgallery.org.uk/',
     'hours': 'Daily 10am-6pm, Fri until 9pm', 'gmap': gsearch('National Gallery, Trafalgar Square, London')},
    {'place': 'National Portrait Gallery', 'type': 'Portraits of famous Britons through history - free entry to the permanent collection',
     'address': "St Martin's Place, London WC2H 0HE", 'website': 'https://www.npg.org.uk/',
     'hours': 'Daily 10:30am-6pm, Fri-Sat until 9pm', 'gmap': gsearch('National Portrait Gallery, London')},
    {'place': "St James's Park", 'type': "One of London's prettiest royal parks - lake, pelicans, views to Buckingham Palace",
     'address': "St James's Park, London SW1A 2BJ", 'gmap': gsearch("St James's Park, London")},
    {'place': 'Green Park', 'type': 'Quiet, tree-lined royal park between Piccadilly and Buckingham Palace',
     'address': 'Green Park, London SW1A 1BW', 'gmap': gsearch('Green Park, London')},
    {'place': 'The Ritz London', 'type': 'Legendary 1906 hotel - iconic Louis XVI-style facade, famous afternoon tea (book well ahead)',
     'address': '150 Piccadilly, London W1J 9BR', 'website': 'https://www.theritzlondon.com/', 'gmap': gsearch('The Ritz London, Piccadilly')},
    {'place': 'Spencer House', 'type': "Princess Diana's ancestral family home - 18th-century state rooms, open select days",
     'address': "27 St James's Place, London SW1A 1NR", 'website': 'https://www.spencerhouse.co.uk/', 'gmap': gsearch("Spencer House, St James's Place, London")},
    {'place': "Christie's", 'type': 'World-famous auction house - free public viewing rooms before major sales',
     'address': "8 King St, St James's, London SW1Y 6QT", 'website': 'https://www.christies.com/', 'gmap': gsearch("Christie's King Street, London")},
    {'place': 'Handel & Hendrix House', 'type': "Composer Handel's Georgian home next door to where Jimi Hendrix once lived - small museum",
     'address': '25 Brook St, London W1K 4HB', 'website': 'https://handelhendrix.org/',
     'hours': 'Wed-Sun 10am-5pm (closed Mon-Tue)', 'phone': '020 7495 1685', 'gmap': gsearch('Handel Hendrix House, Brook Street, London')},
    {'place': "The Photographers' Gallery", 'type': "London's leading photography gallery - free exhibitions on the ground floor",
     'address': '16-18 Ramillies St, London W1F 7LW', 'website': 'https://thephotographersgallery.org.uk/',
     'hours': 'Mon-Wed & Sat 10:30am-6pm, Thu-Fri 10:30am-8pm, Sun 11am-6pm', 'gmap': gsearch("The Photographers' Gallery, Ramillies Street, London")},
    {'place': 'Covent Garden Piazza', 'type': 'Street performers, market stalls and the Royal Opera House',
     'address': 'The Piazza, Covent Garden, London WC2E 8RF', 'gmap': gsearch('Covent Garden Piazza, London')},
    {'place': 'Shaftesbury Avenue Theatreland', 'type': "London's main theatre strip - Lyric, Apollo, Gielgud, Queen's and more, all in a row",
     'address': 'Shaftesbury Ave, London W1D', 'gmap': gsearch('Shaftesbury Avenue, London')},
    {'place': 'Waterloo Place & Duke of York Column', 'type': 'Grand statue-lined avenue with steps down toward The Mall and St James\'s Park',
     'address': 'Waterloo Place, London SW1Y 5AY', 'gmap': gsearch('Waterloo Place, London')},
    {'place': 'Berkeley Square', 'type': "Mayfair's grand garden square, lined with plane trees - of 'nightingale sang' fame",
     'address': 'Berkeley Square, London W1J 6BR', 'gmap': gsearch('Berkeley Square, London')},
]
piccthings20_html = ''.join(place_card(p) for p in PICC_THINGS_20)

CARS_BABY_CARS = [
    {'place': 'Rolls-Royce Motor Cars London', 'type': 'Flagship Rolls-Royce showroom on the corner of Berkeley Street and Stratton Street (~10 min walk)',
     'address': '50 Berkeley St, London W1J 8HD', 'website': 'https://www.rolls-roycemotorcars.com/london/',
     'gmap': gsearch('Rolls-Royce Motor Cars London, 50 Berkeley Street')},
    {'place': 'Jack Barclay Bentley', 'type': "London's oldest Bentley dealership (since 1927), on Berkeley Square (~10 min walk)",
     'address': '18 Berkeley Square, London W1J 6AE', 'website': 'https://www.jackbarclay.bentleymotors.com/',
     'gmap': gsearch('Jack Barclay Bentley, 18 Berkeley Square, London')},
    {'place': 'H.R. Owen Ferrari Mayfair', 'type': 'Official Ferrari flagship showroom, Berkeley Square (~10 min walk)',
     'address': '15-17 Berkeley Square, London W1J 6EG', 'website': 'https://london-hrowen.ferraridealers.com/',
     'gmap': gsearch('H.R. Owen Ferrari Mayfair, Berkeley Square, London')},
    {'place': 'Lamborghini Mayfair', 'type': 'H.R. Owen flagship Lamborghini showroom, Berkeley Square (~10 min walk)',
     'address': '20 Berkeley Square, London W1J 6BR', 'website': 'https://www.hrowen.co.uk/lamborghini/location/lamborghini-mayfair/',
     'gmap': gsearch('Lamborghini Mayfair, 20 Berkeley Square, London')},
    {'place': 'Volvo Cars Central London', 'type': 'Official Volvo showroom and service centre, Swiss Cottage (a drive/tube ride, not walkable)',
     'address': '1 Northways Parade, Finchley Rd, London NW3 5EN', 'website': 'https://www.volvocars.com/uk/dealers/car-retailers/volvo-cars-swiss-cottage-london/',
     'gmap': gsearch('Volvo Cars Central London, Northways Parade, Finchley Road, London')},
    {'place': 'Mercedes-Benz of Chelsea', 'type': 'Official Mercedes-Benz showroom on Wandsworth Bridge (a drive/tube ride, not walkable)',
     'address': 'Jews Row, Wandsworth, London SW18 1TB', 'website': 'https://www.mercedes-benz.co.uk/passengercars/mercedes-benz-cars/dealer-locator.html',
     'gmap': gsearch('Mercedes-Benz of Chelsea, Jews Row, Wandsworth, London')},
]
carsbaby_html = ''.join(place_card(p) for p in CARS_BABY_CARS)
carsbaby_note = ("Rolls-Royce, Bentley, Ferrari and Lamborghini are all genuinely walkable from Piccadilly Circus around Berkeley Square, Mayfair. "
                 "Volvo and Mercedes-Benz are London dealerships but sit further out (Swiss Cottage and Wandsworth) - worth a taxi/tube rather than a walk. "
                 "Zeekr doesn't have a UK showroom yet - its London launch is expected later in 2026.")

MILAN_DINNER_OPTIONS = [
    {'place': 'Cantine Milano', 'type': 'Open Wed: 12:00–3:00pm & 6:00pm–12:30am', 'address': 'Via Trau 1, 20159 Milano',
     'website': 'https://cantinemilano.com/', 'menu': 'https://cantinemilano.com/menu/',
     'gmap': 'https://www.google.com/maps/search/?api=1&query=Cantine+Milano+Via+Trau+1+Milano',
     'instagram': 'https://www.instagram.com/cantinemilano/',
     'photo': 'https://cantinemilano.com/wp-content/uploads/2023/05/wine-restaurant.jpg'},
    {'place': "L'Immagine Ristorante Bistrot", 'type': 'Open Wed: 6:00–10:30pm (dinner only)', 'address': 'Via Varesina 61, 20156 Milano',
     'website': 'https://www.limmaginebistrot.com/', 'menu': 'https://www.limmaginebistrot.com/s/menu-465.html',
     'gmap': 'https://www.google.com/maps/search/?api=1&query=L%27immagine+Bistrot+Via+Varesina+61+Milano',
     'instagram': 'https://www.instagram.com/limmaginebistrot/',
     'photo': 'https://media-cdn.tripadvisor.com/media/photo-f/1b/2d/36/13/interno-sala-bistrot.jpg'},
    {'place': 'Casa Festa - Pizzeria Alcolica', 'type': 'Open Wed: 11:30am–3:00pm & 6:30–11:30pm', 'address': 'Viale Bligny 42, 20136 Milano',
     'website': 'https://www.pizzeriacasafesta.it/', 'menu': 'https://www.quandoo.it/en/place/johnny-take-ue-93037/menu',
     'gmap': 'https://www.google.com/maps/search/?api=1&query=Casa+Festa+Pizzeria+Alcolica+Viale+Bligny+42+Milano',
     'instagram': 'https://www.instagram.com/casafesta_pizzeriaalcolica/',
     'photo': 'https://media-cdn.tripadvisor.com/media/photo-s/1c/15/d3/e2/johnny-take-ue-bligny.jpg'},
    {'place': 'Osteria Cornalia', 'type': 'TripAdvisor 4.6★ (362 reviews) · Open Wed: 12:00–3:00pm & 7:00pm–12:00am', 'address': 'Via Emilio Cornalia 16, 20124 Milano',
     'website': 'https://www.osteriacornalia.it/', 'menu': 'https://www.osteriacornalia.it/menu-cena-osteria-cornalia/',
     'gmap': 'https://www.google.com/maps/search/?api=1&query=Osteria+Cornalia+Via+Emilio+Cornalia+16+Milano',
     'instagram': 'https://www.instagram.com/osteriacornalia/',
     'photo': 'https://www.osteriacornalia.it/wp-content/uploads/2024/02/IMG_2521-scaled.jpg'},
    {'place': 'Da Gigi Ristorante & Pizzeria', 'type': 'TheFork 8.9/10 · Open Wed: 12:00pm–11:00pm (non-stop)', 'address': 'Via Mauro Macchi 2, 20124 Milano',
     'website': 'https://www.dagigiristorante.it/', 'menu': 'https://www.thefork.it/ristorante/da-gigi-ristorante-r742987/menu',
     'gmap': 'https://www.google.com/maps/search/?api=1&query=Da+Gigi+Ristorante+Via+Mauro+Macchi+2+Milano',
     'instagram': 'https://www.instagram.com/dagigi_ristorante/',
     'photo': 'https://www.dagigiristorante.it/wp-content/uploads/2026/01/DA-GIGI-1727-scaled-e1768401050721.jpg'},
    {'place': 'Osteria Nanin - Torriani', 'type': 'TripAdvisor 4.0★ (97 reviews) · Open Wed: 12:00–3:00pm & 7:00–10:45pm', 'address': 'Via Napo Torriani 10, 20124 Milano',
     'website': 'https://nanin.it/', 'menu': 'https://nanin.it/wp-content/uploads/Menu-Osteria-Nanin-Napo-Torriani-Gennaio-2024.pdf',
     'gmap': 'https://www.google.com/maps/search/?api=1&query=Osteria+Nanin+Torriani+Via+Napo+Torriani+10+Milano',
     'instagram': 'https://www.instagram.com/osteria_nanin/',
     'photo': 'https://nanin.it/wp-content/uploads/Header_Osteria_V2.jpeg'},
    {'place': 'Giannino dal 1899', 'type': 'TripAdvisor 4.3★ (303 reviews) · Open Wed: 12:00–3:00pm & 7:00–11:30pm', 'address': 'Via Vittor Pisani 6, 20124 Milano',
     'website': 'https://gianninoristorante.it/', 'menu': 'https://gianninoristorante.it/en/the-menu/',
     'gmap': 'https://www.google.com/maps/search/?api=1&query=Giannino+dal+1899+Via+Vittor+Pisani+6+Milano',
     'instagram': 'https://www.instagram.com/gianninodal1899/',
     'photo': 'https://gianninoristorante.it/wp-content/uploads/2022/02/home1.jpg'},
    {'place': 'Pizza Shambò', 'type': 'TripAdvisor 4.6★ (229 reviews) · Open Wed: 12:00–3:00pm & 6:00–11:00pm', 'address': 'Via Edolo 1, 20125 Milano',
     'website': 'https://www.thefork.it/ristorante/shambo-r465529', 'menu': 'https://www.thefork.it/ristorante/shambo-r465529/menu',
     'gmap': 'https://www.google.com/maps/search/?api=1&query=Pizza+Shambo+Via+Edolo+1+Milano',
     'instagram': 'https://www.instagram.com/pizzashambo/',
     'photo': 'https://www.pizzashambo.com/wp-content/uploads/2025/02/DSC09015-683x1024.jpg'},
]
milan_dinner_html = ''.join(place_card(p) for p in MILAN_DINNER_OPTIONS)

MILAN_DINNER_DISTANCE = [
    ('Cantine Milano', '~1.8 km', '~20 min walk / ~7 min taxi', 'Walk via Via Sammartini, or short taxi'),
    ("L'Immagine Ristorante Bistrot", '~4.5 km', '~15 min taxi / ~25 min metro + walk', 'Taxi, or M5 to Portello then ~10 min walk'),
    ('Casa Festa - Pizzeria Alcolica', '~4.8 km', '~18 min taxi / ~25 min metro', 'Taxi, or M3 toward Porta Romana/Lodi then ~8 min walk'),
    ('Osteria Cornalia', '~0.6 km', '~8 min walk', 'Walk via Via Napo Torriani/Via Sammartini'),
    ('Da Gigi Ristorante & Pizzeria', '~0.5 km', '~7 min walk', 'Walk via Via Vittor Pisani/Via Mauro Macchi'),
    ('Osteria Nanin - Torriani', '~0.45 km', '~6 min walk', 'Walk via Via Napo Torriani'),
    ('Giannino dal 1899', '~0.9 km', '~12 min walk', 'Walk via Via Vittor Pisani towards Piazza della Repubblica'),
    ('Pizza Shambò', '~2.0 km', '~25 min walk / ~10 min taxi', 'Taxi, or bus/tram towards Via Porpora'),
]
milan_dinner_distance_html = ''.join(
    f'<tr><td>{esc(dest)}</td><td>{esc(dist)}</td><td>{esc(time_)}</td><td class="ttc-notes">{esc(method)}</td></tr>'
    for dest, dist, time_, method in MILAN_DINNER_DISTANCE
)

def milan_dinner_stack():
    dist_map = {name: (dist, time_, method) for name, dist, time_, method in MILAN_DINNER_DISTANCE}
    rows = []
    for p in MILAN_DINNER_OPTIONS:
        dist, time_, method = dist_map.get(p['place'], ('', '', ''))
        links = ''
        if p.get('website'):
            links += f'<a class="pill pill-website" href="{esc(p["website"])}" target="_blank">Website</a>'
        if p.get('menu'):
            links += f'<a class="pill pill-weblink" href="{esc(p["menu"])}" target="_blank">Menu</a>'
        if p.get('gmap'):
            links += f'<a class="pill" href="{esc(p["gmap"])}" target="_blank">Map</a>'
        if p.get('instagram'):
            links += f'<a class="pill pill-instagram" href="{esc(p["instagram"])}" target="_blank" title="Instagram link">I</a>'
        photo_html = ''
        if p.get('photo'):
            photo_html = (
                f'<img class="resto-photo" src="{esc(p["photo"])}" alt="{esc(p["place"])}" '
                f'loading="lazy" referrerpolicy="no-referrer" '
                f'onerror="this.style.display=\'none\'">'
            )
        rows.append(f'''
        <div class="resto-item">
          <div class="resto-info">
            <div class="resto-name">{esc(p['place'])}</div>
            <div class="resto-hours">{esc(p.get('type') or '')}</div>
            <div class="resto-addr">{esc(p.get('address') or '')}</div>
            <div class="resto-dist"><span class="resto-dist-ic">&#128663;</span>{esc(dist)} from iQ Hotel Milano &middot; {esc(time_)} &middot; {esc(method)}</div>
            <div class="resto-links">{links}</div>
          </div>
          {photo_html}
        </div>''')
    return ''.join(rows)

milan_dinner_stack_html = milan_dinner_stack()

italy_options = sched.get('italy_options', [])
_options_prev_stay = tuscany_days[-1].get('stay') if tuscany_days else None
italy_options_html = ''.join(
    day_card(d, 'milan2', day_id=day_id_for(d['title']),
             day_map=day_map_for(d['title'], d, 'milan2', prev_stay=_options_prev_stay))
    for d in italy_options
)

london_places_html = ''.join(place_card(p, with_review=True) for p in places['london_places'])
rome_places_html = ''.join(place_card(p, with_review=True) for p in places['rome_places'])
tuscany_places_html = ''.join(place_card(p, with_review=True) for p in places['tuscany_places'])
italy_places_html = ''.join(place_card(p, with_review=True) for p in places['italy_places'])
milan_places_html = ''.join(place_card(p, with_review=True) for p in places.get('milan_places', []))

london_ttc_html = ''.join(ttc_row(t) for t in places['london_ttc'])
italy_ttc_html = ''.join(ttc_row(t) for t in places['italy_ttc'])
ntb_html = ''.join(ntb_row(n) for n in places['need_to_book'])
tt_html = ''.join(tt_row(t, i) for i, t in enumerate(places.get('things_to_take', [])))

ETA_PEOPLE = ['Karen Nicholson', 'Deb Gyde', 'Thomas Akhurst', 'Gary Nicholson']
def eta_row(name, idx):
    eta_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    first_name = name.split(' ')[0]
    return f'''
    <tr>
      <td>{esc(name)}</td>
      <td class="tt-tick"><input type="checkbox" class="eta-check" id="eta-{idx}-{eta_id}" data-eta-id="{eta_id}" data-first-name="{esc(first_name)}"></td>
    </tr>'''
eta_html = ''.join(eta_row(n, i) for i, n in enumerate(ETA_PEOPLE))

PASSPORT_PEOPLE = ['Karen Nicholson', 'Deb Gyde', 'Thomas Akhurst', 'Gary Nicholson']
def passport_row(name, idx):
    pp_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    first_name = name.split(' ')[0]
    return f'''
    <tr>
      <td>{esc(name)}</td>
      <td class="tt-tick"><input type="checkbox" class="passport-check" id="passport-{idx}-{pp_id}" data-passport-id="{pp_id}" data-first-name="{esc(first_name)}"></td>
    </tr>'''
passport_html = ''.join(passport_row(n, i) for i, n in enumerate(PASSPORT_PEOPLE))

IDP_PEOPLE = [
    ('Karen Nicholson', False, ''),
    ('Deb Gyde', False, ''),
    ('Thomas Akhurst', False, ''),
    ('Gary Nicholson', True, 'IDP196978'),
]
def idp_row(name, has_idp, number, idx):
    idp_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    first_name = name.split(' ')[0]
    checked = ' checked' if has_idp else ''
    number_html = esc(number) if number else '&nbsp;'
    return f'''
    <tr>
      <td>{esc(name)}</td>
      <td class="tt-tick"><input type="checkbox" class="idp-check" id="idp-{idx}-{idp_id}" data-idp-id="{idp_id}" data-first-name="{esc(first_name)}"{checked}></td>
      <td>{number_html}</td>
    </tr>'''
idp_html = ''.join(idp_row(n, has_idp, num, i) for i, (n, has_idp, num) in enumerate(IDP_PEOPLE))

DRIVE_TIMES = [
    ('Civitavecchia (car collection) &rarr; Agriturismo Buratta, Talamone', '~140 km', '~2h 00m', 'Coastal route via SS1 Aurelia'),
    ('Agriturismo Buratta, Talamone &rarr; Hotel Borgo di Cortefreda Relais', '~140 km', '~2h 00m', 'Via SS223 (Siena&ndash;Grosseto), then north toward Tavarnelle'),
    ('Total driving, via Talamone lunch stop', '~280 km', '~4h 00m driving (excl. lunch)', 'Direct route without the detour is approx. 230 km / 3h 10m'),
]
drive_times_html = ''.join(
    f'<tr><td>{leg}</td><td>{dist}</td><td>{time_}</td><td class="ttc-notes">{note}</td></tr>'
    for leg, dist, time_, note in DRIVE_TIMES
)

def theme_for_where(where):
    w = (where or '').lower()
    if 'rome' in w or 'arrival in rome' in w: return 'rome'
    if 'queen victoria' in w or 'sea day' in w or 'marseille' in w or 'villefranche' in w or 'genoa' in w or 'spezia' in w: return 'cruise'
    if 'tuscany' in w: return 'tuscany'
    if 'milan' in w: return 'milan'
    if 'london' in w: return 'london'
    return 'air'

def flag_for_where(where):
    w = (where or '').lower()
    if 'sea day' in w: return ('&#127466;&#127482;', 'EU / at sea')
    if 'air travel' in w or w == 'air travel': return ('&#9992;&#65039;', 'Flying')
    if 'marseille' in w or 'villefranche' in w: return ('&#127467;&#127479;', 'France')
    if 'rome' in w or 'tuscany' in w or 'milan' in w or 'genoa' in w or 'spezia' in w: return ('&#127470;&#127481;', 'Italy')
    if 'london' in w: return ('&#127468;&#127463;', 'UK')
    if 'home' in w: return ('&#9992;&#65039;', 'Flying home')
    return ('', '')

# Dates (ISO) that still have an outstanding item in the Things To Do "need to book" list -
# these drive the UNCONFIRMED tag on the Trip at a Glance timeline. Kept in sync manually
# against site_data_places.json's need_to_book array.
UNCONFIRMED_DATES = {'2026-09-14', '2026-09-26'}

timeline_html = ''
for t in travel_json:
    if not (t.get('where') or t.get('what') or t.get('accom')):
        continue
    theme = theme_for_where(t.get('where'))
    d = datetime.date.fromisoformat(t['date'])
    date_disp = d.strftime('%a %d %b')
    day_num = trip_day_number(d)
    where = t.get('where') or t.get('accom') or ''
    what = t.get('what') or ''
    notes = t.get('notes') or ''
    flag_emoji, flag_title = flag_for_where(where)
    flag_html = f'<div class="tl-flag" title="{esc(flag_title)}">{flag_emoji}</div>' if flag_emoji else '<div class="tl-flag"></div>'
    day_num_html = f'<div class="tl-daynum">(Day {day_num})</div>' if 1 <= day_num <= 20 else ''
    if t['date'] in UNCONFIRMED_DATES:
        status_html = '<span class="tl-status tl-status-unconfirmed">UNCONFIRMED</span>'
    elif what:
        status_html = '<span class="tl-status tl-status-confirmed">CONFIRMED</span>'
    else:
        status_html = ''
    dst_html = '<div class="tl-dst">NZ Daylight Saving starts here</div>' if t['date'] == '2026-09-27' else ''
    timeline_html += f'''
    <div class="tl-row {theme}">
      <div class="tl-date">{esc(date_disp)}{day_num_html}</div>
      <div>
        <div class="tl-where">{esc(where)} {status_html}</div>
        <div class="tl-what">{esc(what)}</div>
        {f'<div class="tl-notes">{esc(notes)}</div>' if notes else ''}
        {dst_html}
      </div>
      {flag_html}
    </div>'''

ALL_DAY_IDS = sorted(set(
    did for did in (
        day_id_for(d['title'])
        for d in rome_days + cruise_days + tuscany_days + milan_days + london_days + italy_options
    ) if did
))

SUB_IDS = ['melia20', 'shops20', 'piccshops20', 'piccthings20', 'carsbaby', 'quizquestions', 'quizanswers']

CSS = '''
:root {
  --navy: #1f3864; --gold: #c99a3e;
  --rome: #7f1d1d; --rome-light: #fdecec;
  --cruise: #0e6f76; --cruise-light: #e6f6f7;
  --tuscany: #2e6b3e; --tuscany-light: #eaf5ec;
  --london: #2e4d9e; --london-light: #eaeffc;
  --milan: #6a3fa0; --milan-light: #f2eafb;
  --photo-frame: #3f7cbf;
  --ink: #262626; --muted: #666;
  --card-bg: #ffffff; --page-bg: #f6f5f1;
}
* { box-sizing: border-box; }
body { margin:0; font-family:'Segoe UI','Source Sans Pro',system-ui,sans-serif; color:var(--ink); background:var(--page-bg); line-height:1.5; }
a { color: inherit; }
.hero { background: linear-gradient(135deg, rgba(11,31,58,.86) 0%, rgba(196,90,60,.78) 45%, rgba(91,155,213,.72) 100%), url('data:image/svg+xml;base64,__EUROPE_MAP_B64__') center/cover no-repeat, var(--navy); color:#fff; padding:56px 24px; }
.hero-flags { font-size:1.9rem; letter-spacing:10px; margin:6px 0 4px; }
.hero-inner { max-width:1080px; margin:0 auto; display:flex; align-items:center; justify-content:center; gap:48px; flex-wrap:wrap; text-align:center; }
.hero-text { flex:1 1 380px; text-align:center; }
.hero-photo { flex:0 0 auto; display:flex; flex-direction:column; align-items:center; }
.view-counter { display:inline-flex; align-items:center; gap:6px; margin-bottom:10px; padding:5px 14px; border-radius:20px; background:rgba(255,255,255,.12); color:#fff; font-size:.8rem; font-weight:600; border:1px solid rgba(255,255,255,.3); }
.view-counter .ic { font-size:.9rem; }
.hero-photo img { width:220px; height:220px; object-fit:cover; border-radius:50%; border:5px solid rgba(255,255,255,.85); box-shadow:0 8px 30px rgba(0,0,0,.35); }
.hero-clock { margin-top:12px; font-size:.85rem; color:#fff; opacity:.9; text-align:center; }
.hero-next-trip { margin-top:6px; font-size:.8rem; font-weight:700; letter-spacing:.04em; color:var(--gold); text-align:center; }
@media print { .hero-next-trip { display:none !important; } }
.hero-countdown-wrap { margin-top:16px; text-align:center; }
.hero-countdown-label { font-size:.75rem; letter-spacing:.09em; text-transform:uppercase; color:var(--gold); margin-bottom:10px; font-weight:700; }
.polarsteps-link { display:inline-flex; align-items:center; gap:6px; margin-top:14px; padding:7px 16px; border-radius:20px; background:rgba(255,255,255,.12); color:#fff; text-decoration:none; font-size:.82rem; font-weight:600; border:1px solid rgba(255,255,255,.3); transition:background .2s; }
.polarsteps-link:hover { background:rgba(255,255,255,.22); }
.polarsteps-link .ic { font-size:1rem; }
.flip-clock { display:flex; justify-content:center; align-items:flex-start; gap:12px; flex-wrap:wrap; }
.flip-unit { display:flex; flex-direction:column; align-items:center; }
.flip-card { position:relative; width:64px; height:76px; background:#132038; border:2px solid var(--gold); border-radius:10px; box-shadow:0 4px 14px rgba(0,0,0,.45), inset 0 0 0 1px rgba(255,255,255,.05); overflow:hidden; perspective:200px; }
.flip-card::after { content:''; position:absolute; top:50%; left:0; right:0; height:2px; background:rgba(0,0,0,.55); transform:translateY(-1px); z-index:2; }
.flip-digit { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:2.2rem; font-weight:800; color:#fff; font-variant-numeric:tabular-nums; transform-origin:center top; transition:transform .35s cubic-bezier(.4,0,.2,1), opacity .35s ease; }
.flip-digit.flip-drop { transform:rotateX(-90deg) translateY(6px); opacity:.25; }
.flip-label { margin-top:8px; font-size:.68rem; letter-spacing:.07em; text-transform:uppercase; color:#fff; opacity:.9; font-weight:600; }
@media (max-width:480px) { .flip-card { width:48px; height:58px; } .flip-digit { font-size:1.5rem; } .flip-clock { gap:8px; } }
.hero h1 { font-size:2.6rem; margin:0 0 8px; letter-spacing:.5px; text-shadow:0 2px 10px rgba(0,0,0,.25); }
.hero-h1-cover { display:none; }
.hero-dates-cover { display:none; }
.hero p.sub { font-size:1.15rem; opacity:.95; margin:0 0 6px; }
.hero .fab4 { margin-top:22px; font-size:.95rem; opacity:.9; }
@media (max-width:700px) { .hero-inner { flex-direction:column-reverse; gap:24px; } .hero-photo img { width:160px; height:160px; } }
.hero-nav { display:flex; flex-wrap:wrap; justify-content:center; gap:14px 16px; margin:22px 0 8px; }
.hero-nav a { display:inline-flex; align-items:center; gap:7px; text-decoration:none; font-weight:600; color:#fff; font-size:.88rem; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.4); padding:9px 18px; border-radius:999px; transition:background .15s; }
.hero-nav a:hover { background:rgba(255,255,255,.32); }
.hero-nav .ic { font-size:1.05rem; line-height:1; }
.nav-grid { display:flex; flex-wrap:wrap; justify-content:center; gap:18px 16px; margin:22px 0 14px; }
.nav-col { display:flex; flex-direction:column; align-items:center; gap:6px; }
.nav-col a { display:inline-flex; align-items:center; gap:7px; text-decoration:none; font-weight:600; color:#fff; font-size:.88rem; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.4); padding:9px 18px; border-radius:4px 4px 0 0; transition:background .15s; width:100%; justify-content:center; box-sizing:border-box; }
.nav-col a:hover { background:rgba(255,255,255,.32); }
.nav-col .ic { font-size:1.05rem; line-height:1; }
.nav-col .print-mini { width:100%; justify-content:center; border-radius:0 0 4px 4px; border-top:none; font-size:.72rem; padding:6px 12px; opacity:.9; }
.nav-col .print-mini:hover { opacity:1; }
.ship-banner { margin:0 0 22px; border-radius:12px; overflow:hidden; box-shadow:0 1px 6px rgba(0,0,0,.12); }
.ship-banner img { width:100%; display:block; max-height:420px; object-fit:cover; }
.deck-plan-btn-row { display:flex; justify-content:center; padding:14px 0; background:#fff; }
.qv4-map-wrap { background:#fff; padding:0 12px 16px; text-align:center; }
.qv4-map-img { width:100%; max-width:100%; height:auto; display:block; margin:0 auto; border:1px solid #e3ddc9; border-radius:8px; }
.qv4-caption { font-size:.78rem; color:var(--muted); margin-top:8px; font-style:italic; }
.cabin-box { background:#eef4fb; border:1px solid #c8d9ec; border-radius:10px; padding:14px 18px; margin:0 0 18px; }
.cabin-box-title { font-weight:700; color:var(--navy); margin-bottom:8px; }
.cabin-row { display:flex; align-items:center; gap:12px; padding:3px 0; font-size:.95rem; }
.cabin-num { display:inline-block; min-width:56px; padding:2px 8px; background:var(--navy); color:#fff; border-radius:5px; font-weight:700; text-align:center; }
.cabin-who { color:#333; }
.cabin-note { font-size:.78rem; color:var(--muted); margin-top:8px; font-style:italic; }
.mandatory-fee-box { display:flex; align-items:flex-start; gap:8px; margin-top:8px; padding:7px 10px; background:#eef8ee; border:1.5px solid #8fce8f; border-radius:7px; }
.currency-badge { flex:0 0 auto; display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#3f9142; color:#fff; font-size:.72rem; font-weight:700; line-height:1; }
.mandatory-fee-text { font-size:.76rem; color:#2e5c2e; line-height:1.35; }
section { max-width:1080px; margin:0 auto; padding:48px 20px 8px; }
section h2 { font-size:1.7rem; color:var(--navy); border-left:6px solid var(--gold); padding-left:14px; margin-bottom:6px; }
section h3 { color:var(--navy); margin-top: 30px; }
section .lede { color:var(--muted); margin-bottom:26px; font-size:.98rem; }
.timeline { display:grid; gap:10px; margin-bottom:20px; }
#overview { padding:10px 16px 2px; }
#overview h2 { font-size:1.22rem; margin-bottom:2px; padding-left:8px; border-left-width:4px; }
#overview .lede { margin-bottom:4px; font-size:.78rem; }
#overview .timeline { gap:1px; margin-bottom:3px; }
#overview .tl-row { padding:2px 7px; gap:6px; grid-template-columns:90px 1fr 24px; border-radius:5px; }
#overview .tl-date { font-size:.68rem; }
#overview .tl-daynum { font-size:.58rem; font-weight:400; }
#overview .tl-where { font-size:.8rem; }
#overview .tl-what { font-size:.7rem; line-height:1.18; }
#overview .tl-notes { font-size:.62rem; margin-top:0; line-height:1.15; }
#overview .tl-flag { font-size:.95rem; }
#overview .tl-status { font-size:.54rem; padding:1px 4px; }
#overview .tl-dst { font-size:.6rem; margin-top:0; }
.tl-status { display:inline-block; font-size:.68rem; font-weight:800; letter-spacing:.03em; padding:2px 7px; border-radius:8px; vertical-align:middle; margin-left:4px; }
.tl-status-confirmed { background:#1f8f4e; color:#fff; }
.tl-status-unconfirmed { background:#c62828; color:#fff; }
.tl-dst { color:var(--gold); font-weight:700; font-size:.82rem; margin-top:3px; }
.tl-row { display:grid; grid-template-columns:130px 1fr 32px; gap:14px; background:var(--card-bg); border-radius:10px; padding:12px 16px; box-shadow:0 1px 4px rgba(0,0,0,.06); border-left:5px solid var(--navy); }
.tl-row.rome { border-left-color:var(--rome); }
.tl-row.cruise { border-left-color:var(--cruise); }
.tl-row.tuscany { border-left-color:var(--tuscany); }
.tl-row.london { border-left-color:var(--london); }
.tl-row.milan { border-left-color:var(--milan); }
.tl-row.air { border-left-color:#999; }
.tl-date { font-weight:700; color:var(--navy); font-size:.88rem; }
.tl-daynum { font-weight:400; color:var(--navy); opacity:.7; font-size:.74rem; }
.tl-where { font-weight:700; }
.tl-what { color:var(--ink); font-size:.92rem; }
.tl-notes { color:var(--muted); font-size:.82rem; margin-top:2px; }
.tl-flag { font-size:1.4rem; align-self:center; justify-self:center; line-height:1; }
.day-card { background:var(--card-bg); border-radius:12px; margin-bottom:20px; overflow:hidden; box-shadow:0 1px 6px rgba(0,0,0,.08); }
.day-head { padding:12px 18px; font-weight:700; color:#fff; font-size:1.02rem; letter-spacing:.3px; display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
.day-loc { font-weight:600; font-size:.82rem; letter-spacing:.4px; text-transform:uppercase; background:rgba(255,255,255,.22); padding:4px 12px; border-radius:999px; }
.day-head-right { display:flex; align-items:center; gap:8px; }
.print-day-btn { background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.5); color:#fff; font-size:.72rem; font-weight:700; padding:4px 11px; border-radius:999px; cursor:pointer; }
.print-day-btn:hover { background:rgba(255,255,255,.32); }
.day-map-box { margin-top:16px; padding:16px 18px; background:#faf9f5; border:1px dashed #d9d3c4; border-radius:10px; }
.dinner-box { margin-top:16px; padding:16px 18px; background:#fdf6ec; border:1px dashed var(--gold); border-radius:10px; }
.dinner-box .place-grid { margin:10px 0 0; }
.option-box { margin-top:16px; padding:16px 18px; background:#eef3fb; border:1px dashed var(--london); border-radius:10px; }
.option-box .place-grid { margin:10px 0 0; grid-template-columns:1fr; max-width:340px; }
.option-box .place-grid.place-grid-wide { grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); max-width:700px; }
@media (max-width:600px) { .option-box .place-grid.place-grid-wide { grid-template-columns:1fr; } }
.option-box-title { font-weight:700; color:var(--navy); margin-bottom:4px; font-size:.95rem; }
.option-box-sub { color:var(--muted); font-size:.82rem; margin-bottom:6px; }
.day-map-title { font-weight:700; color:var(--navy); margin-bottom:8px; font-size:.95rem; }
.day-map-caption { color:var(--muted); font-size:.78rem; font-style:italic; margin-top:8px; }
.day-map-timeline { display:flex; flex-direction:column; }
.dm-stop { display:flex; align-items:flex-start; gap:12px; }
.dm-dot { flex:0 0 auto; width:16px; height:16px; border-radius:50%; background:var(--london); margin-top:2px; box-shadow:0 0 0 3px #fff, 0 0 0 4px var(--london); }
.dm-stop-body { flex:1 1 auto; padding-bottom:2px; }
.dm-name { font-weight:600; }
.dm-note { color:var(--muted); font-size:.85rem; margin-top:2px; }
.dm-leg { display:flex; align-items:stretch; gap:12px; }
.dm-leg-line { flex:0 0 16px; width:16px; position:relative; min-height:36px; }
.dm-leg-line::before { content:''; position:absolute; left:50%; top:0; bottom:0; border-left:3px dashed var(--gold); transform:translateX(-1.5px); }
.dm-leg-body { flex:1 1 auto; padding:6px 0 10px; }
.dm-leg-head { font-weight:600; font-size:.85rem; color:var(--cruise); }
.dm-leg-text { color:var(--muted); font-size:.85rem; font-style:italic; margin-top:2px; }
.theme-london .day-head { background:linear-gradient(90deg, var(--london), #4a68c9); }
.theme-italy .day-head { background:linear-gradient(90deg, var(--rome), #a83a3a); }
.theme-cruise .day-head { background:linear-gradient(90deg, var(--cruise), #14a3ac); }
.theme-tuscany2 .day-head { background:linear-gradient(90deg, var(--tuscany), #4d9a63); }
.theme-milan2 .day-head { background:linear-gradient(90deg, var(--milan), #9a6cc9); }
.day-body { padding:6px 18px 14px; }
.ev-row { display:grid; grid-template-columns:110px 1fr; gap:14px; padding:10px 0; border-bottom:1px solid #f0eee8; }
.ev-row:last-child { border-bottom:none; }
.ev-time { font-weight:700; color:var(--navy); font-size:.85rem; }
.ev-name { font-weight:600; }
.ev-addr { color:var(--muted); font-size:.85rem; margin-top:2px; }
.ev-note { color:var(--muted); font-size:.85rem; font-style:italic; margin-top:2px; }
.ev-empty { color:var(--muted); font-style:italic; padding:10px 0; }
.ev-stay { margin-top:8px; font-size:.85rem; color:var(--gold); font-weight:600; }
.fun-fact-box { border:1px solid var(--gold); border-radius:8px; padding:10px 14px; margin-bottom:14px; background:#fffcf3; }
.fun-fact-label { font-weight:700; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; color:var(--gold); margin-bottom:4px; }
.fun-fact-text { font-size:.85rem; color:var(--ink); line-height:1.45; }
.fun-fact-text + .fun-fact-text { margin-top:8px; padding-top:8px; border-top:1px dashed #eee6cf; }
.fun-fact-text a { color:var(--cruise); }
.fun-fact-source { color:var(--muted); font-size:.8rem; white-space:nowrap; }
.ffp-day { border:1px solid var(--gold); border-radius:8px; padding:12px 16px; margin-bottom:14px; background:#fffcf3; page-break-inside:avoid; break-inside:avoid; }
.ffp-day-title { font-size:.95rem; color:var(--navy); margin:0 0 8px; }
.ec-boxes { display:flex; flex-wrap:wrap; gap:20px; margin-top:14px; }
.ec-box { flex:1 1 320px; border:1px solid var(--gold); border-radius:10px; padding:18px 20px; background:#fffcf3; page-break-inside:avoid; break-inside:avoid; }
.ec-box-title { color:var(--navy); margin:0 0 12px; font-size:1.08rem; }
.ec-people { display:flex; flex-direction:column; gap:12px; }
.ec-person { border-top:1px dashed #eee6cf; padding-top:12px; }
.ec-person:first-child { border-top:none; padding-top:0; }
.ec-person-name { font-weight:700; color:var(--ink); margin-bottom:4px; font-size:.95rem; }
.ec-line { font-size:.85rem; color:var(--muted); }
.ec-blank { color:#b9ac7e; font-style:italic; font-weight:600; }
.ec-blank-line { color:#ccc; }
@media print { .ec-box { break-inside:avoid; } }
.td-row { display:flex; align-items:center; gap:14px; margin:14px 0; }
.td-btn { min-width:140px; text-align:center; }
.td-qr { width:70px; height:70px; border:1px solid #ddd; border-radius:6px; background:#fff; padding:3px; }
.place-fact { margin-top:8px; padding-top:8px; border-top:1px dashed #e3ddc9; font-size:.78rem; color:var(--muted); font-style:italic; line-height:1.4; }
.place-hours { font-size:.78rem; color:var(--navy); font-weight:600; margin:2px 0 6px; }
body.hide-facts .fun-fact-box, body.hide-facts .place-fact { display:none !important; }
.badge { display:inline-block; font-size:.7rem; font-weight:700; padding:2px 9px; border-radius:999px; margin-left:6px; vertical-align:middle; text-transform:uppercase; letter-spacing:.3px; }
.badge-booked { background:#e3f6e8; color:#1e7d3a; }
.w3w-badge { display:inline-block; background:#000; color:#fff; font-size:.75rem; font-weight:700; padding:2px 8px; border-radius:3px; margin-left:6px; vertical-align:middle; text-decoration:none; letter-spacing:.2px; }
.ev-qr { display:inline-flex; flex-direction:column; align-items:center; gap:2px; margin:6px 0; }
.ev-qr img { width:88px; height:88px; border:1px solid #ddd; border-radius:6px; padding:4px; background:#fff; }
.ev-qr-label { font-size:.7rem; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }
.w3w-badge:hover { background:#222; }
.badge-tobook { background:#fdecd6; color:#b6591a; }
.badge-toconfirm { background:#e5edfb; color:#1f4fa6; }
.badge-optional { background:#f1eef8; color:#6a3fa0; }
.place-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:14px; margin:18px 0 30px; }
.place-card { position:relative; background:var(--card-bg); border-radius:10px; padding:14px 16px; box-shadow:0 1px 5px rgba(0,0,0,.07); border-top:4px solid var(--gold); }
.place-qr-corner { position:absolute; bottom:8px; right:8px; width:34px; height:34px; display:block; line-height:0; }
.place-qr-corner img { width:100%; height:100%; border:1px solid #ddd; border-radius:3px; background:#fff; padding:1px; }
.place-photo { width:100%; height:130px; object-fit:cover; border-radius:12px; border:3px solid var(--photo-frame); margin-bottom:8px; display:block; }
.place-photo-btn { margin-bottom:10px; }
.place-website-btn { display:inline-block; background:#c0392b !important; }
.pill-website { background:#c0392b; }
.place-name { font-weight:700; margin-bottom:2px; }
.place-type { font-size:.8rem; color:var(--rome); margin-bottom:4px; }
.place-addr { font-size:.82rem; color:var(--muted); margin-bottom:10px; min-height:2.2em; }
.place-links { display:flex; gap:6px; flex-wrap:wrap; }
@media print { .place-photo, .place-photo-btn { display:none; } }
.resto-list { display:flex; flex-direction:column; gap:14px; margin:18px 0 30px; }
.resto-item { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; background:var(--card-bg); border-radius:10px; padding:14px 18px; box-shadow:0 1px 5px rgba(0,0,0,.07); border-left:4px solid var(--milan); }
.resto-info { flex:1 1 auto; min-width:0; }
.resto-photo { flex:0 0 auto; width:120px; height:120px; object-fit:cover; border-radius:12px; border:3px solid var(--photo-frame); box-shadow:0 1px 4px rgba(0,0,0,.15); }
.resto-name { font-weight:700; font-size:1.02rem; margin-bottom:2px; }
.resto-hours { font-size:.82rem; color:var(--milan); margin-bottom:4px; }
.resto-addr { font-size:.85rem; color:var(--muted); margin-bottom:6px; }
.resto-dist { font-size:.85rem; color:var(--ink); margin-bottom:10px; }
.resto-dist-ic { margin-right:6px; }
.resto-links { display:flex; gap:6px; flex-wrap:wrap; }
@media print { .resto-photo { display:none; } .resto-item { display:block; } }
@media (max-width:520px) { .resto-item { flex-direction:column; } .resto-photo { width:100%; height:160px; } }
.pill { font-size:.75rem; text-decoration:none; background:var(--navy); color:#fff !important; padding:4px 11px; border-radius:999px; font-weight:600; }
.pill-review { background:var(--gold); }\n.pill-booking { background:#1f8a5f; }\n.ev-link { margin-top:6px; }\n.pill-weblink { background:var(--cruise); }\n.pill-directions { background:#8a5a1f; }\n.pill-instagram { background:#c13584; padding:4px 10px; font-weight:800; }\n.pill-todo { display:inline-block; background:#d64545; color:#fff !important; font-size:.68rem; font-weight:800; padding:2px 9px; border-radius:999px; margin-left:6px; letter-spacing:.4px; vertical-align:middle; }\n.ev-logo { height:34px; width:34px; vertical-align:middle; margin-left:6px; border-radius:50%; box-shadow:0 1px 4px rgba(0,0,0,.25); }\n.ev-photo { display:block; width:100%; max-width:320px; height:180px; object-fit:cover; border-radius:12px; border:3px solid var(--photo-frame); margin-top:8px; box-shadow:0 1px 5px rgba(0,0,0,.15); }\n@media print { .ev-photo { display:none; } }\n.ev-photo-row { display:flex; align-items:flex-start; gap:16px; flex-wrap:wrap; }\n.ev-photo-row .ev-photo { margin-top:8px; flex:0 0 auto; }\n.walk-map-wrap { display:flex; align-items:center; gap:12px; margin-top:8px; flex:0 0 auto; }\n.walk-map { display:block; width:100%; max-width:320px; height:auto; border-radius:12px; border:3px solid var(--photo-frame); box-shadow:0 1px 5px rgba(0,0,0,.15); }\n.walk-info { font-size:.82rem; color:var(--ink); max-width:150px; }\n.walk-time { font-weight:700; margin-bottom:4px; }\n.walk-dist { color:var(--muted); margin-bottom:4px; }\n.walk-note { color:var(--muted); font-size:.78rem; }\n@media print { .walk-map-wrap { display:none; } }\n@media (max-width:900px) { .ev-photo-row { flex-direction:column; } .walk-map-wrap { margin-top:0; } }\n@media (max-width:600px) { .walk-map-wrap { flex-direction:column; align-items:flex-start; width:100%; } .walk-map { max-width:100%; } .walk-info { max-width:100%; margin-top:8px; } }\n.travel-opts { margin-top:10px; padding-top:8px; border-top:1px dashed #e2ddd0; font-size:.82rem; }\n.travel-opts-title { font-weight:700; color:var(--muted); text-transform:uppercase; font-size:.72rem; letter-spacing:.4px; margin-bottom:6px; }\n.travel-opt { margin:4px 0; color:var(--ink); }\n.travel-opt-label { font-weight:700; margin-right:6px; }\n@media print { .travel-opts { display:none; } }\n.ig-note { font-size:.78rem; color:var(--muted); font-style:italic; margin:-14px 0 20px; }
.shop-list { margin-top:10px; padding-top:8px; border-top:1px dashed #e2ddd0; }
.shop-list-title { font-size:.78rem; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:.4px; margin-bottom:6px; }
.shop-item { display:flex; align-items:center; gap:8px; margin:5px 0; flex-wrap:wrap; }
.shop-name { font-weight:600; font-size:.88rem; min-width:180px; }
.shop-addr-text { font-size:.76rem; color:var(--muted); }
.map-wrap { background:var(--card-bg); border-radius:12px; padding:14px; box-shadow:0 1px 6px rgba(0,0,0,.08); margin:16px 0 30px; text-align:center; }
.map-wrap img { max-width:100%; border-radius:8px; }
.map-wrap .cap { color:var(--muted); font-size:.82rem; margin-top:8px; font-style:italic; }
table.ttc, table.ntb { width:100%; border-collapse:collapse; background:var(--card-bg); border-radius:10px; overflow:hidden; box-shadow:0 1px 6px rgba(0,0,0,.07); margin-bottom:30px; font-size:.9rem; }
table.ttc th, table.ntb th { background:var(--navy); color:#fff; padding:10px 12px; text-align:left; font-size:.82rem; }
table.ttc td, table.ntb td { padding:10px 12px; border-bottom:1px solid #f0eee8; vertical-align:top; }
.ttc-day, .ntb-date { font-weight:700; white-space:nowrap; color:var(--navy); }
.ttc-notes, .ntb-notes { color:var(--muted); font-size:.85rem; }
table.flight-table { font-size:.82rem; }
table.flight-table th, table.flight-table td { padding:8px 9px; }
table.flight-table tr.flight-gk td { background:var(--london-light); }
table.flight-table tr.flight-dt td { background:var(--tuscany-light); }
@media print {
  table.flight-table { font-size:.72rem; }
  table.flight-table th, table.flight-table td { padding:5px 6px; }
}
.flight-legend { display:flex; flex-wrap:wrap; gap:18px; align-items:center; font-size:.82rem; color:var(--muted); margin:-14px 0 26px; }
.flight-legend span { display:inline-flex; align-items:center; gap:6px; }
.flight-swatch { display:inline-block; width:14px; height:14px; border-radius:3px; }
.flight-swatch.gk { background:var(--london-light); border:1px solid var(--london); }
.flight-swatch.dt { background:var(--tuscany-light); border:1px solid var(--tuscany); }
.flight-swatch.all { background:var(--card-bg); border:1px solid #ccc; }
.ntb-flag { color:#c0392b; font-weight:700; font-size:.85rem; margin-top:4px; }
.ntb-tick { text-align:center; }
.tickbox { display:inline-block; width:18px; height:18px; border:2px solid var(--navy); border-radius:4px; }
.tt-tick { text-align:center; }
.tt-check { width:20px; height:20px; accent-color:var(--navy); cursor:pointer; }
.tt-note { color:var(--muted); font-size:.82rem; font-style:italic; margin:-10px 0 24px; }
.eta-check { width:20px; height:20px; accent-color:#c0392b; cursor:pointer; }
.uketa-box { margin-top:28px; border:2px solid #c0392b; border-radius:10px; padding:14px 18px; background:#fdecec; }
.uketa-summary { cursor:pointer; font-weight:700; color:#c0392b; font-size:1.02rem; }
.uketa-box .tt-note { margin-top:10px; }
.eta-reminder { display:flex; align-items:center; justify-content:center; gap:10px; flex-wrap:wrap; background:#c0392b; color:#fff; text-align:center; padding:12px 20px; font-weight:700; font-size:.95rem; }
.eta-reminder a { color:#fff; text-decoration:underline; }
.eta-reminder.flashing { animation: eta-flash 1.1s ease-in-out infinite; }
@keyframes eta-flash { 0%, 100% { background:#c0392b; } 50% { background:#e67e22; } }
@media (prefers-reduced-motion: reduce) { .eta-reminder.flashing { animation: none; } }
.japan-banner { text-align:center; padding:50px 20px 60px; background:var(--navy); color:#fff; }
.japan-banner .jb-text { font-size:2rem; font-weight:800; letter-spacing:.03em; margin:0; }
.japan-banner .jb-flag { font-size:2.4rem; display:block; margin-bottom:10px; }
@media (max-width:600px) { .japan-banner .jb-text { font-size:1.3rem; } }
@media print { .japan-banner { display:none !important; } }
.sec-rome { background:var(--rome-light); }
.sec-cruise { background:var(--cruise-light); }
.sec-tuscany { background:var(--tuscany-light); }
.sec-london { background:var(--london-light); }
.sec-milan { background:var(--milan-light); }
.sec-wrap { padding-bottom:40px; }
footer { text-align:center; padding:30px 20px 50px; color:var(--muted); font-size:.85rem; }
.section-head-row { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
.section-head-row h2 { margin-bottom:0; }
.print-btn { display:inline-flex; align-items:center; gap:7px; background:var(--navy); color:#fff; border:none; font-size:.85rem; font-weight:600; padding:8px 16px; border-radius:999px; cursor:pointer; }
.print-btn:hover { background:#16294d; }
.print-btn .ic { font-size:1rem; }
.hero-title-row { display:flex; align-items:center; justify-content:center; gap:16px; flex-wrap:wrap; }
.home-fab { display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.5); color:#fff !important; text-decoration:none; font-size:1.05rem; font-weight:700; padding:12px 22px; border-radius:999px; box-shadow:0 2px 10px rgba(0,0,0,.25); transition:background .15s; }
.home-fab:hover { background:rgba(255,255,255,.32); }
.home-fab .ic { font-size:1.25rem; }
@media (max-width:600px) { .home-fab { padding:9px 16px; font-size:.9rem; } .home-fab .ic { font-size:1.05rem; } }
.home-fab-fixed { position:fixed; bottom:22px; right:22px; z-index:999; display:flex; align-items:center; justify-content:center; width:54px; height:54px; border-radius:50%; background:var(--navy); color:#fff !important; text-decoration:none; font-size:1.5rem; box-shadow:0 3px 14px rgba(0,0,0,.35); transition:background .15s, transform .15s; }
.home-fab-fixed:hover { background:var(--gold); transform:scale(1.06); }
@media (max-width:600px) { .home-fab-fixed { width:46px; height:46px; font-size:1.25rem; bottom:14px; right:14px; } }
.print-row { display:flex; flex-wrap:wrap; justify-content:center; gap:8px; margin:18px 0 4px; }
.print-mini { display:inline-flex; align-items:center; gap:5px; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.4); color:#fff; font-size:.76rem; font-weight:600; padding:6px 13px; border-radius:999px; cursor:pointer; }
.print-mini:hover { background:rgba(255,255,255,.32); }
.print-mini-all { background:var(--gold); border-color:var(--gold); font-weight:700; display:inline-flex; margin:2px auto 4px; padding:8px 20px; font-size:.8rem; }
.print-mini-all:hover { background:#b98a30; }
@media print {
  body, body * { font-family:'Source Sans Pro','Segoe UI',system-ui,sans-serif !important; }
  .home-fab { display:none !important; }
  .no-print { display:none !important; }
  .day-card, .place-card, .tl-row { page-break-inside: avoid; break-inside: avoid; }
  table.ttc tr, table.ntb tr { page-break-inside: avoid; break-inside: avoid; }
  h2 { page-break-before: always; break-before: page; page-break-after: avoid; }
  h3 { page-break-after: avoid; break-after: avoid-page; }
  #flights h2 { page-break-before: avoid; break-before: avoid; }
  .hero, .ship-banner, .map-wrap { page-break-inside: avoid; break-inside: avoid; }
  body.printing-book .day-card, body.printing-book .place-card { page-break-inside: auto; break-inside: auto; }
  body.printing-book .day-card { page-break-before: always; break-before: page; }
  body.printing-book [data-day-id="day-11"] .dinner-box { page-break-before: always; break-before: page; }
  body.printing-book .hero { background:#fff !important; color:var(--navy) !important; padding:0; height:100vh; page-break-after:always; break-after:page; page-break-inside:avoid; display:flex; align-items:center; justify-content:center; }
  body.printing-book .hero-title-row, body.printing-book .hero-flags, body.printing-book .hero p.sub,
  body.printing-book .nav-grid, body.printing-book .hero .fab4 { display:none !important; }
  body.printing-book .hero-inner { display:block; text-align:center; }
  body.printing-book .hero-text { display:block; }
  body.printing-book .hero-h1-cover { display:block; font-size:2.6rem; color:var(--navy); text-shadow:none; margin:0 auto; text-align:center; max-width:640px; }
  body.printing-book .hero-dates-cover { display:block; font-size:1.3rem; color:var(--gold); font-weight:700; letter-spacing:.04em; text-align:center; margin:10px auto 0; }
  body.printing-book .hero-photo { display:block; }
  body.printing-book .hero-photo img { display:block; border-color:var(--navy); box-shadow:none; width:740px; height:740px; margin:26px auto 0; }
''' + '\n'.join(
    f'  body.printing-{sid} .print-block:not([data-section="{sid}"]) {{ display:none !important; }}\n'
    f'  body.printing-{sid} > *:not(.print-block) {{ display:none !important; }}\n'
    f'  body.printing-{sid} .print-block[data-section="{sid}"] {{ padding-top:10px; }}\n'
    f'  body.printing-{sid} .print-block[data-section="{sid}"] h2 {{ page-break-before: avoid; }}'
    for sid in ['flights', 'overview', 'rome', 'cruise', 'tuscany', 'milan', 'london', 'places', 'needtobook', 'hotels', 'funfacts', 'emergencycontacts', 'traveldocuments', 'ztl', 'dailyquiz']
) + '\n' + '\n'.join(
    f'  body.printing-day-{did} [data-day-id]:not([data-day-id="{did}"]) {{ display:none !important; }}\n'
    f'  body.printing-day-{did} .print-block:not(:has([data-day-id="{did}"])) {{ display:none !important; }}\n'
    f'  body.printing-day-{did} > *:not(.print-block) {{ display:none !important; }}'
    for did in ALL_DAY_IDS
) + '\n' + '\n'.join(
    f'  body.printing-sub-{sub} [data-subsection]:not([data-subsection="{sub}"]) {{ display:none !important; }}\n'
    f'  body.printing-sub-{sub} .print-block:not([data-subsection="{sub}"]):not(:has([data-subsection="{sub}"])) {{ display:none !important; }}\n'
    f'  body.printing-sub-{sub} > *:not(.print-block) {{ display:none !important; }}'
    for sub in SUB_IDS
) + '''
  body[class*="printing-sub-"] #london > *:not(.print-block) { display:none !important; }
  body[class*="printing-sub-"] { font-size:.82em; }
  body[class*="printing-sub-"] .lede { display:none !important; }
  body[class*="printing-sub-"] .place-grid { grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:8px; margin:8px 0; }
  body[class*="printing-sub-"] .place-card { padding:6px 8px; }
  body[class*="printing-sub-"] .place-photo, body[class*="printing-sub-"] .place-photo-btn { display:none !important; }
  body[class*="printing-sub-"] .place-addr { min-height:0; margin-bottom:4px; }
  body[class*="printing-sub-"] .place-hours { margin:1px 0 3px; }
  body[class*="printing-sub-"] .place-fact { display:none !important; }
''' + '''
  body[class*="printing-day-"] h2, body[class*="printing-day-"] h3, body[class*="printing-day-"] table.ttc,
  body[class*="printing-day-"] .lede, body[class*="printing-day-"] .ig-note, body[class*="printing-day-"] .place-grid {
    display:none !important;
  }
  body[class*="printing-day-"] .day-card { page-break-inside: auto; break-inside: auto; padding-top:4px; }
  body[class*="printing-day-"] .day-map-box { page-break-before: always; break-before: page; page-break-inside: auto; margin-top:0; padding:8px 10px; }
  body[class*="printing-day-"] .day-map-timeline, body[class*="printing-day-"] .dm-stop, body[class*="printing-day-"] .dm-leg {
    display:block !important;
  }
  body[class*="printing-day-"] .dm-leg-line { display:none !important; }
  body[class*="printing-day-"] .dm-stop-body, body[class*="printing-day-"] .dm-leg-body { page-break-inside: avoid; break-inside: avoid; }
  body[class*="printing-day-"] { font-size:.86em; }
  body[class*="printing-day-"] .day-head { padding:7px 12px; }
  body[class*="printing-day-"] .day-body { padding:3px 12px 8px; }
  body[class*="printing-day-"] .ev-row { padding:5px 0; gap:10px; }
  body[class*="printing-day-"] .fun-fact-box { display:none !important; }
  body[class*="printing-day-"] .day-map-title { margin-bottom:4px; }
  body[class*="printing-day-"] .day-map-caption { margin-top:4px; }
  body[class*="printing-day-"] .dm-leg-body { padding:2px 0 4px; }
  body[class*="printing-day-"] .dm-stop-body { padding-bottom:1px; }
  body.printing-book .ev-photo, body.printing-book .day-map-box, body.printing-book .walk-map-wrap, body.printing-book .travel-opts { display:none !important; }
  body[class*="printing-day-"] .ship-banner { display:none !important; }
  body[class*="printing-day-"] .tube-info-box { display:none !important; }
  body[class*="printing-day-"] .resto-list { display:none !important; }
  body[class*="printing-day-"] .london-quicklinks { display:none !important; }
  body.printing-book .fun-fact-box { display:none !important; }
  body.printing-book #funfacts { display:none !important; }
  body.printing-all .day-card { page-break-before: always; break-before: page; page-break-inside: auto; padding-top:4px; }
  body.printing-all .day-map-box { page-break-before: always; break-before: page; page-break-inside: auto; margin-top:0; padding:8px 10px; }
  body.printing-all .day-map-timeline, body.printing-all .dm-stop, body.printing-all .dm-leg { display:block !important; }
  body.printing-all .dm-leg-line { display:none !important; }
  body.printing-all .dm-stop-body, body.printing-all .dm-leg-body { page-break-inside: avoid; break-inside: avoid; padding:2px 0 4px; }
  body.printing-all .dm-stop-body { padding-bottom:1px; }
  body.printing-all .day-map-title { margin-bottom:4px; }
  body.printing-all .day-map-caption { margin-top:4px; }
''' + '\n'.join(
    f'  body.printing-{sid} {{ font-size:.86em; }}\n'
    f'  body.printing-{sid} .day-card {{ page-break-inside: auto; break-inside: auto; padding-top:4px; }}\n'
    f'  body.printing-{sid} .day-head {{ padding:7px 12px; }}\n'
    f'  body.printing-{sid} .day-body {{ padding:3px 12px 8px; }}\n'
    f'  body.printing-{sid} .ev-row {{ padding:5px 0; gap:10px; }}\n'
    f'  body.printing-{sid} .fun-fact-box {{ display:none !important; }}\n'
    f'  body.printing-{sid} .day-map-box {{ page-break-before: always; break-before: page; page-break-inside: auto; margin-top:0; padding:8px 10px; }}\n'
    f'  body.printing-{sid} .day-map-title {{ margin-bottom:4px; }}\n'
    f'  body.printing-{sid} .day-map-caption {{ margin-top:4px; }}\n'
    f'  body.printing-{sid} .day-map-timeline, body.printing-{sid} .dm-stop, body.printing-{sid} .dm-leg {{ display:block !important; }}\n'
    f'  body.printing-{sid} .dm-leg-line {{ display:none !important; }}\n'
    f'  body.printing-{sid} .dm-stop-body, body.printing-{sid} .dm-leg-body {{ page-break-inside: avoid; break-inside: avoid; padding:2px 0 4px; }}\n'
    f'  body.printing-{sid} .ship-banner {{ display:none !important; }}\n'
    f'  body.printing-{sid} .tube-info-box {{ display:none !important; }}\n'
    f'  body.printing-{sid} .resto-list {{ display:none !important; }}\n'
    f'  body.printing-{sid} .london-quicklinks {{ display:none !important; }}'
    for sid in ['rome', 'cruise', 'tuscany', 'milan', 'london']
) + '''
  @page { margin: 8mm; }
}
@media (max-width:600px) {
  .hero h1 { font-size:1.9rem; }
  .tl-row, .ev-row { grid-template-columns:1fr; }
}
.quiz-day-box { background:var(--card-bg); border-radius:10px; padding:14px 18px; box-shadow:0 1px 5px rgba(0,0,0,.07); border-top:4px solid var(--gold); margin-bottom:14px; }
.quiz-day-head { font-weight:700; color:var(--navy); margin-bottom:8px; }
.quiz-q-list { margin:0; padding-left:22px; }
.quiz-q-list li { margin-bottom:10px; }
.quiz-q-text { font-weight:600; color:var(--ink); }
.quiz-opts { font-size:.84rem; color:var(--muted); margin-top:2px; }
.quiz-answers-hidden { display:none; }
body.printing-sub-quizanswers .quiz-answers-hidden { display:block !important; }
body[class*="printing-sub-"] #dailyquiz > *:not(.print-block) { display:none !important; }
body.printing-dailyquiz .print-block[data-subsection="quizquestions"] { display:block !important; }
@media print {
  .quiz-day-box { page-break-inside: avoid; break-inside: avoid; }
  .quiz-answer-day { page-break-inside: avoid; break-inside: avoid; margin-bottom:14px; }
  .quiz-answer-day h3 { color:var(--navy); font-size:.98rem; margin-bottom:6px; page-break-before:avoid !important; }
  .quiz-answer-day ol { margin:0; padding-left:20px; }
  .quiz-answer-day li { margin-bottom:5px; font-size:.85rem; }
  .quiz-note { color:var(--muted); font-style:italic; }
}
'''

FLIGHTS = [
    ('Thu 10 Sept', 'QF162', 'Qantas', 'T1 &rarr; T1', 'Wellington (WLG) &rarr; Sydney (SYD)', '6:05am &rarr; 7:45am', 'Business', '3h 40m', 'gk'),
    ('Thu 10 Sept', 'QF1', 'Qantas', 'T1 &rarr; T1', 'Sydney (SYD) &rarr; Singapore (SIN)', '2:45pm &rarr; 9:15pm', 'Premium Economy', '8h 30m', 'all'),
    ('Thu 10 &ndash; Fri 11 Sept', 'BA12', 'British Airways', 'T1 &rarr; T5', 'Singapore (SIN) &rarr; London Heathrow (LHR)', '11:20/11:25pm &rarr; 6:35am +1', 'Premium Economy', '~14h 10-15m', 'all'),
    ('Fri 11 Sept', 'BA548', 'British Airways', 'T5 &rarr; T3', 'London Heathrow (LHR) &rarr; Rome Fiumicino (FCO)', '8:00am &rarr; 11:35am', 'Business', '2h 35m', 'gk'),
    ('Fri 11 Sept', 'BA548', 'British Airways', 'T5 &rarr; T3', 'London Heathrow (LHR) &rarr; Rome Fiumicino (FCO)', '8:00am &rarr; 11:35am', 'Economy', '2h 35m', 'dt'),
    ('Thu 24 Sept', 'BA575', 'British Airways', 'n/a &rarr; T5', 'Milan Linate (LIN) &rarr; London Heathrow (LHR)', '3:55pm &rarr; 4:50pm', 'Business', '1h 55m', 'all'),
    ('Sun 27 &ndash; Mon 28 Sept', 'BA15', 'British Airways', 'T5 &rarr; T1', 'London Heathrow (LHR) &rarr; Singapore (SIN)', '10:00pm &rarr; 6:40pm +1', 'Premium Economy', '13h 40m', 'all'),
    ('Mon 28 &ndash; Tue 29 Sept', 'BA15', 'British Airways', 'T1 &rarr; T1', 'Singapore (SIN) &rarr; Sydney (SYD)', '8:20pm &rarr; 6:05am +1', 'Premium Economy', '7h 45m', 'all'),
    ('Tue 29 Sept', 'QF161', 'Qantas', 'T1 &rarr; n/a', 'Sydney (SYD) &rarr; Wellington (WLG)', '9:35am &rarr; 3:45pm', 'Economy', '3h 10m', 'gk'),
]
FLIGHT_WHO = {'gk': 'Karen &amp; Gary only', 'dt': 'Deb &amp; Tom only', 'all': 'All 4'}
flight_rows_html = ''.join(
    f'<tr class="flight-{who}"><td>{date}</td><td>{flight}</td><td>{terminals}</td><td>{airline}</td><td>{route}</td><td>{times}</td><td>{cabin}</td><td>{dur}</td></tr>'
    for date, flight, airline, terminals, route, times, cabin, dur, who in FLIGHTS
)
FLIGHTS_TABLE_HTML = f'''
<table class="ttc flight-table">
  <tr><th>Date</th><th>Flight</th><th>Terminal</th><th>Airline</th><th>Route</th><th>Depart &rarr; Arrive</th><th>Cabin</th><th>Duration</th></tr>
  {flight_rows_html}
</table>
<div class="flight-legend">
  <span><span class="flight-swatch gk"></span>Karen &amp; Gary only</span>
  <span><span class="flight-swatch dt"></span>Deb &amp; Tom only</span>
  <span><span class="flight-swatch all"></span>All 4 together</span>
</div>
<p class="tt-note">All flights are on 2026 dates, operated by Qantas (QF) and British Airways (BA). Reservation codes: Gary &amp; Karen &ndash; KXFECY / EKNMYW; Deb &amp; Tom &ndash; UWBGQP / EKH3PP (the Akhursts join the group in Sydney, so have no Wellington&ndash;Sydney sector). Frequent flyer numbers, seat assignments and check-in requirements are held in the original Sabre itinerary emails.</p>
<p class="tt-note"><strong>Sydney layover (Thu 10 Sept, ~7 hrs):</strong> Yes, you can leave the airport. As NZ passport holders, Gary &amp; Karen are automatically granted a Special Category (subclass 444) visa on arrival, so there's no separate visa to arrange. A ~7 hour layover is comfortably above the ~5 hour minimum generally recommended to clear immigration, get into the city and back through security in time (allow ~45 min for immigration on arrival, ~60 min for security before the next departure).</p>
<p class="tt-note"><strong>Singapore transit on BA15 (Mon 28 Sept, ~1h 40m):</strong> Everyone must deplane at Changi with all carry-on items &ndash; there's no option to stay onboard. On one ticket with bags checked through you won't need to clear passport control, but you WILL need to re-clear security before boarding the onward Sydney sector, as security is at the gate in Singapore. Queues can be long since the whole aircraft transits at once &ndash; follow the crew's instruction on what time to be back at the gate.</p>
'''

NAV_SECTIONS = [
    ('flights', '&#9992;&#65039;', 'Flights'),
    ('overview', '&#129517;', 'Overview'),
    ('rome', '&#127963;&#65039;', 'Rome'),
    ('cruise', '&#128674;', 'Cruise'),
    ('tuscany', '&#127817;', 'Tuscany'),
    ('milan', '&#128717;&#65039;', 'Milan'),
    ('london', '&#127468;&#127463;', 'London'),
    ('places', '&#128506;&#65039;', 'Places &amp; Maps'),
    ('needtobook', '&#9989;', 'Things to Do'),
    ('hotels', '&#127976;&#65039;', 'Hotel Addresses'),
    ('dailyquiz', '&#129504;', 'Daily Quiz'),
]
UKETA_URL = 'https://www.gov.uk/eta/apply'
POLARSTEPS_URL = 'https://www.polarsteps.com/BaxterBrown/24078717-fab-four-does-europe-26?mode=plan'
CONNECTIONS_PDF_URL = 'audit.pdf'
PRINT_BOOK_PDF_URL = 'fab4-print-book.pdf'
PRINT_ALL_PDF_URL = 'fab4-print-all.pdf'
nav_grid_html = ''.join(
    (
        f'''<div class="nav-col">
      <a href="#{sid}"><span class="ic">{icon}</span>{label}</a>
      <button class="print-mini no-print" onclick="printSection('{sid}')">Print {label}</button>
      {f'<a class="print-mini no-print" href="{HOTEL_MAILTO}"><span class="ic">&#9993;&#65039;</span>Email {label}</a>' if sid == 'hotels' else ''}
    </div>'''
    )
    for sid, icon, label in NAV_SECTIONS
)

CSS = CSS.replace('__EUROPE_MAP_B64__', EUROPE_MAP_B64)

HTML = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Fab 4 Take on Europe</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<a href="#top" class="home-fab-fixed no-print" title="Back to Home">&#127968;</a>

<div class="hero" id="top">
  <div class="hero-inner">
    <div class="hero-text">
      <div class="hero-title-row">
        <a href="#top" class="home-fab no-print"><span class="ic">&#127968;</span>Home</a>
        <h1 class="hero-h1-normal">The Fab 4 Take on Europe</h1>
      </div>
      <h1 class="hero-h1-cover">FAB4 Does Europe &ndash; September 2026</h1>
      <p class="hero-dates-cover">10 &ndash; 29 September 2026</p>
      <div class="hero-flags" aria-label="United Kingdom, Italy, France">&#127468;&#127463; &#127470;&#127481; &#127467;&#127479;</div>
      <p class="sub">10 &ndash; 29 September 2026</p>
      <div class="nav-grid">{nav_grid_html}</div>
      <a class="print-mini print-mini-all no-print" href="{PRINT_BOOK_PDF_URL}" target="_blank" rel="noopener"><span class="ic">&#128214;</span>Print Book</a>
      <a class="print-mini print-mini-all no-print" href="{PRINT_ALL_PDF_URL}" target="_blank" rel="noopener"><span class="ic">&#128424;&#65039;</span>Print All</a>
      <button class="print-mini no-print" id="factsToggleBtn" onclick="toggleFunFacts()"><span class="ic">&#127881;</span>Hide Fun Facts</button>
      <button class="print-mini no-print" onclick="printSection('funfacts')"><span class="ic">&#128424;&#65039;</span>Print Fun Facts</button>
      <div class="fab4">Karen Nicholson &middot; Deb Gyde &middot; Thomas Akhurst &middot; Gary Nicholson</div>
    </div>
    <div class="hero-photo">
      <div class="view-counter no-print" id="viewCounter" title="Website views"><span class="ic">&#128065;&#65039;</span><span id="viewCounterNum">100</span> views</div>
      <img src="data:image/jpeg;base64,{IMG['hero']}" alt="The Fab 4 at dinner">
      <div class="hero-clock no-print" id="heroClock">&nbsp;</div>
      <div class="hero-countdown-wrap no-print">
        <div class="hero-countdown-label">Countdown to Departure</div>
        <div class="flip-clock" id="heroCountdown">
          <div class="flip-unit"><div class="flip-card"><div class="flip-digit" data-unit="days">00</div></div><div class="flip-label">Days</div></div>
          <div class="flip-unit"><div class="flip-card"><div class="flip-digit" data-unit="hours">00</div></div><div class="flip-label">Hrs</div></div>
          <div class="flip-unit"><div class="flip-card"><div class="flip-digit" data-unit="minutes">00</div></div><div class="flip-label">Min</div></div>
          <div class="flip-unit"><div class="flip-card"><div class="flip-digit" data-unit="seconds">00</div></div><div class="flip-label">Sec</div></div>
        </div>
        <a class="polarsteps-link no-print" href="{POLARSTEPS_URL}" target="_blank" rel="noopener"><span class="ic">&#128205;</span>Polarsteps &ndash; Open trip</a>
        <a class="polarsteps-link no-print" href="#emergencycontacts"><span class="ic">&#128222;</span>Emergency Contacts</a>
        <a class="polarsteps-link no-print" href="#traveldocuments"><span class="ic">&#128196;</span>Travel Documents</a>
        <a class="polarsteps-link no-print" href="#ztl"><span class="ic">&#128663;</span>ZTL / Driving Zones</a>
        <a class="polarsteps-link no-print" href="{CONNECTIONS_PDF_URL}" target="_blank" rel="noopener"><span class="ic">&#128203;</span>Audit</a>
        <a class="polarsteps-link no-print" href="#" id="shareSiteBtn" onclick="shareSite(event)"><span class="ic">&#128257;</span>Share This Site</a>
      </div>
    </div>
  </div>
</div>

<div id="etaReminder" class="eta-reminder no-print" style="display:none">
  <span class="ic">&#9888;&#65039;</span>
  <span id="etaReminderText">Reminder: Do our UK ETA's!</span>
  <a href="{UKETA_URL}" target="_blank" rel="noopener" onclick="revealEtaChecklist()">Go to checklist</a>
</div>

<div id="passportReminder" class="eta-reminder no-print" style="display:none">
  <span class="ic">&#9888;&#65039;</span>
  <span id="passportReminderText">Reminder: Check our passports are valid!</span>
  <a href="#needtobook" onclick="revealPassportChecklist()">Go to checklist</a>
</div>

<section id="flights" class="print-block" data-section="flights">
  <h2>Flight Summary</h2>
  {FLIGHTS_TABLE_HTML}
</section>

<section id="overview" class="print-block" data-section="overview">
  <h2>Trip at a Glance</h2>
  <div class="timeline">
    {timeline_html}
  </div>
</section>

<div class="sec-wrap sec-rome print-block" data-section="rome">
<section id="rome">
  <h2>Rome</h2>
  <p class="lede">11 &ndash; 14 September &middot; The Republic Hotel, Via Gaeta 61</p>
  <p class="ig-note">'I' buttons link to that place's official Instagram page.</p>
  {rome_days_html}

  <h3>Things to Consider &ndash; Rome / Cruise</h3>
  <table class="ttc">
    <tr><th>Day</th><th>Item</th><th>Status</th><th>Notes</th></tr>
    {italy_ttc_html}
  </table>
</section>
</div>

<div class="sec-wrap sec-cruise print-block" data-section="cruise">
<section id="cruise">
  <h2>Queen Victoria Cruise</h2>
  <p class="lede">14 &ndash; 20 September &middot; Marseille &middot; Villefranche &middot; Genoa &middot; La Spezia</p>
  <p class="ig-note">'I' buttons link to that place's official Instagram page.</p>
  <div class="ship-banner">
    <img src="data:image/jpeg;base64,{IMG['ship']}" alt="Cunard Queen Victoria in port">
    <div class="deck-plan-btn-row no-print">
      <a class="pill pill-weblink" href="fab4-qv-deck-plans.pdf" target="_blank" rel="noopener">&#128421;&#65039; Full Deck Plan (PDF)</a>
    </div>
    <div class="qv4-map-wrap">
      <img class="qv4-map-img" src="data:image/png;base64,{IMG['qv8']}" alt="Queen Victoria Deck 8 plan showing staterooms 8118 and 8112 circled">
      <div class="qv4-caption">Deck 8 (Balcony) &ndash; our two staterooms circled</div>
    </div>
  </div>
  {cruise_days_html}

  <h3>Cunard Voyage Info (V618D)</h3>
  <table class="ttc">
    <tr><th>Day</th><th>Port</th><th>Arrives</th><th>Departs</th></tr>
    <tr><td>Mon 14 Sep</td><td>Civitavecchia (depart Rome)</td><td>&ndash;</td><td>Evening</td></tr>
    <tr><td>Tue 15 Sep</td><td>At Sea</td><td>&ndash;</td><td>&ndash;</td></tr>
    <tr><td>Wed 16 Sep</td><td>Marseille, France</td><td>Early morning</td><td>Evening</td></tr>
    <tr><td>Thu 17 Sep</td><td>Villefranche, France</td><td>Early morning</td><td>Evening</td></tr>
    <tr><td>Fri 18 Sep</td><td>Genoa, Italy</td><td>Early morning</td><td>Late evening</td></tr>
    <tr><td>Sat 19 Sep</td><td>La Spezia (tours to Florence or Pisa)</td><td>Early morning</td><td>Evening</td></tr>
    <tr><td>Sun 20 Sep</td><td>At Sea</td><td>&ndash;</td><td>&ndash;</td></tr>
    <tr><td>Mon 21 Sep</td><td>Civitavecchia (disembark)</td><td>Early morning</td><td>&ndash;</td></tr>
  </table>

  <h3>Ship Stats</h3>
  <table class="ttc">
    <tr><th>Guests</th><th>Crew</th><th>Length</th></tr>
    <tr><td>2,059</td><td>913</td><td>964.5 ft</td></tr>
  </table>

  <h3>Onboard &ndash; Things to Check Out</h3>
  <table class="ttc">
    <tr><th>Venue</th><th>Notes</th></tr>
    <tr><td>Gala evenings</td><td>Formal nights with themed menus, cocktails, decorations, music and dancing</td></tr>
    <tr><td>Princess Grill Restaurant</td><td>Reserved table each night, elevated menu, sea views</td></tr>
    <tr><td>Chart Room</td><td>Signature venue with zodiac-themed cocktails, dark woods, golden lighting</td></tr>
    <tr><td>Queens Room</td><td>Fencing classes, Afternoon Tea, live music, dancing</td></tr>
    <tr><td>Grill Suites Terrace/Courtyard</td><td>Outdoor sanctuary for Queens/Princess Grill Suite guests, sun loungers, drinks service</td></tr>
    <tr><td>Gym</td><td>Included in fare, guests 16+, sea views, optional fitness classes/personal training</td></tr>
    <tr><td>Children's clubs</td><td>Under-18s, book via the My Voyage portal on board &ndash; games, arts and crafts, activities</td></tr>
  </table>

  <p class="ig-note">Full deck plan: <a href="https://www.cunard.com/dam/inventory-assets/ships/QV/0/qv-deck-plan-november-2025.pdf.pdf" target="_blank" rel="noopener">View Deck Plan (PDF)</a></p>
  <div class="ship-banner">
    <img src="data:image/jpeg;base64,{IMG['ship_at_sea']}" alt="Cunard Queen Victoria under way at sea">
    <div class="qv4-caption" style="padding:8px 12px 14px;text-align:center;">Fair winds &ndash; the Queen Victoria at sea</div>
  </div>
</section>
</div>

<div class="sec-wrap sec-tuscany print-block" data-section="tuscany">
<section id="tuscany">
  <h2>Tuscany</h2>
  <p class="lede">21 &ndash; 22 September &middot; Hotel Borgo di Cortefreda Relais, Tavarnelle Val di Pesa</p>
  <p class="ig-note">'I' buttons link to that place's official Instagram page.</p>
  {tuscany_days_html}

  <h3>Mercedes Drive Times &ndash; Monday 21 September</h3>
  <table class="ttc">
    <tr><th>Leg</th><th>Approx. Distance</th><th>Approx. Drive Time</th><th>Notes</th></tr>
    {drive_times_html}
  </table>
  <p class="lede">Estimates only &ndash; not a live routing query. Confirm via GPS/Google Maps on the day; actual times will vary with traffic and any stops.</p>
</section>
</div>

<div class="sec-wrap sec-milan print-block" data-section="milan">
<section id="milan">
  <h2>Milan</h2>
  <p class="lede">23 September &middot; iQ Hotel Milano</p>
  <p class="ig-note">'I' buttons link to that place's official Instagram page.</p>
  {milan_days_html}

  <h3>Alternative Options for 23 September</h3>
  <p class="lede">Four alternative full-day plans in place of the base Tuscany &rarr; Milan drive above &ndash; pick one.</p>
  <p class="lede"><strong>Note on Option C:</strong> Venice is a significant detour east before doubling back west to Milan &ndash; approx. 610 km / ~6h 20m total driving (vs. ~1h 30m for the base plan, ~5h 15m for Option A, ~3h 40m for Option B). Also note Venice's historic centre is car-free, so the car must be left at Tronchetto or Piazzale Roma and the centre reached on foot/vaporetto. Worth confirming everyone's comfortable with the long day before booking.</p>
  {italy_options_html}

  <h3>Potential Dinner Restaurants &ndash; Milan (23 September, all 3 plans)</h3>
  <p class="lede">All confirmed open on a Wednesday. The first three (Cantine Milano, L'Immagine, Casa Festa) were the original shortlist; the five below (Osteria Cornalia, Da Gigi, Osteria Nanin - Torriani, Giannino dal 1899, Pizza Shamb&ograve;) are all 4-5 star Italian/Mediterranean options and much closer to the hotel (6-12 min walk, except Pizza Shamb&ograve; at ~25 min). Hours and ratings sourced online &ndash; please reconfirm nearer the date. Distances are estimates only, from iQ Hotel Milano.</p>
  <div class="resto-list">{milan_dinner_stack_html}</div>
</section>
</div>

<div class="sec-wrap sec-london print-block" data-section="london">
<section id="london">
  <h2>London</h2>
  <p class="lede">24 &ndash; 27 September &middot; The Level at Meli&aacute; White House</p>
  <p class="ig-note">'I' buttons link to that place's official Instagram page.</p>
  {LONDON_TUBE_INFO_HTML}
  {london_days_html}

  <h3>Things to Consider &ndash; London</h3>
  <table class="ttc">
    <tr><th>Day</th><th>Item</th><th>Status</th><th>Notes</th></tr>
    {london_ttc_html}
  </table>

  <div class="print-block" data-subsection="melia20">
  <div class="section-head-row">
    <h3 id="melia20" style="margin-bottom:0;">Within 20 Minutes of the Melia on foot</h3>
    <button class="print-btn no-print" onclick="printSub('melia20')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">20 things to do within roughly a 20-minute walk of The Level at Meli&aacute; White House, Longford Street. Walk times are estimates &ndash; check live maps nearer the time.</p>
  <div class="place-grid">{melia20_html}</div>
  </div>

  <div class="print-block" data-subsection="shops20">
  <div class="section-head-row">
    <h3 id="shops20" style="margin-bottom:0;">20 Shops to See in London</h3>
    <button class="print-btn no-print" onclick="printSub('shops20')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">A top-20 pick of iconic London shops, department stores and markets &ndash; not all are near the hotel, so check travel time before heading out.</p>
  <div class="place-grid">{shops20_html}</div>
  </div>

  <div class="print-block" data-subsection="piccshops20">
  <div class="section-head-row">
    <h3 id="piccshops20" style="margin-bottom:0;">20 Shops within 15 Minutes of Piccadilly Circus</h3>
    <button class="print-btn no-print" onclick="printSub('piccshops20')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">20 shops, arcades and shopping streets all within roughly a 15-minute walk of Piccadilly Circus tube station. Walk times are estimates &ndash; check live maps nearer the time.</p>
  <div class="place-grid">{piccshops20_html}</div>
  </div>

  <div class="print-block" data-subsection="piccthings20">
  <div class="section-head-row">
    <h3 id="piccthings20" style="margin-bottom:0;">20 Things to Do within 15 Minutes of Piccadilly Circus</h3>
    <button class="print-btn no-print" onclick="printSub('piccthings20')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">20 sights, galleries, parks and landmarks all within roughly a 15-minute walk of Piccadilly Circus tube station. Walk times are estimates &ndash; check live maps nearer the time.</p>
  <div class="place-grid">{piccthings20_html}</div>
  </div>

  <div class="print-block" data-subsection="carsbaby">
  <div class="section-head-row">
    <h3 id="carsbaby" style="margin-bottom:0;">Cars Baby Cars</h3>
    <button class="print-btn no-print" onclick="printSub('carsbaby')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">Supercar and luxury-marque showrooms clustered around Berkeley Square, Mayfair &ndash; all within roughly a 15-minute walk of Piccadilly Circus.</p>
  <div class="place-grid">{carsbaby_html}</div>
  <p class="lede" style="margin-top:10px;font-style:italic;">{carsbaby_note}</p>
  </div>
</section>
</div>

<section id="places" class="print-block" data-section="places">
  <h2>Places &amp; Maps</h2>
  <p class="lede">Schematic maps and place lists from the itinerary, with website and review links.</p>
  <p class="ig-note">'I' buttons link to that place's official Instagram page.</p>

  <h3>Rome</h3>
  <div class="map-wrap">
    <img src="data:image/png;base64,{IMG['rome']}" alt="Rome detail map">
    <div class="cap">Schematic map &ndash; approximate positions, not to scale</div>
  </div>
  <div class="place-grid">{rome_places_html}</div>

  <h3>Tuscany</h3>
  <div class="map-wrap">
    <img src="data:image/png;base64,{IMG['tuscany']}" alt="Tuscany hotel area map">
    <div class="cap">Schematic map &ndash; approximate positions, not to scale</div>
  </div>
  <div class="place-grid">{tuscany_places_html}</div>

  <h3>Milan</h3>
  <div class="map-wrap">
    <img src="data:image/png;base64,{IMG['milan']}" alt="Milan detail map">
    <div class="cap">Schematic map &ndash; approximate positions, not to scale</div>
  </div>
  <div class="place-grid">{milan_places_html}</div>

  <h3>Italy Overview (cruise ports &amp; drive route)</h3>
  <div class="map-wrap">
    <img src="data:image/png;base64,{IMG['italy']}" alt="Italy overview map">
    <div class="cap">Schematic map &ndash; approximate positions, not to scale</div>
  </div>
  <div class="place-grid">{italy_places_html}</div>

  <h3>London</h3>
  <div class="map-wrap">
    <img src="data:image/png;base64,{IMG['london']}" alt="London detail map">
    <div class="cap">Schematic map &ndash; approximate positions, not to scale</div>
  </div>
  <div class="place-grid">{london_places_html}</div>
</section>

<section id="ztl" class="print-block" data-section="ztl">
  <h2>ZTL / Limited Traffic Zones (Italy)</h2>
  <p class="lede">You asked about "LTZ" areas &ndash; in Italy these are officially called ZTL (Zona a Traffico Limitato), or Limited Traffic Zones. Every historic Italian city centre has one, and they're the single easiest way to rack up fines while self-driving.</p>
  <p class="tt-note">A ZTL is a camera-enforced zone &ndash; usually the old walled/historic centre &ndash; where only residents, permit holders and registered vehicles may drive during posted hours. Drive through the wrong gate and a camera reads the plate; the fine (typically &euro;80&ndash;335, sometimes one per gate crossed) goes to the hire company, who forwards it to us plus their own admin fee &ndash; and it can turn up months after we're home. Watch for the sign: a white circle with a red border reading "Zona Traffico Limitato".</p>
  <div class="map-wrap">
    <img src="data:image/png;base64,{IMG['ztl']}" alt="Schematic map of ZTL zones relevant to our Italy driving route">
    <div class="cap">Schematic map &ndash; approximate positions, not to scale</div>
  </div>
  <div class="place-grid">{ZTL_CARDS_HTML}</div>
  <p class="tt-note">General rule of thumb: park in a signed paid car park outside the old walls/centre and walk in, rather than following the satnav to the door &ndash; it's almost always faster than dealing with a fine later.</p>
</section>

<section id="needtobook" class="print-block" data-section="needtobook">
  <div class="section-head-row">
    <h2>Things to Do</h2>
    <button class="print-btn no-print" onclick="printSection('needtobook')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">Everything still to book or confirm, pulled together from across the itinerary.</p>
  <table class="ntb">
    <tr><th>Date</th><th>Item</th><th>Status</th><th>Notes</th><th>Booked?</th><th>Links</th></tr>
    {ntb_html}
  </table>

  <h3>Things to Take</h3>
  <p class="tt-note">Packing checklist. Tick boxes save in this browser only &mdash; they don't sync back to the spreadsheet, so keep the master list on the Things to Do tab in the workbook up to date separately.</p>
  <table class="ntb">
    <tr><th>Item</th><th>Packed?</th></tr>
    {tt_html}
  </table>

  <details id="uketaDetails" class="uketa-box">
    <summary class="uketa-summary"><span class="ic">&#128179;</span> UK ETA Applications &ndash; tick off once each person has applied</summary>
    <p class="tt-note">Apply here: <a href="{UKETA_URL}" target="_blank" rel="noopener">gov.uk/eta/apply</a> &ndash; each of the 4 of us needs our own UK ETA before flying to London. Tick boxes save in this browser only.</p>
    <table class="ntb">
      <tr><th>Name</th><th>Applied?</th></tr>
      {eta_html}
    </table>
  </details>

  <details id="passportDetails" class="uketa-box">
    <summary class="uketa-summary"><span class="ic">&#128209;</span> Passport Validity Check &ndash; tick off once each passport is confirmed valid</summary>
    <p class="tt-note">Passports need at least 6 months' validity remaining AT THE END of the trip (29 Sept 2026) &ndash; so valid until at least 29 March 2027. Tick boxes save in this browser only.</p>
    <table class="ntb">
      <tr><th>Name</th><th>Checked?</th></tr>
      {passport_html}
    </table>
  </details>
</section>

<section id="hotels" class="print-block" data-section="hotels">
  <div class="section-head-row">
    <h2>Hotel Addresses</h2>
    <button class="print-btn no-print" onclick="printSection('hotels')"><span class="ic">&#128424;&#65039;</span>Print</button>
    <a class="print-btn no-print" href="{HOTEL_MAILTO}"><span class="ic">&#9993;&#65039;</span>Email</a>
  </div>
  <p class="lede">Every hotel on the trip, with address, phone and email &ndash; use Print for a paper copy or a browser "Save as PDF", or Email to send yourself/family a copy.</p>
  <div class="place-grid">{HOTEL_DIRECTORY_HTML}</div>
</section>

<section id="dailyquiz" class="print-block" data-section="dailyquiz">
  <div class="section-head-row">
    <h2>Daily Quiz</h2>
  </div>
  <p class="lede">A 5-question multi-choice quiz for every day of the trip, themed to wherever we are that day &ndash; Rome history, cruise trivia, French Riviera, Tuscany, London and more. Browse the questions below any time, or print two separate documents: one with just the questions, one with the answer key.</p>

  <div class="print-block" data-subsection="quizquestions">
    <div class="section-head-row">
      <h3 id="quizquestions" style="margin-bottom:0;">Questions</h3>
      <button class="print-btn no-print" onclick="printSub('quizquestions')"><span class="ic">&#128424;&#65039;</span>Print Questions</button>
    </div>
    {QUIZ_SCREEN_HTML}
  </div>

  <div class="print-block" data-subsection="quizanswers">
    <div class="section-head-row">
      <h3 id="quizanswers" style="margin-bottom:0;">Answer Key</h3>
      <button class="print-btn no-print" onclick="printSub('quizanswers')"><span class="ic">&#128424;&#65039;</span>Print Answers</button>
    </div>
    <p class="tt-note">Hidden from normal browsing so the quiz stays a surprise &ndash; use Print Answers to check your scores.</p>
    <div class="quiz-answers-hidden">{QUIZ_ANSWER_KEY_HTML}</div>
  </div>
</section>

<section id="tubemap" class="print-block" data-section="tubemap">
  <div class="section-head-row">
    <h2>London Tube Map</h2>
  </div>
  <p class="lede">The official TfL Tube map, saved here so it's always at hand even offline.</p>
  <div class="ev-link">
    <a class="pill pill-directions" href="standard-tube-map.pdf" target="_blank">&#128506;&#65039; CLICK HERE to view the Tube Map (PDF)</a>
  </div>
</section>

<section id="funfacts" class="print-block" data-section="funfacts">
  <div class="section-head-row">
    <h2>Fun Facts by Day</h2>
    <button class="print-btn no-print" onclick="printSection('funfacts')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">Extra fun facts for the places we're seeing each day &ndash; on top of the ones shown in each day's Fun Facts box on screen.</p>
  {FUN_FACTS_PAGE_HTML}
</section>

<section id="emergencycontacts" class="print-block" data-section="emergencycontacts">
  <div class="section-head-row">
    <h2>Emergency Contacts</h2>
    <button class="print-btn no-print" onclick="printSection('emergencycontacts')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">Emergency contacts back home for each couple, in case anyone needs to reach family while we're away.</p>
  <div class="ec-boxes">{EMERGENCY_CONTACTS_HTML}</div>
</section>

<section id="traveldocuments" class="print-block" data-section="traveldocuments">
  <div class="section-head-row">
    <h2>Travel Documents</h2>
    <button class="print-btn no-print" onclick="printSection('traveldocuments')"><span class="ic">&#128424;&#65039;</span>Print</button>
  </div>
  <p class="lede">Key trip documents, saved here so they're always at hand &ndash; open on screen or scan the QR code with your phone.</p>
  <div class="td-row">
    <a class="pill pill-weblink td-btn" href="fab4-travel-docs.pdf" target="_blank">Travel Docs</a>
    <img class="td-qr" src="data:image/png;base64,{TRAVEL_DOCS_QR_B64}" alt="QR code to Travel Docs">
  </div>
  <div class="td-row">
    <a class="pill pill-weblink td-btn" href="fab4-car-docs.pdf" target="_blank">Car Docs</a>
    <img class="td-qr" src="data:image/png;base64,{CAR_DOCS_QR_B64}" alt="QR code to Car Docs">
  </div>
  <div class="td-row">
    <a class="pill pill-weblink td-btn" href="fab4-eta-docs.pdf" target="_blank">ETA Confirmation (Gary)</a>
    <img class="td-qr" src="data:image/png;base64,{ETA_DOCS_QR_B64}" alt="QR code to ETA Confirmation">
  </div>
  <div class="td-row">
    <a class="pill pill-weblink td-btn" href="fab4-gk-travel-insurance.pdf" target="_blank">G&amp;K Travel Insurance</a>
    <img class="td-qr" src="data:image/png;base64,{INSURANCE_DOCS_QR_B64}" alt="QR code to G&amp;K Travel Insurance">
  </div>

  <details id="idpDetails" class="uketa-box">
    <summary class="uketa-summary"><span class="ic">&#128663;</span> International Driving Permit (IDP) Check</summary>
    <p class="tt-note">Whoever's driving in Italy needs a valid IDP alongside their normal licence. Tick boxes save in this browser only.</p>
    <table class="ntb">
      <tr><th>Name</th><th>Have IDP?</th><th>IDP Number</th></tr>
      {idp_html}
    </table>
  </details>
</section>

<footer class="no-print">
  Built from the Fab4takeoneurope itinerary workbook &middot; private &amp; for family use only
</footer>

<div class="japan-banner">
  <span class="jb-flag">&#127471;&#127477;</span>
  <p class="jb-text">BRING ON JAPAN 2027</p>
</div>

<script>
function printSection(id) {{
  document.body.className = 'printing-' + id;
  window.print();
}}
function printDay(id) {{
  document.body.className = 'printing-day-' + id;
  window.print();
}}
function printSub(id) {{
  document.body.className = 'printing-sub-' + id;
  window.print();
}}
function printAll() {{
  document.body.className = 'printing-all';
  window.print();
}}
function printBook() {{
  document.body.className = 'printing-book';
  window.print();
}}
window.addEventListener('afterprint', function() {{
  document.body.className = '';
}});
(function() {{
  var boxes = document.querySelectorAll('.tt-check');
  boxes.forEach(function(box) {{
    var key = 'fab4-packed-' + box.dataset.ttId;
    box.checked = localStorage.getItem(key) === '1';
    box.addEventListener('change', function() {{
      localStorage.setItem(key, box.checked ? '1' : '0');
    }});
  }});
}})();
function shareSite(e) {{
  if (e) e.preventDefault();
  var url = 'https://fab4-europe-trip.netlify.app/';
  var btn = document.getElementById('shareSiteBtn');
  if (navigator.share) {{
    navigator.share({{ title: 'The Fab 4 Take on Europe', text: 'Our September 2026 Europe trip itinerary', url: url }}).catch(function() {{}});
  }} else if (navigator.clipboard) {{
    navigator.clipboard.writeText(url).then(function() {{
      if (btn) {{
        var orig = btn.innerHTML;
        btn.innerHTML = '<span class="ic">&#9989;</span>Link copied!';
        setTimeout(function() {{ btn.innerHTML = orig; }}, 2000);
      }}
    }}).catch(function() {{ prompt('Copy this link to share:', url); }});
  }} else {{
    prompt('Copy this link to share:', url);
  }}
}}
function revealEtaChecklist() {{
  var d = document.getElementById('uketaDetails');
  if (d) {{
    d.open = true;
    setTimeout(function() {{ d.scrollIntoView({{behavior:'smooth', block:'center'}}); }}, 60);
  }}
}}
function joinNamesWithAnd(names) {{
  if (names.length === 0) return '';
  if (names.length === 1) return names[0];
  return names.slice(0, -1).join(', ') + ' and ' + names[names.length - 1];
}}
(function() {{
  var boxes = document.querySelectorAll('.eta-check');
  function updateEtaReminder() {{
    var banner = document.getElementById('etaReminder');
    var textEl = document.getElementById('etaReminderText');
    if (!banner || !boxes.length) return;
    var doneCount = 0;
    var remaining = [];
    boxes.forEach(function(b) {{
      if (b.checked) {{ doneCount++; }} else {{ remaining.push(b.dataset.firstName); }}
    }});
    if (doneCount < boxes.length) {{
      banner.style.display = 'flex';
      banner.classList.add('flashing');
      var base = "Reminder: Do our UK ETA's!";
      if (textEl) textEl.textContent = doneCount > 0
        ? base + ' Only ' + joinNamesWithAnd(remaining) + ' left to go'
        : base;
    }} else {{
      banner.style.display = 'none';
      banner.classList.remove('flashing');
    }}
  }}
  boxes.forEach(function(box) {{
    var key = 'fab4-eta-' + box.dataset.etaId;
    box.checked = localStorage.getItem(key) === '1';
    box.addEventListener('change', function() {{
      localStorage.setItem(key, box.checked ? '1' : '0');
      updateEtaReminder();
    }});
  }});
  updateEtaReminder();
}})();
function revealPassportChecklist() {{
  var d = document.getElementById('passportDetails');
  if (d) {{
    d.open = true;
    setTimeout(function() {{ d.scrollIntoView({{behavior:'smooth', block:'center'}}); }}, 60);
  }}
}}
(function() {{
  var boxes = document.querySelectorAll('.passport-check');
  function updatePassportReminder() {{
    var banner = document.getElementById('passportReminder');
    var textEl = document.getElementById('passportReminderText');
    if (!banner || !boxes.length) return;
    var doneCount = 0;
    var remaining = [];
    boxes.forEach(function(b) {{
      if (b.checked) {{ doneCount++; }} else {{ remaining.push(b.dataset.firstName); }}
    }});
    if (doneCount < boxes.length) {{
      banner.style.display = 'flex';
      banner.classList.add('flashing');
      var base = 'Reminder: Check our passports are valid!';
      if (textEl) textEl.textContent = doneCount > 0
        ? base + ' Only ' + joinNamesWithAnd(remaining) + ' left to go'
        : base;
    }} else {{
      banner.style.display = 'none';
      banner.classList.remove('flashing');
    }}
  }}
  boxes.forEach(function(box) {{
    var key = 'fab4-passport-' + box.dataset.passportId;
    box.checked = localStorage.getItem(key) === '1';
    box.addEventListener('change', function() {{
      localStorage.setItem(key, box.checked ? '1' : '0');
      updatePassportReminder();
    }});
  }});
  updatePassportReminder();
}})();
(function() {{
  var boxes = document.querySelectorAll('.idp-check');
  boxes.forEach(function(box) {{
    var key = 'fab4-idp-' + box.dataset.idpId;
    var stored = localStorage.getItem(key);
    if (stored !== null) {{ box.checked = stored === '1'; }}
    box.addEventListener('change', function() {{
      localStorage.setItem(key, box.checked ? '1' : '0');
    }});
  }});
}})();
(function() {{
  var el = document.getElementById('viewCounterNum');
  if (!el) return;
  fetch('https://countapi.mileshilliard.com/api/v1/hit/fab4-europe-trip-netlify-2026-siteviews')
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data && typeof data.value === 'number') {{
        el.textContent = (data.value + 99).toLocaleString();
      }}
    }})
    .catch(function() {{ /* offline or blocked - leave default 100 shown */ }});
}})();
function updateHeroClock() {{
  var el = document.getElementById('heroClock');
  if (!el) return;
  var now = new Date();
  var dateStr = now.toLocaleDateString(undefined, {{ weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }});
  var timeStr = now.toLocaleTimeString(undefined, {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }});
  el.textContent = dateStr + ' · ' + timeStr;
}}
updateHeroClock();
setInterval(updateHeroClock, 1000);
function toggleFunFacts() {{
  var hidden = document.body.classList.toggle('hide-facts');
  localStorage.setItem('fab4-hide-facts', hidden ? '1' : '0');
  var btn = document.getElementById('factsToggleBtn');
  if (btn) btn.innerHTML = hidden
    ? '<span class="ic">&#127881;</span>Show Fun Facts'
    : '<span class="ic">&#127881;</span>Hide Fun Facts';
}}
(function() {{
  if (localStorage.getItem('fab4-hide-facts') === '1') {{
    document.body.classList.add('hide-facts');
    var btn = document.getElementById('factsToggleBtn');
    if (btn) btn.innerHTML = '<span class="ic">&#127881;</span>Show Fun Facts';
  }}
}})();
var flipLastValues = {{}};
function setFlipDigit(unitName, value) {{
  var el = document.querySelector('.flip-digit[data-unit="' + unitName + '"]');
  if (!el) return;
  var text = value < 10 ? '0' + value : String(value);
  if (flipLastValues[unitName] === text) return;
  flipLastValues[unitName] = text;
  el.classList.add('flip-drop');
  setTimeout(function() {{
    el.textContent = text;
    el.classList.remove('flip-drop');
  }}, 180);
}}
function updateCountdown() {{
  var wrap = document.getElementById('heroCountdown');
  if (!wrap) return;
  var target = new Date('2026-09-10T14:45:00');
  var diff = target.getTime() - new Date().getTime();
  if (diff <= 0) {{
    wrap.innerHTML = '<div class="flip-label" style="font-size:1.1rem;color:#fff;">✈️ We\\'re off!</div>';
    return;
  }}
  var totalSeconds = Math.floor(diff / 1000);
  var days = Math.floor(totalSeconds / 86400);
  var hours = Math.floor((totalSeconds % 86400) / 3600);
  var minutes = Math.floor((totalSeconds % 3600) / 60);
  var seconds = totalSeconds % 60;
  setFlipDigit('days', days);
  setFlipDigit('hours', hours);
  setFlipDigit('minutes', minutes);
  setFlipDigit('seconds', seconds);
}}
updateCountdown();
setInterval(updateCountdown, 1000);
</script>

</body>
</html>
'''

with open('fab4_europe_site.html', 'w') as f:
    f.write(HTML)
print('Wrote fab4_europe_site.html', len(HTML), 'bytes')

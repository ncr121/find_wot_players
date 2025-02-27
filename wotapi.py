import json
import requests
import pandas as pd

app_id = '939a086f42896b0f8581ac8bd7f8be06'
app_url = '?application_id={}&'.format(app_id)

api_url = 'https://api.worldoftanks.eu/wot/'
acc_url = api_url + 'account/'


def load_json(url):
    return json.loads(requests.get(url).text)


def load_wot_json(url):
    return load_json(url).get('data', {})


def load_tank_info():
    url = api_url + 'encyclopedia/vehicles/' + app_url
    data = load_wot_json(url)
    return pd.DataFrame(data).T[['name', 'short_name', 'tier', 'nation', 'type', 'tag']]

def get_account_ids(names):
    url = acc_url + 'list/' + app_url + 'search={}&type=exact'.format('%2C'.join(names))
    data = load_wot_json(url)
    return dict(pd.DataFrame(data).values)


def get_account_data(ids):
    url = acc_url + 'info/' + app_url + 'account_id={}'.format('%2C'.join(map(str, ids)))
    data = load_wot_json(url)
    return {int(k): v for k, v in data.items() if v is not None}


def get_overall_stats(ids):
    return {k: v['statistics']['all'] for k, v in get_account_data(ids).items()}


def get_tank_stats(acc_id):
    url = api_url + 'tanks/stats/' + app_url + 'account_id={}'.format(acc_id)
    data = load_wot_json(url)[str(acc_id)]
    return {tank_data['tank_id']: tank_data['all'] for tank_data in data}

import shelve
import datetime as dt
import numpy as np
import pandas as pd
import xlwings as xw

import wotapi
import wn8
import tomato

zero_dt = dt.datetime(1970, 1, 1)


def get_ti(year, month, day, hour=0, minute=0, second=0):
    delta = dt.datetime(year, month, day, hour, minute, second) - zero_dt
    return 86400*delta.days + delta.seconds


def get_ti_from_dt(dt_=dt.datetime.now()):
    return get_ti(dt_.year, dt_.month, dt_.day, dt_.hour, dt_.minute, dt_.second)


def get_dt(ti):
    return zero_dt + dt.timedelta(seconds=ti)


def get_hundred_data(start_id):
    ids = start_id + np.arange(100)
    return wotapi.get_account_data(ids)


def satisfies_basic(data, last_ti):
    try:
        if data['clan_id'] is None and data['last_battle_time'] > last_ti:
            return True
        return False
    except TypeError:
        return False

def satisfies_overall(acc_id, data, now_ti, exp_df, reqs):
    overall = data['statistics']['all']
    ttl = overall['battles']
    return (ttl / ((now_ti - data['created_at']) / 86400) > reqs['battles_per_day']
            and wn8.approx_overall_wn8(acc_id, exp_df) > reqs['wn8']
            and overall['wins'] / ttl > reqs['wr'])


def find_players(db_file, excel_raw_file, last_ti, reqs, default='539604020'):
    now_ti = get_ti_from_dt()
    exp_df = wn8.load_expected_values()

    with shelve.open(db_file) as db:
        start_id = int(max(db, default=default)) + 1
        row = len(db) + 3

        wb = xw.Book(excel_raw_file)
        ws = wb.sheets[0]

        while True:
            print(start_id)

            for acc_id, data in get_hundred_data(start_id).items():
                if satisfies_basic(data, last_ti):
                    if satisfies_overall(acc_id, data, now_ti, exp_df, reqs):
                        df = tomato.get_table(data['nickname'], acc_id)
                        db[str(acc_id)] = df
                        ws[row, 0].value = data['nickname']
                        ws[row, 1].value = df.values
                        wb.save()
                        row += 1

            start_id += 100


def filter_by_recent(df_raw, reqs):
    df1 = df_raw['30 Days']
    return df_raw[(df1['Battles'] > reqs['battles']) & (df1['WN8'] > reqs['wn8']) & (df1['Wins'] > reqs['wr'])]


last_ti = get_ti(2024, 12, 1)
overall_reqs = {'battles_per_day': 3, 'wn8': 2000, 'wr': 0.52}
recent_reqs = {'battles': 300, 'wn8': 2500, 'wr': 0.55}

db_file = 'tomato_db'
excel_raw_file = 'tomato_stats_raw.xlsx'
excel_file = 'tomato_stats.xlsx'

df_raw = pd.read_excel(excel_raw_file, header=[0, 1], index_col=0)
df = filter_by_recent(df_raw, recent_reqs)
wn8.add_colour(excel_file, df)
find_players(db_file, excel_raw_file, last_ti, overall_reqs)

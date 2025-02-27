import requests
import time
import pandas as pd
from bs4 import BeautifulSoup

row_labels = {'Battles': 1, 'Avg Tier': 1, 'WN8': 1, 'Wins': 3, 'Survived': 3, 'Damage': 2, 'Damage Ratio': 1,
              'Frags': 2, 'K/D Ratio': 1}
col_labels = ['Overall', '1 Day', '3 Days', '7 Days', '30 Days', '60 Days', '1000 Battles']


def empty_table():
    return pd.DataFrame(None, row_labels, col_labels).astype(float)


def get_full_table(name, acc_id):
    df = empty_table()

    try:
        url = 'https://tomato.gg/stats/{}-{}/EU?tab=main'.format(name, acc_id)
        response = requests.get(url).text
        time.sleep(1)
        soup = BeautifulSoup(response, 'html.parser')
        text = soup.get_text('%2C').split('%2C')

        idxs = [text.index(label) for label in row_labels]
        idxs.append(idxs[-1] + text[idxs[-1]:].index('Tanks'))

        for i in range(df.shape[0]):
            row = text[idxs[i]+1:idxs[i+1]]
            m = row_labels[df.index[i]]
            n = 0

            for j in range(df.shape[1]):
                if row[n] != '-':
                    if m == 1:
                        df.iloc[i, j] = float(row[n])
                    elif m == 2:
                        df.iloc[i, j] = float(row[n+1])
                    else:
                        df.iloc[i, j] = round(float(row[n+1])/100, 4)
                    n += m
                else:
                    n += 1
    except:
        pass

    return df


def get_table(name, acc_id):
    df = get_full_table(name, acc_id).iloc[:4, [0, 4]]
    return pd.Series(df.T.values.reshape(-1), pd.MultiIndex.from_product([df.columns, df.index])).rename(name)

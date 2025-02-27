import numpy as np
import pandas as pd
import xlwings as xw

import wotapi

wn8_borders = [300, 450, 650, 900, 1200, 1600, 2000, 2450, 2900]
wr_borders = [0.46, 0.47, 0.48, 0.5, 0.52, 0.54, 0.56, 0.6, 0.65]
colours = [(204, 0, 0), (255, 0, 0), (255, 153, 0), (255, 255, 102), (153, 204, 0),
           (0, 128, 0), (51, 204, 255), (0, 153, 255), (153, 0, 255), (102, 0, 204)]


def load_expected_values():
    url = 'https://static.modxvm.com/wn8-data-exp/json/wg/wn8exp.json'
    return pd.DataFrame(wotapi.load_json(url)['data']).set_index('IDNum')


def compute_tank_wn8(tank_id, data, exp_df):
    try:
        exp = exp_df.loc[tank_id]
    except KeyError:
        return

    ttl = data['battles']

    if ttl == 0:
        return 0, 0

    rDAMAGE = (data['damage_dealt'] / ttl) / exp['expDamage']
    rSPOT = (data['spotted'] / ttl) / exp['expSpot']
    rFRAG = (data['frags'] / ttl) / exp['expFrag']
    rDEF = (data['dropped_capture_points'] / ttl) / exp['expDef']
    rWIN = (data['wins'] / ttl) / (exp['expWinRate'] / 100)

    rDAMAGEc = max(0, (rDAMAGE - 0.22) / 0.78)
    rFRAGc = max(0, min(rDAMAGEc + 0.2, (rFRAG - 0.12) / 0.88))
    rSPOTc = max(0, min(rDAMAGEc + 0.1, (rSPOT - 0.38) / 0.62))
    rDEFc = max(0, min(rDAMAGEc + 0.1, (rDEF - 0.1) / 0.9))
    rWINc = max(0, (rWIN - 0.71) / 0.29)

    wn8 = 980*rDAMAGEc + 210*rDAMAGEc*rFRAGc + 155*rFRAGc*rSPOTc + 75*rDEFc*rFRAGc + 145*min(1.8, rWINc)

    return ttl, wn8


def approx_overall_wn8(acc_id, exp_df):
    try:
        data = wotapi.get_tank_stats(acc_id)
        tank_wn8 = [compute_tank_wn8(*tank_data, exp_df) for tank_data in data.items()]
        weights, values = pd.DataFrame(tank_wn8).dropna().T.values
        return np.dot(weights, values) / weights.sum()
    except:
        return 0


def get_colour(value, borders):
    for upper_bound, colour in zip(borders, colours):
        if value < upper_bound:
            return colour
    return colours[-1]


def get_wn8_colour(wn8):
    return get_colour(wn8, wn8_borders)


def get_wr_colour(wr):
    return get_colour(wr, wr_borders)


def add_colour(excel_file, df):
    with pd.ExcelWriter(excel_file) as writer:
        df.to_excel(writer)

    wb = xw.Book(excel_file)
    ws = wb.sheets[0]
    ws.autofit()

    for j in range(1, df.shape[1]):
        ws[0, j].column_width = 8.09

    for j in (3, 7):
        for cell in ws[3, j].expand('down'):
            cell.color = get_wn8_colour(cell.value)

    for j in (4, 8):
        for cell in ws[3, j].expand('down'):
            cell.color = get_wr_colour(cell.value)
            cell.number_format = '0.00%'

    wb.save()

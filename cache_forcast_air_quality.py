# -*- coding: utf-8 -*-
import json
import logging
import calendar
import datetime

import requests
import sqlite3

from cwb_auth_key import AUTH_KEY
from constants import EPA_AQFN_URL, CWB_DB_PATH
from dataset_ids import dataset_ids_level_3
from time_util import timestr2ts

logging.basicConfig(level=logging.DEBUG)

def check_or_create_table_level_1_2():
    '''第一、二級行政區'''
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS {} (end_ts int, location text, Wx int, MaxT int, MinT int, PoP int, CI text, PRIMARY KEY (end_ts, location))'''.format('level_1_2'))
    conn.commit()
    conn.close()

def insert_data_level_1_2(dict_data):
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    for loc in dict_data:
        for time in dict_data[loc]:
            Wx = dict_data[loc][time]['Wx']
            MaxT = dict_data[loc][time]['MaxT']
            MinT = dict_data[loc][time]['MinT']
            PoP = dict_data[loc][time]['PoP']
            CI = dict_data[loc][time]['CI']
            insert_sql = "INSERT OR REPLACE INTO {} VALUES ({}, \'{}\', {}, {}, {}, {}, \'{}\')".format('level_1_2', time, loc.encode('utf-8'), Wx, MaxT, MinT, PoP, CI.encode('utf-8'))
            logging.debug(insert_sql)
            c.execute(insert_sql)
    conn.commit()
    conn.close()


def get_data_from_EPA():
    '''limit, offset, format, locationName, elementName, sort'''
    logging.info('getting data from EPA...')

    r = requests.get(EPA_AQFN_URL)
    
    if r.status_code != 200:
        logging.error('r.status_code: {}'.format(r.status_code))
        return None

    data = r.json()
    if data.get('success') != True:
        logging.error('success != True')
        return None
    return data['result']['records']

def simplify_data(records):
    ''' drop unused data '''
    for r in records:
        r.pop('Content')
        r['Area']  # "北部"
        r['MajorPollutant']  # "細懸浮微粒
        r['AQI'] = int(r['AQI'])  # "150"
        r['ForecastDate'] = timestr2ts(r['ForecastDate'], 8)  # "2017-04-07"
        r.pop('MinorPollutant')  # ""
        r.pop('MinorPollutantAQI')  # ""
        r['PublishTime'] = timestr2ts(r['PublishTime'], 8)  #"2017-04-07 12:00"
        print r

            
if __name__ == '__main__':
    dict_data = get_data_from_EPA()
    data = simplify_data(dict_data)
    # check_or_create_table_level_1_2()
    # insert_data_level_1_2(dict_data)


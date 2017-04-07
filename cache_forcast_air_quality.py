# -*- coding: utf-8 -*-
import json
import logging
import calendar
import datetime

import requests
import sqlite3

from constants import EPA_AQFN_URL, CWB_DB_PATH, TABLE_AQI
from time_utils import timestr2ts

logging.basicConfig(level=logging.DEBUG)

def check_or_create_table_AQI():
    '''AQI forecast database'''
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS {} (publish_ts int, forecast_ts int, area text, major_pollutant text, AQI int, PRIMARY KEY (publish_ts, forecast_ts, area))'''.format(TABLE_AQI))
    conn.commit()
    conn.close()

def insert_data_table_AQI(data):
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    for r in data:
        insert_sql = "INSERT OR REPLACE INTO {} VALUES ({}, {}, \'{}\', \'{}\', {})".format(TABLE_AQI, r['publish_ts'], r['forecast_ts'], r['area'].encode('utf-8'), r['major_pollutant'].encode('utf-8'), r['AQI'])
        logging.debug(insert_sql)
        c.execute(insert_sql)
    conn.commit()
    conn.close()


def get_data_from_EPA():
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
        r['area'] = r.pop('Area')  # "北部"
        r['major_pollutant'] = r.pop('MajorPollutant')  # "細懸浮微粒
        r['AQI'] = int(r['AQI'])  # "150"
        r['forecast_ts'] = timestr2ts(r['ForecastDate'], 8)  # "2017-04-07"
        r.pop('MinorPollutant')  # ""
        r.pop('MinorPollutantAQI')  # ""
        r['publish_ts'] = timestr2ts(r['PublishTime'], 8)  #"2017-04-07 12:00"
        print r

            
if __name__ == '__main__':
    data = get_data_from_EPA()
    simplify_data(data)
    check_or_create_table_AQI()
    insert_data_table_AQI(data)


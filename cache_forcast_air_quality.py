# -*- coding: utf-8 -*-
import json
import logging
import calendar
import datetime

import requests
import sqlite3

from constants import EPA_AQFN_URL, EPA_AQI_URL, CWB_DB_PATH, TABLE_AQFN, TABLE_AQI
from time_utils import timestr2ts

logging.basicConfig(level=logging.DEBUG)

def check_or_create_table_AQFN():
    '''AQI forecast database'''
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS {} (publish_ts int, forecast_ts int, area text, major_pollutant text, AQI int, PRIMARY KEY (publish_ts, forecast_ts, area))'''.format(TABLE_AQFN))
    conn.commit()
    conn.close()


def insert_data_table_AQFN(data):
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    for r in data:
        insert_sql = "INSERT OR REPLACE INTO {} VALUES ({}, {}, \'{}\', \'{}\', {})".format(TABLE_AQFN, r['publish_ts'], r['forecast_ts'], r['area'].encode('utf-8'), r['major_pollutant'].encode('utf-8'), r['AQI'])
        logging.debug(insert_sql)
        c.execute(insert_sql)
    conn.commit()
    conn.close()


def check_or_create_table_AQI():
    '''AQI forecast database'''
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS {} (county text, site_name text, publish_ts int, AQI int, pollutant text, status text, PM10 int, PM25 int, PRIMARY KEY (county, site_name, publish_ts))'''.format(TABLE_AQI))
    conn.commit()
    conn.close()


def insert_data_table_AQI(data):
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    for r in data:
        logging.debug('start')
        logging.debug(r)
        logging.debug('end')
        insert_sql = "INSERT OR REPLACE INTO {} VALUES (\'{county}\', \'{site_name}\', {publish_ts}, {AQI}, \'{pollutant}\', \'{status}\', {PM10}, {PM25})".format(
            TABLE_AQI,
            county=r['county'].encode('utf-8'),
            site_name=r['site_name'].encode('utf-8'),
            publish_ts=r['publish_ts'],
            AQI=r['AQI'],
            pollutant=r['pollutant'].encode('utf-8'),
            status=r['status'].encode('utf-8'),
            PM10=r['PM10'],
            PM25=r['PM2.5'],
        )
        logging.debug(insert_sql)
        c.execute(insert_sql)
    conn.commit()
    conn.close()


def get_data_from_EPA(url):
    logging.info('getting data from EPA...')

    r = requests.get(url)
    
    if r.status_code != 200:
        logging.error('r.status_code: {}'.format(r.status_code))
        return None

    data = r.json()
    if data.get('success') != True:
        logging.error('success != True')
        return None
    return data['result']['records']

def simplify_aqfn(records):
    ''' drop unused data '''
    for r in records:
        r.pop('Content')
        r['area'] = r.pop('Area')  # "北部"
        r['major_pollutant'] = r.pop('MajorPollutant')  # "細懸浮微粒
        r['AQI'] = int(r['AQI'])  # "150"
        r['forecast_ts'] = timestr2ts(r['ForecastDate'], 8)  # "2017-04-07"
        r.pop('MinorPollutant')  # ""
        r.pop('MinorPollutantAQI')  # ""
        r['publish_ts'] = timestr2ts(r['PublishTime'], 8)  # "2017-04-07 12:00"
        print r


def simplify_aqi(records):
    ''' drop unused data '''
    data = []
    for r in records:
        if r['AQI'] == '':
            continue
        if r['PM10'] == '' or r['PM10'] == 'ND':
            continue
        if r['PM2.5'] == '' or r['PM2.5'] == 'ND':
            continue
        t = {}
        t['county'] = r.pop('County')  # "彰化縣
        t['site_name'] = r.pop('SiteName')  # "二林"
        t['publish_ts'] = timestr2ts(r['PublishTime'], 8)  # "2017-04-07 12:00"
        t['AQI'] = int(r['AQI'])  # "150"
        t['pollutant'] = r.pop('Pollutant')  # "細懸浮微粒"
        t['status'] = r.pop('Status')  # "普通"
        t['PM10'] = int(r.pop('PM10'))  # 45
        t['PM2.5'] = int(r.pop('PM2.5'))  # 16
        print t
        data.append(t)
    return data

            
if __name__ == '__main__':
    data = get_data_from_EPA(EPA_AQFN_URL)
    simplify_aqfn(data)
    check_or_create_table_AQFN()
    insert_data_table_AQFN(data)

    data = get_data_from_EPA(EPA_AQI_URL)
    data = simplify_aqi(data)
    check_or_create_table_AQI()
    insert_data_table_AQI(data)

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

logging.basicConfig(level=logging.DEBUG)

def check_or_create_table_level_1_2():
    '''第一、二級行政區'''
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS {} (end_ts int, location text, Wx int, MaxT int, MinT int, PoP int, CI text, PRIMARY KEY (end_ts, location))'''.format('level_1_2'))
    conn.commit()
    conn.close()

def check_or_create_table_level_3():
    '''第三級行政區'''
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS {} (start_ts int, end_ts int, location text, sub_location text, Wx int, T int, AT int, PoP int, CI text, PRIMARY KEY (start_ts, end_ts, location, sub_location))'''.format('level_3'))
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

def process_data(records):
    print(len(records))
    for r in records:
        r.pop('Content')
        r['Area']  # "北部"
        r['MajorPollutant']  # "細懸浮微粒
        r['AQI']  # "150"
        r['ForecastDate']  # "2017-04-07"
        r['MinorPollutant']  # ""
        r['MinorPollutantAQI']  # ""
        r['PublishTime']  #"2017-04-07 12:00" 

def parse_json_to_dict_level_1_2(data):
    logging.info('parsing {} ...'.format(data['records']['datasetDescription'].encode('utf-8')))
    output = {}
    locations = data['records']['location']
    for l in locations:
        location_name = l['locationName']
        output[location_name] = {}
        factors = l['weatherElement']
        for f in factors:
            factor_name = f['elementName']
            periods = f['time']
            for p in periods:
                # start_time_ts = calendar.timegm(datetime.datetime.strptime(p['startTime'], '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                end_time_ts = calendar.timegm(datetime.datetime.strptime(p['endTime'], '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                # time_key = str(start_time_ts) + ',' + str(end_time_ts)
                time_key = end_time_ts
                if time_key not in output[location_name]:
                    output[location_name][time_key] = {}
                forecast_status = p['parameter']['parameterName']
                if factor_name == 'Wx':
                    forecast_value = p['parameter']['parameterValue']
                    output[location_name][time_key][factor_name] = int(forecast_value)
                elif factor_name in ['MaxT', 'MinT', 'PoP']:
                    forecast_status = int(forecast_status)
                    output[location_name][time_key][factor_name] = forecast_status
                elif factor_name == 'CI':
                    output[location_name][time_key][factor_name] = forecast_status
    return output

            
if __name__ == '__main__':
    dict_data = get_data_from_EPA()
    data = process_data(dict_data)
    # dict_data = parse_json_to_dict_level_1_2(json_data)
    # check_or_create_table_level_1_2()
    # insert_data_level_1_2(dict_data)


# -*- coding: utf-8 -*-
import json
import logging
import calendar
import datetime

import requests
import sqlite3

from cwb_auth_key import AUTH_KEY
from constants import CWB_URL, CWB_DB_PATH

logging.basicConfig(level=logging.DEBUG)

def check_or_create_sqlite_table():
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS {} (end_ts int, location text, Wx int, MaxT int, MinT int, PoP int, CI text, PRIMARY KEY (end_ts, location))'''.format('forecast_36hr'))
    conn.commit()
    conn.close()

def insert_data(dict_data):
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    for loc in dict_data:
        for time in dict_data[loc]:
            Wx = dict_data[loc][time]['Wx']
            MaxT = dict_data[loc][time]['MaxT']
            MinT = dict_data[loc][time]['MinT']
            PoP = dict_data[loc][time]['PoP']
            CI = dict_data[loc][time]['CI']
            insert_sql = "INSERT OR REPLACE INTO {} VALUES ({}, \'{}\', {}, {}, {}, {}, \'{}\')".format('forecast_36hr', time, loc.encode('utf-8'), Wx, MaxT, MinT, PoP, CI.encode('utf-8'))
            logging.debug(insert_sql)
            c.execute(insert_sql)
    conn.commit()
    conn.close()

def get_data_from_cwb(data_id, auth_key, params={}):
    '''limit, offset, format, locationName, elementName, sort'''
    logging.info('getting data from CWB...')

    dest_url = CWB_URL + '{}'.format(data_id)
    r = requests.get(dest_url, headers={'Authorization': auth_key})
    params_list = ['{}={}'.format(key, params[key]) for key in params]
    params_str = '?' + '&'.join(params_list)
    dest_url += params_str
    logging.debug('dest_url: {}'.format(dest_url))
    
    if r.status_code != 200:
        logging.error('r.status_code: {}'.format(r.status_code))
        return None

    data = r.json()
    
    if data.get('success') != 'true':
        return None
    return data

def parse_json_to_dict(data):
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

def dump_dict_to_json_file(dict_data, filename):
    logging.info('dump to json file...')
    with open(filename, 'w') as fp:
        json.dump(dict_data, fp)

if __name__ == '__main__':
    json_data = get_data_from_cwb('F-C0032-001', AUTH_KEY, {'locationName': '臺北市', 'limit': 1})
    dict_data = parse_json_to_dict(json_data)
    # dump_dict_to_json_file(dict_data, 'output.json')
    check_or_create_sqlite_table()
    insert_data(dict_data)

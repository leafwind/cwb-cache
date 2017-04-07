# -*- coding: utf-8 -*-
import json
import logging
import calendar
import datetime

import requests
import sqlite3

from cwb_auth_key import AUTH_KEY
from constants import CWB_URL, CWB_DB_PATH, TABLE_WEATHER_LEVEL_1_2
from dataset_ids import dataset_ids_level_3

logging.basicConfig(level=logging.DEBUG)

def check_or_create_table_level_1_2():
    '''第一、二級行政區'''
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS {} (end_ts int, location text, Wx int, MaxT int, MinT int, PoP int, CI text, PRIMARY KEY (end_ts, location))'''.format(TABLE_WEATHER_LEVEL_1_2))
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
            insert_sql = "INSERT OR REPLACE INTO {} VALUES ({}, \'{}\', {}, {}, {}, {}, \'{}\')".format(TABLE_WEATHER_LEVEL_1_2, time, loc.encode('utf-8'), Wx, MaxT, MinT, PoP, CI.encode('utf-8'))
            logging.debug(insert_sql)
            c.execute(insert_sql)
    conn.commit()
    conn.close()

def insert_data_level_3(dict_data):
    conn = sqlite3.connect(CWB_DB_PATH)
    c = conn.cursor()
    for key in dict_data:
        (location_name, sub_location_name, start_time_ts, end_time_ts) = key
        Wx = dict_data[key]['Wx']
        T = dict_data[key]['T']
        AT = dict_data[key]['AT']
        PoP = 0
        CI = ''
        insert_sql = "INSERT OR REPLACE INTO {} VALUES ({}, {}, \'{}\', \'{}\', {}, {}, {}, {}, \'{}\')".format('level_3', start_time_ts, end_time_ts, location_name.encode('utf-8'), sub_location_name.encode('utf-8'), Wx, T, AT, PoP, CI)
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

def parse_json_to_dict_level_3(data):
    logging.info('parsing {} ...'.format(data['records']['contentDescription'].encode('utf-8')))
    output = {}
    locations = data['records']['locations']
    for l in locations:
        location_name = l['locationsName']
        datasetDescription = l['datasetDescription'].encode('utf-8')
        sub_locations = l['location']
        for sl in sub_locations:
            sub_location_name = sl['locationName']
            geocode = sl['geocode']
            lat = sl['lat']
            lon = sl['lon']
            factors = sl['weatherElement']
            for f in factors:
                factor_name = f['elementName']
                periods = f['time']
                for p in periods:
                    if factor_name in ['Wx']:  # ['PoP', 'WeatherDescription', 'PoP6h']
                        start_time = p['startTime']
                        end_time = p['endTime']
                        start_time_ts = calendar.timegm(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                        end_time_ts = calendar.timegm(datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                        value = p['parameter'][0]['parameterValue']
                    elif factor_name in ['AT', 'T']:  # ['RH', 'CI', 'Td']
                        start_time = p['dataTime']
                        start_time_ts = calendar.timegm(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                        end_time_ts = start_time_ts + 3 * 3600
                        value = p['elementValue']
                    else:
#                         p['elementValue']
#                         elif factor_name in ['Wind']
#                         p['dataTime']
#                         p['parameter']
                        continue
                    key = (location_name, sub_location_name, start_time_ts, end_time_ts)
                    if key not in output:
                        output[key] = {}
                    output[key][factor_name] = value
    return output
            
def dump_dict_to_json_file(dict_data, filename):
    logging.info('dump to json file...')
    with open(filename, 'w') as fp:
        json.dump(dict_data, fp)

if __name__ == '__main__':
    # TODO: use F-D0047-089
    json_data = get_data_from_cwb('F-C0032-001', AUTH_KEY, {})
    dict_data = parse_json_to_dict_level_1_2(json_data)
    # dump_dict_to_json_file(dict_data, 'output.json')
    check_or_create_table_level_1_2()
    insert_data_level_1_2(dict_data)

    check_or_create_table_level_3()
    for dataset_id in dataset_ids_level_3:
        json_data = get_data_from_cwb(dataset_id, AUTH_KEY, {})
        dict_data = parse_json_to_dict_level_3(json_data)
        # print(dict_data)
        insert_data_level_3(dict_data)

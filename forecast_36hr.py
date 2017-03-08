# -*- coding: utf-8 -*-
import json
import logging
import calendar
import datetime

import requests
import sqlite3

from cwb_auth_key import AUTH_KEY
from constants import CWB_URL
from predict_code_map import PREDICT_CODE_MAP

logging.basicConfig(level=logging.DEBUG)

def get_data():
    logging.info('getting data from CWB...')
    #'{dataid}?limit={limit}&offset={offset}&format={format}&locationName={locationName}&elementName={elementName}&sort={sort}'
    r = requests.get(CWB_URL + '{}'.format('F-C0032-001'), headers={'Authorization': AUTH_KEY})
    
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
                start_time_ts = calendar.timegm(datetime.datetime.strptime(p['startTime'], '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                end_time_ts = calendar.timegm(datetime.datetime.strptime(p['endTime'], '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                time_key = str(start_time_ts) + ',' + str(end_time_ts)
                if time_key not in output[location_name]:
                    output[location_name][time_key] = {}
                forecast_status = p['parameter']['parameterName']
                if factor_name == 'Wx':
                    forecast_value = p['parameter']['parameterValue']
                    output[location_name][time_key][factor_name] = PREDICT_CODE_MAP[int(forecast_value)]
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
    json_data = get_data()
    dict_data = parse_json_to_dict(json_data)
    dump_dict_to_json_file(dict_data, 'output.json')

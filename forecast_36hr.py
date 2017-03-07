# -*- coding: utf-8 -*-
import requests
import json
import logging
import calendar
import datetime

from cwb_auth_key import AUTH_KEY
from constants import CWB_URL

def get_data():
    #'{dataid}?limit={limit}&offset={offset}&format={format}&locationName={locationName}&elementName={elementName}&sort={sort}'
    
    r = requests.get(CWB_URL + '{}'.format('F-C0032-001'), headers={'Authorization': AUTH_KEY})
    
    if r.status_code != 200:
        logging.error('r.status_code: {}'.format(r.status_code))
        return False
    data = r.json()
    
    if data.get('success') != 'true':
        return False
    
    output = {}
    # data['records']['datasetDescription']
    locations = data['records']['location']
    for l in locations:
        location_name = l['locationName']
        output[location_name] = {}
        factors = l['weatherElement']
        for f in factors:
            factor_name = f['elementName']
            # output[location_name][factor_name] = []
            periods = f['time']
            for p in periods:
                start_time_ts = calendar.timegm(datetime.datetime.strptime(p['startTime'], '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                end_time_ts = calendar.timegm(datetime.datetime.strptime(p['endTime'], '%Y-%m-%d %H:%M:%S').timetuple()) - 8 * 3600
                time_key = str(start_time_ts) + ',' + str(end_time_ts)
                if time_key not in output[location_name]:
                    output[location_name][time_key] = {}
                forecast_status = p['parameter']['parameterName']
                if factor_name not in ['CI', 'Wx']:
                    forecast_status = int(forecast_status)
                elif factor_name == 'Wx':
                    forecast_value = p['parameter']['parameterValue']
                    output[location_name][time_key]['Wx_value'] = int(forecast_value)
                output[location_name][time_key][factor_name] = forecast_status

    with open('forecast_36hr.json', 'w') as fp:
        json.dump(output, fp)

if __name__ == '__main__':
    get_data()

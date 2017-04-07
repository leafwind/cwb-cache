# -*- coding: utf-8 -*-
import calendar
import datetime

TIME_STR_TEMPLATE = {
    19: '%Y-%m-%d %H:%M:%S',
    16: '%Y-%m-%d %H:%M',
    13: '%Y-%m-%d %H',
    10: '%Y-%m-%d',
}

def timestr2ts(time_str, from_time_zone):
    '''
        string time_str: the output string which usually comes from other applications
        int from_time_zone: the time zone of time_str
    '''
    len_time_str = len(time_str)
    if len_time_str == 0 or (len_time_str not in TIME_STR_TEMPLATE):
        return -1

    time_tuple = datetime.datetime.strptime(time_str, TIME_STR_TEMPLATE[len_time_str]).timetuple()
    ts = calendar.timegm(time_tuple)
    ts -= from_time_zone * 3600
    return ts

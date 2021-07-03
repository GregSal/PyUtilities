'''Date Conversion Methods.
'''
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=logging-fstring-interpolation

import re
from itertools import chain
from typing import Dict, List


# Day and Monthe Text in English
MONTHS = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
          'JUL': 7, 'AUG': 9, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
DAYS = ('SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT')


def build_date_re(compile_re=True, include_time=True):
    '''Compile a regular expression for parsing a date_string.
    Combines patterns for Date and Time.
    Allows for the following date and time formats
    Short date
        yyyy-MM-dd
        dd/MM/yyyy
        dd/MM/yy
        d/M/yy
        yy-MM-dd
        M/dd/yy
        dd-MMM-yy
        dd-MMM-yy
    Long date
        MMMM d, yyyy
        dddd, MMMM dd, yyyy
        MMMM-dd-yy
        d-MMM-yy
    Long time
        h:mm:ss tt
        hh:mm:ss tt
        HH:mm:ss
        H:mm:ss
    Short Time
        h:mm tt
        hh:mm tt
        HH:mm tt
        H:mm
    '''
    date_pattern = (
        '(?P<date1>'       # beginning of date1 string group
        '[a-zA-Z0-9]+'     # Month Day or year as a number or text
        ')'                # end of date1 string group
        '(?P<delimeter1>'  # beginning of delimeter1 string group
        '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
        ')'                # end of delimeter1 string group
        '(?P<date2>'       # beginning of date2 string group
        '[a-zA-Z0-9]+'     # Month Day or year as a number or text
        ')'                # end of date2 string group
        '(?P<delimeter2>'  # beginning of delimeter2 string group
        '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
        ')'                # end of delimeter2 string group
        '(?P<date3>'       # beginning of date3 string group
        '\d{2,4}'          # day or year as a number
        ')'                # end of date3 string group
        '(?P<date4>'       # beginning of possible date4 string group
        '((?<=, )\d{2,4})?'# Additional year section if date1 is the day name
        ')'                # end of date4 string group
        )
    time_pattern = (
        '\s+'              # gap between date and time
        '(?P<time>'        # beginning of time string group
        '\d{1,2}'          # Hour as 1 or 2 digits
        ':'                # Time delimiter
        '\d{1,2}'          # Minutes as 1 or 2 digits
        ':?'               # Time delimiter
        '\d{0,2}'          # Seconds (optional) as 0,  1 or 2 digits
        ')'                # end of time string group
        )
    am_pm_pattern = (
        '\s?'              # possible space separating time from AM/PM indicator
        '(?P<am_pm>'       # beginning of possible AM/PM (group)
        '[aApP][mM]'       # am or pm in upper or lower case
        ')?'               # end of am/pm string group
        '\s?'              # possible space after the date and time ends
        )
    if include_time:
        full_pattern = ''.join([date_pattern, time_pattern, am_pm_pattern])
    else:
        full_pattern = date_pattern
    if compile_re:
        return re.compile(full_pattern)
    return full_pattern

def make_date_time_string(date_match: re.match,
                          include_time: bool = True)->str:
    '''Extract date and time strings.
    Combine time and am/pm strings.
    '''
    if date_match:
        date_match_groups = date_match.groups(default='')
        if include_time:
            date_parameters = [
                date_part for date_part in chain(
                    date_match_groups[0:6],
                    [' '],
                    date_match_groups[6:8]
                    )
                ]
        else:
            date_parameters = date_match_groups[0:6]
        date_string = ''.join(date_parameters)
    else:
        date_string = ''
    return date_string


def get_date_time(date_match: re.match):
    '''Extract date and time strings.
    Combine time and am/pm strings.
    '''
    #if date_match:
    #    date_parameters = date_match.groupdict()

    #else:
    #    return None
    #date_str = date_parameters['date'].strip()
    #time_str = date_parameters['time'].strip()
    #am_pm_str = date_parameters['am_pm']
    #if am_pm_str:
    #    time_str += ' '
    #    time_str += am_pm_str.strip()
    raise NotImplementedError('get_date_time is not yet implemented')



class DateString(object):
    '''Parsing results for a string containing a date and time.
    Attributes:
        raw_text (str): The unprocessed input string
        is_datetime (bool): True is the input string contains a date and time.
        date (str): The date portion of the input string
        time (str): The time portion of the input string
    '''
    default_date_order = ('day', 'month', 'year')
    _date_re = build_date_re(compile_re=True, include_time=True)
    def __init__(self):
        #self.date = ''
        #self.time = ''
        #self.date_order = ('day', 'month', 'year')
        raise NotImplementedError('test_date_num is not implemented')

    def find_date_pattern(self, date_num_list: List[int],
                          num_type_list: List[str]) -> str:
        '''Iterate through date numbers to identify the date pattern if possible.
        continue until all '?' are replaced or until no more replacements cane be
        made.
        '''
        #done = False
        #while not done:  # FIXME  Iteration does not close
        #    if '?' not in num_type_list:
        #        done = True
        #    else:
        #        i = num_type_list.index('?')  # FIXME need to iterate here
        #        date_num = date_num_list[i]
        #        num_type = self.test_date_num(date_num, num_type_list)
        #        num_type_list[i] = num_type
        #return num_type_list
        raise NotImplementedError('test_date_num is not implemented')

    def test_date_num(self, date_num, num_type_list):
        raise NotImplementedError('test_date_num is not implemented')

    def build_date_string(self, date_parameters: Dict[str, str]):
        '''Extract date and time strings.
        Combine time and am/pm strings

        # TODO check each date group for string or number
        # TODO check strings for 1st 3 letters in months
        # TODO check numbers for valid day (1-31) month (1-12) year (0-9999)
        # TODO if order is apparent from text and numbers set default date order
        # TODO if not use default date order to assign values
        # TODO Build output date string
        '''
        #date_keys = [key for key in date_parameters.keys() if 'date' in key]
        #date_num_list = list()
        #num_type_list = list()
        #for key in date_keys:
        #    date_str = date_parameters['date1'].strip()
        #    try:
        #        date_num_list.append(int(date_str))
        #    except ValueError:
        #        month_num = MONTHS.get(date_str[0:2].lower())
        #        if month_num:
        #            date_num_list.append(month_num)
        #            num_type_list.append('month')
        #    else:
        #        num_type_list.append('?')
        raise NotImplementedError('test_date_num is not implemented')

    def get_date_time(self, date_parameters: Dict[str, str]):
        '''Extract date and time strings.
        Combine time and am/pm strings
        '''
        #date_str = date_parameters['date'].strip()
        #time_str = date_parameters['time'].strip()
        #am_pm_str = date_parameters['am_pm']
        #if am_pm_str:
        #    time_str += ' '
        #    time_str += am_pm_str.strip()
        #self.date = date_str
        #self.time = time_str
        raise NotImplementedError('test_date_num is not implemented')

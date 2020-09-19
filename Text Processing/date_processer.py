'''Date Conversion Methods.
'''
# pylint: disable=anomalous-backslash-in-string

import re
from typing import Union, Dict, List, TextIO


class DateString(object):
    '''Parsing results for a string containing a date and time.
    Attributes:
        raw_text (str): The unprocessed input string
        is_datetime (bool): True is the input string contains a date and time.
        date (str): The date portion of the input string
        time (str): The time portion of the input string
    '''
    default_date_order = ('day', 'month', 'year')
    months = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
              'JUL': 7, 'AUG': 9, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
    days = ('SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT')

    def build_date_re():
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
            '^'                # beginning of string
            '\s?'              # possible space before the date begins
            '(?P<date>'        # beginning of date string group
            '[a-zA-Z0-9]+'     # Month Day or year as a number or text
            '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
            '[a-zA-Z0-9]+'     # Month Day or year as a number or text
            '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
            '\d{2,4}'          # day or year as a number
            '((?<=, )\d{2,4})?'# Additional year section if the day name was included
            ')'                # end of date string group
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
            '$'                # end of string
            )
        return re.compile(date_pattern + time_pattern + am_pm_pattern)

    def build_section_date_re():
        # FIXME I Don't think this method is used for anything.
        date_section_pattern = (
            '^'                # beginning of string
            '\s?'              # possible space before the date begins
            '(?P<date1>'       # beginning of date1 string group
            '[a-zA-Z0-9]+'     # Month Day or year as a number or text
            ')'                # end of date1 string group
            '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
            '(?P<date2>'       # beginning of date2 string group
            '[a-zA-Z0-9]+'     # Month Day or year as a number or text
            ')'                # end of date2 string group
            '[\s,-/]{1,2}'     # Date delimiter one of '-' '/' or ', '
            '(?P<date3>'       # beginning of date3 string group
            '\d{2,4}'          # day or year as a number
            ')'                # end of date3 string group
            '(?P<date4>'       # beginning of possible date4 string group
            '((?<=, )\d{2,4})?'# Additional year section if the day name was included
            ')'                # end of date4 string group
            )
        time_section_pattern = (
            '\s+'              # gap between date and time
            '(?P<hour>'        # beginning of hour string group
            '\d{1,2}'          # Hour as 1 or 2 digits
            ')'                # end of hour string group
            ':'                # Time delimiter
            '(?P<minutes>'     # beginning of minutes string group
            '\d{1,2}'          # Minutes as 1 or 2 digits
            ')'                # end of minutes string group
            ':?'               # Time delimiter
            '(?P<seconds>'     # beginning of seconds string group
            '\d{0,2}'          # Seconds (optional) as 0,  1 or 2 digits
            ')'                # end of seconds string group
            )
        am_pm_pattern = (
            '\s?'              # possible space separating time from AM/PM indicator
            '(?P<am_pm>'       # beginning of possible AM/PM (group)
            '[aApP][mM]'       # am or pm in upper or lower case
            ')?'               # end of am/pm string group
            '\s?'              # possible space after the date and time ends
            '$'                # end of string
            )
        return re.compile(date_section_pattern + time_section_pattern +
                          am_pm_pattern)

    __date_re = build_date_re()
    __date_section_re = build_section_date_re()

    def __init__(self, line: str):
        '''Scan a string for date and time elements
        '''
        self.date_delimeter = '-'
        self.date_format = r'dd/mm/yy'
        self.raw_text = line
        self.is_datetime = False
        self.date = ''
        self.time = ''

        self.parse_date_string()

    def parse_date_string(self):
        '''Parse a single line to extract date parameters.
        '''
        found = self.__date_re.search(self.raw_text)
        if found:
            date_parameters = found.groupdict()
            self.get_date_time(date_parameters)
            self.is_datetime = True
        else:
            self.is_datetime = False

    def test_date_num(self, date_num: int, num_type: List[str]) -> str:
        '''Identify the date number if possible.
        Returns one of 'year', 'month', 'day' or '?'
        '''
        if date_num > 31:
            date_type = 'year'
        elif ('year' in num_type) and (date_num > 12):
            date_type = 'month'
        elif ('year' in num_type) and ('month' in num_type):
            date_type = 'day'
        else:
            date_type = '?'
        return date_type

    def find_date_pattern(self, date_num_list: List[int],
                          num_type_list: List[str]) -> str:
        '''Iterate through date numbers to identify the date pattern if possible.
        continue until all '?' are replaced or until no more replacements cane be
        made.
        '''
        done = False
        while not done:  # FIXME  Iteration does not close
            if '?' not in num_type_list:
                done = True
            else:
                i = num_type_list.index('?')  # FIXME need to iterate here
                date_num = date_num_list[i]
                num_type = self.test_date_num(date_num, num_type_list)
                num_type_list[i] = num_type
        return num_type_list

    def build_date_string(self, date_parameters: Dict[str, str]):
        '''Extract date and time strings.
        Combine time and am/pm strings
        '''
        # TODO check each date group for string or number
        # TODO check strings for 1st 3 letters in months
        # TODO check numbers for valid day (1-31) month (1-12) year (0-9999)
        # TODO if order is apparent from text and numbers set default date order
        # TODO if not use default date order to assign values
        # TODO Build output date string
        date_keys = [key for key in date_parameters.keys() if 'date' in key]
        date_num_list = list()
        num_type_list = list()
        for key in date_keys:
            date_str = date_parameters['date1'].strip()
            try:
                date_num_list.append(int(date_str))
            except ValueError:
                month_num = self.months.get(date_str[0:2].lower())
                if month_num:
                    date_num_list.append(month_num)
                    num_type_list.append('month')
            else:
                num_type_list.append('?')

    def get_date_time(self, date_parameters: Dict[str, str]):
        '''Extract date and time strings.
        Combine time and am/pm strings
        '''
        date_str = date_parameters['date'].strip()
        time_str = date_parameters['time'].strip()
        am_pm_str = date_parameters['am_pm']
        if am_pm_str:
            time_str += ' '
            time_str += am_pm_str.strip()
        self.date = date_str
        self.time = time_str



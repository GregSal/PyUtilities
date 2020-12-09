
#%% Imports
from pathlib import Path
from itertools import chain
from functools import partial
from pprint import pprint
from typing import List, Callable
import csv
import re

import pandas as pd

import logging_tools as lg
from file_utilities import clean_ascii_text

import Text_Processing as tp
from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorEOF
from buffered_iterator import BufferOverflowWarning


#%% Logging
logger = lg.config_logger(prefix='Temp3', level='INFO')


#%% Line Parsing Functions
# Date Rule
def make_date_parse_rule() -> tp.Rule:
    def date_parse(line: str, *args, **kwargs) -> tp.ParseResults:
        '''If Date,don't split beyond first :.'''
        parsed_line = line.split(':', maxsplit=1)
        return [parsed_line]

    date_trigger = tp.Trigger('Date', location='START',
                              name='Starts With Date')
    date_rule = tp.Rule(date_trigger, date_parse,
                        name='date_rule')
    return date_rule


# Approved Status
def make_approved_status_rule() -> tp.Rule:
    '''If Treatment Approved, Split "Plan Status" into 3 lines:
        Plan Status
        Approved on
        Approved by
        '''
    def approved_status_parse(line, sentinel, *args, **kwargs) -> tp.ParseResults:
        '''If Treatment Approved, Split "Plan Status" into 3 lines:

        Return three rows for a line containing "Treatment Approved"
            Prescribed dose [unit]: dose
        Gives:
            [['Plan Status', 'Treatment Approved'],
             ['Approved on', date],
             ['Approved by', person]
        '''
        idx1 = line.find(sentinel)
        idx2 = idx1 + len(sentinel)
        idx3 = line.find(' by')
        idx4 = idx3 + 4
        parsed_lines = [
            ['Plan Status', line[idx1:idx2]],
            ['Approved on', line[idx2+1:idx3]],
            ['Approved by', line[idx4:]]
            ]
        return parsed_lines

    approved_status_trigger = tp.Trigger('Treatment Approved',
                                         location='IN',
                                         name='Treatment Approved')
    approved_status_rule = tp.Rule(approved_status_trigger,
                                   approved_status_parse,
                                   name='approved_status_rule')
    return approved_status_rule


# Prescribed Dose Rule
def make_prescribed_dose_rule() -> tp.Rule:
    def parse_prescribed_dose(line, sentinel, *args, **kwargs) -> tp.ParseResults:
        '''Split "Prescribed dose [cGy]" into 2 lines.

        Return two rows for a line containing:
            Prescribed dose [unit]: dose
        Gives:
            [['Prescribed dose', 'dose'],
            ['Prescribed dose unit', 'unit']],
        The line:
            Prescribed dose [unit]: not defined
        Results in:
            [['Prescribed dose', '5000.0'],
             ['Prescribed dose unit', 'cGy']]
        '''
        match_results = sentinel.groupdict()
        if match_results['dose'] == 'not defined':
            match_results['dose'] = ''
            match_results['unit'] = ''

        parsed_lines = [
            ['Prescribed dose', match_results['dose']],
            ['Prescribed dose unit', match_results['unit']]
            ]
        return parsed_lines


    def make_prescribed_dose_trigger()->tp.Trigger:
        '''Create a trigger that checks for Prescribed Dose Line.

        Use regular expression to match:
            Prescribed dose [(unit)]: (dose)

        Returns:
            dose_trigger: A trigger that uses a regular expression to check for
            a Prescribed Dose Line.
        '''
        prescribed_dose_pattern = (
            r'^Prescribed dose\s*'  # Begins with Prescribed dose
            r'\['                   # Unit start delimiter
            r'(?P<unit>[A-Za-z]+)'  # unit group: text surrounded by []
            r'\]'                   # Unit end delimiter
            r'\s*:\s*'              # Dose delimiter with possible whitespace
            r'(?P<dose>[0-9.]+'     # dose group Number
            r'|not defined)'        #"not defined" alternative
            r'[\s\r\n]*'            # drop trailing whitespace
            r'$'                    # end of string
            )
        re_pattern = re.compile(prescribed_dose_pattern)
        dose_trigger = tp.Trigger(re_pattern, name='Prescribed Dose')
        return dose_trigger

    dose_rule = tp.Rule(make_prescribed_dose_trigger(),
                     parse_prescribed_dose,
                     name='prescribed_dose_rule')
    return dose_rule



#%% Section definition
default_parser = tp.define_csv_parser('dvh_info', delimiter=':',
                                      skipinitialspace=True)
dvh_info_reader = tp.SectionReader(
    preprocessing_methods=[clean_ascii_text],
    parsing_rules=[make_date_parse_rule()],
    default_parser=default_parser,
    post_processing_methods=[tp.trim_items, tp.drop_blanks,
                             tp.merge_continued_rows])

plan_info_reader = tp.SectionReader(
    preprocessing_methods=[clean_ascii_text],
    parsing_rules=[make_prescribed_dose_rule(),
                   make_approved_status_rule()],
    default_parser=default_parser,
    post_processing_methods=[tp.trim_items, tp.drop_blanks,
                             tp.convert_numbers]
    )

plan_info_start = tp.SectionBreak(
    name='Start of Plan Info',
    trigger=tp.Trigger(['Plan:', 'Plan sum:']),
    offset='Before'
    )

plan_info_end = tp.SectionBreak(
    name='End of Plan Info',
    trigger=tp.Trigger(['% for dose (%):']),
    offset='After'
    )

dvh_info_break = tp.SectionBoundaries(
    start_section=None,
    end_section=plan_info_start)

plan_info_break = tp.SectionBoundaries(
    start_section=plan_info_start,
    end_section=plan_info_end)

dvh_info_section = tp.Section(
    section_name='DVH Info',
    boundaries=dvh_info_break,
    reader=dvh_info_reader,
    aggregate=tp.to_dict)

plan_info_section = tp.Section(
    section_name='Plan Info',
    boundaries=plan_info_break,
    reader=plan_info_reader,
    aggregate=tp.to_dict)



#%% main
def main():

    # Test Text
    test_source = [
        'Patient Name         : ____, ____',
        'Patient ID           : 1234567',
        'Comment              : DVHs for multiple plans and plan sums',
        'Date                 : Friday, January 17, 2020 09:45:07',
        'Exported by          : gsal',
        'Type                 : Cumulative Dose Volume Histogram',
        ('Description          : The cumulative DVH displays the '
        'percentage (relative)'),
        ('                       or volume (absolute) of structures '
        'that receive a dose'),
        '                      equal to or greater than a given dose.',
        '',
        'Plan sum: Plan Sum',
        'Course: PLAN SUM',
        'Prescribed dose [cGy]: not defined',
        '% for dose (%): not defined',
        ''
        'Plan: PARR',
        'Course: C1',
        'Plan Status: Treatment Approved Thursday, January 02, '
        '2020 12:55:56 by gsal',
        'Prescribed dose [cGy]: 5000.0',
        '% for dose (%): 100.0',
        ''
        'Structure: PRV5 SpinalCanal',
        'Approval Status: Approved',
        'Plan: Plan Sum',
        'Course: PLAN SUM',
        'Volume [cm³]: 121.5',
        'Dose Cover.[%]: 100.0',
        'Sampling Cover.[%]: 100.1',
        'Min Dose [cGy]: 36.7',
        'Max Dose [cGy]: 3670.1',
        'Mean Dose [cGy]: 891.9',
        'Modal Dose [cGy]: 44.5',
        'Median Dose [cGy]: 863.2',
        'STD [cGy]: 621.9',
        'NDR: ',
        'Equiv. Sphere Diam. [cm]: 6.1',
        'Conformity Index: N/A',
        'Gradient Measure [cm]: N/A',
        ''
        'Dose [cGy] Ratio of Total Structure Volume [%]',
        '         0                       100',
        '         1                       100',
        '         2                       100',
        '         3                       100',
        '         4                       100',
        '         5                       100',
        '      3667              4.23876e-005',
        '      3668              2.87336e-005',
        '      3669              1.50797e-005',
        '      3670               1.4257e-006',
        '',
        'Structure: PTV 50',
        'Approval Status: Approved',
        'Plan: Plan Sum',
        'Course: PLAN SUM',
        'Volume [cm³]: 363.6',
        'Dose Cover.[%]: 100.0',
        'Sampling Cover.[%]: 100.0',
        'Min Dose [cGy]: 3985.9',
        'Max Dose [cGy]: 5442.0',
        'Mean Dose [cGy]: 5144.5',
        'Modal Dose [cGy]: 5177.3',
        'Median Dose [cGy]: 5166.9',
        'STD [cGy]: 131.9',
        'NDR: ',
        'Equiv. Sphere Diam. [cm]: 8.9',
        'Conformity Index: N/A',
        'Gradient Measure [cm]: N/A',
        '',
        'Dose [cGy] Ratio of Total Structure Volume [%]',
        '         0                       100',
        '         1                       100',
        '         2                       100',
        '         3                       100',
        '         4                       100',
        '         5                       100',
        '      5437               9.4777e-005',
        '      5438              6.35607e-005',
        '      5439              3.62425e-005',
        '      5440              1.82336e-005',
        '      5441              9.15003e-006',
        '      5442               6.6481e-008'
        ]


    # Context
    context = {
        'File Name': 'Test_DVH_Sections.txt',
        'File Path': Path.cwd() / 'Text Files' / 'Test_DVH_Sections.txt',
        'Line Count': 0
        }
    test_section = tp.Section(
        section_name='Plan Info',
        boundaries=plan_info_break,
        reader=plan_info_reader,
        aggregate=tp.to_dict)
    buffered_source = BufferedIterator(test_source)
    test_section.context = context
    skipped_lines = test_section.find_start(buffered_source)
    print('Skipped Lines')
    pprint(skipped_lines)
    print('Read lines\n\n')

    section_scan = test_section.boundaries.scan(
        'End', buffered_source, section_name='Plan Info', **context)
    read_lines = [row for row in test_section.catch_break(section_scan)]
    pprint(read_lines)
    source_iter = iter(buffered_source)
    print('\nNext Item:')
    print(source_iter.__next__())




if __name__ == '__main__':
    main()

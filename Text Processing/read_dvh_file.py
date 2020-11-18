'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string

#%% Imports
from pathlib import Path
from pprint import pprint
from functools import partial
from itertools import chain
from typing import List, Callable
import csv
import re
import logging_tools as lg
from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorEOF
from buffered_iterator import BufferOverflowWarning
import Text_Processing as tp
import pandas as pd
from file_utilities import clean_ascii_text

#%% Logging
logger = lg.config_logger(prefix='read_dvh.file', level='INFO')


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
    def parse_prescribed_dose(line, sentinel,
                              *args, **kwargs) -> tp.ParseResults:
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

        Use regular expresion to match:
            Prescribed dose [(unit)]: (dose)

        Returns:
            dose_trigger: A trigger that uses a regular expresion to check for
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

def make_default_csv_parser() -> Callable:
    default_csv = tp.define_csv_parser('dvh_info', delimiter=':',
                                       skipinitialspace=True)
    return default_csv
#%% Line Processing

def to_plan_info_dict(plan_info_dict_list):
    '''Combine Plan Info dictionaries into dictionary of dictionaries.
    '''
    output_dict = dict()
    for plan_info_dict in plan_info_dict_list:
        plan_name = plan_info_dict.get['Plan']
        if not plan_name:
            plan_name = plan_info_dict.get['Plan sum']
            plan_info_dict['Plan'] = plan_name
            if not plan_name:
                plan_name = 'Plan'
                plan_info_dict['Plan'] = plan_name
        output_dict[plan_name] = plan_info_dict
    return output_dict


#%% Reader definitions
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
structure_info_reader = tp.SectionReader(
    preprocessing_methods=[clean_ascii_text],
    parsing_rules=[],
    default_parser=default_parser,
    post_processing_methods=[tp.trim_items, tp.drop_blanks,
                             tp.convert_numbers]
    )
dvh_data_reader = tp.SectionReader(
    preprocessing_methods=[clean_ascii_text],
    default_parser=tp.define_fixed_width_parser(widths=10),
    post_processing_methods=[tp.trim_items, tp.drop_blanks]
    )

#%% SectionBreak definitions
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
structure_info_start = tp.SectionBreak(
    name='Start of Structure Info',
    trigger=tp.Trigger(['Structure:']),
    offset='Before'
    )
structure_info_end = tp.SectionBreak(
    name='End of Structure Info',
    trigger=tp.Trigger(['Gradient Measure']),
    offset='After'
    )

dvh_info_break = tp.SectionBoundaries(
    start_section=None,
    end_section=plan_info_start)
plan_info_break = tp.SectionBoundaries(
    start_section=plan_info_start,
    end_section=plan_info_end)
structure_info_break = tp.SectionBoundaries(
    start_section=structure_info_start,
    end_section=structure_info_end)
dvh_data_break = tp.SectionBoundaries(
    start_section=None,
    end_section=structure_info_start)

#%% Section definitions
dvh_info_section = tp.Section(
    section_name='DVH Info',
    boundaries=dvh_info_break,
    reader=dvh_info_reader,
    output_method=tp.to_dict)
plan_info_section = tp.Section(
    section_name='Plan Info',
    boundaries=plan_info_break,
    reader=plan_info_reader,
    output_method=tp.to_dict)
structure_info_section = tp.Section(
    section_name='Structure',
    boundaries=structure_info_break,
    reader=structure_info_reader,
    output_method=tp.to_dict)
dvh_data_section = tp.Section(
    section_name='DVH',
    boundaries=dvh_data_break,
    reader=dvh_data_reader,
    output_method=tp.to_dataframe)


def date_processing():
    pass
def number_processing():
    pass


#%% Main Iteration
def main():
    # Test File
    base_path = Path.cwd()

    #test_file = Path.cwd() / 'PlanSum vs Original.dvh'

    test_file_path = r'Text Files'
    test_file = base_path / test_file_path / 'PlanSum vs Original.dvh'

    # Call Primary routine
    context, section_lines = tp.file_reader(test_file)
    print('done')


if __name__ == '__main__':
    main()

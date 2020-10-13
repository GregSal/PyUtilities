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


#%% Section definitions
default_parser = tp.define_csv_parser('dvh_info', delimiter=':',
                                      skipinitialspace=True)
dvh_info_section = tp.SectionReader(
    section_name='DVH Info',
    preprocessing_methods=[clean_ascii_text],
    parsing_rules=[make_date_parse_rule()],
    default_parser=default_parser,
    post_processing_methods=[tp.trim_items, tp.drop_blanks,
                             tp.merge_continued_rows],
    output_method=tp.to_dict)
plan_info_section = tp.SectionReader(
    section_name='Plan Info',
    preprocessing_methods=[clean_ascii_text],
    parsing_rules=[make_prescribed_dose_rule(),
                   make_approved_status_rule()],
    default_parser=default_parser,
    post_processing_methods=[tp.trim_items, tp.drop_blanks,
                             tp.convert_numbers],
    output_method=tp.to_dict)
structure_info_section = tp.SectionReader(
    section_name='Structure',
    preprocessing_methods=[clean_ascii_text],
    parsing_rules=[],
    default_parser=default_parser,
    post_processing_methods=[tp.trim_items, tp.drop_blanks,
                             tp.convert_numbers],
    output_method=tp.to_dict)
dvh_info_section = tp.SectionReader(
    section_name='DVH',
    preprocessing_methods=[clean_ascii_text],
    parsing_rules=[],
    default_parser=tp.define_fixed_width_parser(widths=10),
    post_processing_methods=[tp.trim_items, tp.drop_blanks,
                             tp.merge_continued_rows],
    output_method=tp.to_dataframe)

#%% SectionBreak definitions
dvh_info_end = tp.SectionBreak(
    name='End of DVH Info',
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
    end_section=dvh_info_end)
plan_info_break = tp.SectionBoundaries(
    start_section=dvh_info_end,
    end_section=plan_info_end)
structure_info_break = tp.SectionBoundaries(
    start_section=structure_info_start,
    end_section=structure_info_end)



def file_reader(test_file):
    with open(test_file, newline='') as csvfile:
        raw_lines = BufferedIterator(csvfile)
        context = {
            'File Name': test_file.name,
            'File Path': test_file.parent,
            'Line Count': 0,
            'Source': raw_lines
            }
        context, section_lines = section_manager(context)
    return context, section_lines

def process_lines(section_lines):
    parsed_lines = BufferedIterator(section_lines)
    pass



def merge_rows(parsed_lines):
    for parsed_line in parsed_lines:
        if len(parsed_line) > 0:
            yield parsed_line

def drop_blanks(parsed_lines):
    for parsed_line in parsed_lines:
        if len(parsed_line) > 0:
            yield parsed_line


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
    context, section_lines = file_reader(test_file)
    print('done')


if __name__ == '__main__':
    main()

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
import pandas as pd
import xlwings as xw

import logging_tools as lg
from file_utilities import clean_ascii_text
from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorEOF
from buffered_iterator import BufferOverflowWarning
import Text_Processing as tp


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


def make_default_csv_parser() -> Callable:
    default_csv = tp.define_csv_parser('dvh_info', delimiter=':',
                                       skipinitialspace=True)
    return default_csv



#%% Post Processing Methods
def fix_structure_names(line: tp.ParsedString) -> tp.ParsedString:
    '''If Structure name starts with "=", add "'" to start of name.
    '''
    if len(line) == 2:
        if 'Structure' in line[0]:
            structure_name = line[1]
            if structure_name.startswith('='):
                structure_name = "'" + structure_name
                line[1] = structure_name
    return line


#%% Line Processing
def to_plan_info_dict(plan_info_dict_list):
    '''Combine Plan Info dictionaries into dictionary of dictionaries.
    '''
    output_dict = dict()
    for plan_info_dict in plan_info_dict_list:
        plan_name = plan_info_dict.get('Plan')
        if not plan_name:
            plan_name = plan_info_dict.get('Plan sum')
            if not plan_name:
                plan_name = 'Plan'
        plan_info_dict['Plan'] = plan_name
        output_dict[plan_name] = plan_info_dict
    return output_dict

def to_structure_data_tuple(structure_data_list):
    '''Combine Structure and DVH data.
    '''
    structures_dict = dict()
    dvh_data_list = list()
    for structure_data, dvh_data in structure_data_list:
        plan_name = structure_data['Plan']
        course_id = structure_data['Course']
        structure_id = structure_data['Structure']
        logger.info(f'Reading DVH data for: {structure_id}.')
        indx = (course_id, plan_name, structure_id)
        structures_dict[indx] = structure_data
        data_columns = list(dvh_data.columns)
        indx_d = [indx + (d,) for d in data_columns]
        indx_names = ['Course', 'Plan', 'Structure', 'Data']
        index = pd.MultiIndex.from_tuples(indx_d, names=indx_names)
        dvh_data.columns = index
        dvh_data_list.append(dvh_data)
    structures_df = pd.DataFrame(structures_dict)
    dvh_df = pd.concat(dvh_data_list, axis='columns')
    return (structures_df, dvh_df)

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
                             tp.convert_numbers,
                             fix_structure_names]
    )
dvh_data_reader = tp.SectionReader(
    preprocessing_methods=[clean_ascii_text],
    default_parser=tp.define_fixed_width_parser(widths=10),
    post_processing_methods=[tp.trim_items, tp.drop_blanks,
                             tp.convert_numbers]
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
dvh_data_start = tp.SectionBreak(
    name='Start of DVH Data',
    trigger=tp.Trigger(['Ratio of Total Structure Volume']),
    offset='Before'
    )

dvh_info_break = tp.SectionBoundaries(
    start_section=None,
    end_section=plan_info_start
    )
plan_info_break = tp.SectionBoundaries(
    start_section=None,
    end_section=plan_info_end
    )
plan_group_break = tp.SectionBoundaries(
    start_section=plan_info_start,
    end_section=structure_info_start
    )
structure_info_break = tp.SectionBoundaries(
    start_section=structure_info_start,
    end_section=structure_info_end
    )
structure_group_break = tp.SectionBoundaries(
    start_section=structure_info_start,
    )
dvh_data_break = tp.SectionBoundaries(
    start_section=dvh_data_start,
    end_section=structure_info_start
    )

#%% Section definitions
dvh_info_section = tp.Section(
    section_name='DVH Info',
    boundaries=dvh_info_break,
    reader=dvh_info_reader,
    aggregate=tp.to_dict
    )
plan_info_section = tp.Section(
    section_name='Plan Info',
    boundaries=plan_info_break,
    reader=plan_info_reader,
    aggregate=tp.to_dict
    )
plan_info_group = tp.Section(
    section_name='Plan Info Group',
    boundaries=plan_group_break,
    reader=plan_info_section,
    aggregate=to_plan_info_dict
    )
structure_info_section = tp.Section(
    section_name='Structure',
    boundaries=structure_info_break,
    reader=structure_info_reader,
    aggregate=tp.to_dict
    )
dvh_data_section = tp.Section(
    section_name='DVH',
    boundaries=dvh_data_break,
    reader=dvh_data_reader,
    aggregate=tp.to_dataframe
    )
dvh_group_section = tp.Section(
    section_name='DVH Groups',
    boundaries=structure_group_break,
    reader=[structure_info_section, dvh_data_section],
    aggregate=to_structure_data_tuple
    )


def date_processing():
    pass
def number_processing():
    pass


#%% Main Iteration
def main():
    # Test File
    base_path = Path.cwd()

    test_file_path = r'Text Files'
    test_file = base_path / test_file_path / 'PlanSum vs Original.dvh'

    # Call Primary routine
    context = {
        'File Name': test_file.name,
        'File Path': test_file.parent,
        'Line Count': 0,
        }

    source = tp.file_reader(test_file)

    dvh_info = dvh_info_section.read(source, **context)
    plan_info = plan_info_group.read(source, **context)
    structures_df, dvh_df = dvh_group_section.read(source, **context)

    # Output DVH Data
    dvh_info_df = pd.Series(dvh_info)
    plan_data = pd.DataFrame(plan_info)
    struct_indx_names = ['Course', 'Plan', 'Structure']
    dvh_indx_names = ['Course', 'Plan', 'Structure', 'Data']
    output_file = base_path / 'read_dvh_test_results.xlsx'

    with pd.ExcelWriter(output_file) as writer:
        dvh_info_df.to_excel(writer, 'DVH Info')
        plan_data.to_excel(writer, 'Plan Data')
        structures_df.to_excel(writer, 'Structures Data',
                               index_label=struct_indx_names)
        dvh_df.to_excel(writer, 'DVH Data',
                        index_label=dvh_indx_names)

    print('done')

if __name__ == '__main__':
    main()

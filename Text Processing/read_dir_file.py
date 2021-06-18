'''Initial testing of Dir output parsing
Using test file  '.\Text Files\test_DIR_Data.txt'
Test file created with command:
DIR ".\Text Files\Test Dir Structure" /S /N /-C /T:W >  ".\Text Files\test_DIR_Data.txt"

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

folder_summary_pt = re.compile(
    r'(?P<files>'       # beginning of files string group
    r'[0-9]+'           # Integer number of files
    r')'                # end of files string group
    r'[ ]+'             # Arbitrary number of spaces
    r'(?P<type>'        # beginning of type string group
    r'File|Dir'         # "File" or " Dir" text
    r')'                # end of type string group
    r'\(s\)'            # "(s)" text
    r'[ ]+'             # Arbitrary number of spaces
    r'(?P<size>'        # beginning of size string group
    r'[0-9]+'           # Integer size of folder
    r')'                # end of size string group
    r' bytes'           # "bytes" text
    )

#%% Line Parsing Functions
# Files / DIRs Parse
def make_files_rule() -> tp.Rule:
    '''If  File(s) or  Dir(s) extract # files & size
        '''
    def files_parse(line, sentinel, *args, **kwargs) -> tp.ParseResults:
        '''Return two lines containing:
        'Number of File(s) / Dir(s)"

        Return two rows for a line containing:
            ### [File|Dir](s)          ### bytes
        The line:
               11 File(s)          72507 bytes
        Results in:
            [['Number of File(s)', 11],
             ['Size', 3501]]
        The line:
           23 Dir(s)     63927545856 bytes free
        Results in:
            [['Number of Dir(s)', 23],
             ['Size', 3501]]
        '''
        files_dict = sentinel.groupdict()
        parsed_lines = [
            [f'Number of {files_dict["type"]}(s)', int(files_dict['files'])],
            ['Size', int(files_dict['size'])]
            ]
        return parsed_lines

    files_trigger = tp.Trigger(folder_summary_pt, name='Files')
    approved_status_rule = tp.Rule(files_trigger,
                                   files_parse,
                                   name='Files_rule')
    return files_rule

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

# Line Parsing to do
#2021-06-18  14:54    <DIR>          .
#2021-06-18  14:54    <DIR>          ..
#2021-06-18  14:54    <DIR>          Dir1
#2021-06-18  14:54    <DIR>          Dir2
#2016-02-25  22:59                 3 TestFile1.txt
#2016-02-15  19:46                 7 TestFile2.rtf



# Prescribed Dose Rule
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
folder_start = tp.SectionBreak(
    name='Start of Folder',
    trigger=tp.Trigger(['Directory of']),
    offset='Before'
    )
folder_end = tp.SectionBreak(
    name='End of Folder',
    trigger=tp.Trigger([folder_summary_pt]),
    offset='After'
    )
summary_start = tp.SectionBreak(
    name='Start of DIR Summary',
    trigger=tp.Trigger(['Total Files Listed:']),
    offset='After'
    )
folder_break = tp.SectionBoundaries(
    start_section=folder_start,
    end_section=folder_end
    )
summary_break = tp.SectionBoundaries(
    start_section=summary_start,
    end_section=None
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


'''Initial testing of Dir output parsing
Using test file  '.\Text Files\test_DIR_Data.txt'
Test file created with command:
     DIR ".\Text Files\Test Dir Structure" /S /N /-C /T:W >  ".\Text Files\test_DIR_Data.txt"

DIR output has the following structure:
    Header Section:
         Volume in drive C has no label.
         Volume Serial Number is 56DB-14A7

    Multiple Folder sections

    Summary Section:
         Total Files Listed:
                  11 File(s)          72507 bytes
                  23 Dir(s)     63927545856 bytes free

Each Folder section has the following line types:
    Directory Label:
         Directory of C:\Test Dir Structure
    Directory listing:
        2021-06-18  14:54    <DIR>          Dir1
    File listing:
        2016-02-25  22:59                 3 TestFile1.txt
    File Count:
               4 File(s)           3501 bytes
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
from date_processer import  build_date_re, make_date_time_string


#%% Logging
logger = lg.config_logger(prefix='read_dvh.file', level='INFO')


#%% Regex Parsing patterns
# File Count and summary:
     #          1 File(s)          59904 bytes
     #         23 Dir(s)     63927545856 bytes free
folder_summary_pt = re.compile(
    '(?P<files>'       # beginning of files string group
    '[0-9]+'           # Integer number of files
    ')'                # end of files string group
    '[ ]+'             # Arbitrary number of spaces
    '(?P<type>'        # beginning of type string group
    'File|Dir'         # "File" or " Dir" text
    ')'                # end of type string group
    '\\(s\\)'          # "(s)" text
    '[ ]+'             # Arbitrary number of spaces
    '(?P<size>'        # beginning of size string group
    '[0-9]+'           # Integer size of folder
    ')'                # end of size string group
    ' bytes'           # "bytes" text
    )
date_pattern = build_date_re(compile_re=False)
file_listing_pt = re.compile(
    f'{date_pattern}'  # Insert date pattern
    '[ ]+'             # Arbitrary number of spaces
    '(?P<size>'        # beginning of size string group
    '[0-9]+'           # Integer size of folder
    ')'                # end of size string group
    ' '                # Single space
    '(?P<filename>'    # beginning of filename string group
    '.*'               # Integer size of folder
    ')'                # end of size string group
    '$'                # end of string
    )


#%% Line Parsing Functions
# Directory Label Rule

def truncate_dir(line: str, sentinel, *args,
                    context=None, **kwargs) -> tp.ParseResults:
    ''' Remove Top Directory from folder header.
    '''
    full_dir = line.replace('Directory of', '').strip()
    if context:
        top_dir = context.get('top_dir', '')
        tree_name = context.get('tree_name', 'top')
        truncated_line = full_dir.replace(top_dir, tree_name)
    else:
        truncated_line = full_dir
    return [['Directory', truncated_line]]

dir_header_rule = tp.Rule(
    name='Dir Header Rule',
    trigger=tp.Trigger('Directory of ', name='Directory Header'),
    pass_method=truncate_dir
    )

# skip <DIR>
def blank_line(*args, **kwargs) -> tp.ParseResults:
    return [['']]
skip_dir_rule = tp.Rule(
    name='Skip <DIR> Rule',
    trigger=tp.Trigger(' <DIR> ', name='Is Directory'),
    pass_method=blank_line
    )
skip_totals_rule = tp.Rule(
    name='Skip Total Files Header Rule',
    trigger=tp.Trigger('Total Files Listed:', name='Total Files Header'),
    pass_method=blank_line
    )


# Regular file listings
def file_parse(line: str, sentinel, *args, **kwargs) -> tp.ParseResults:
    '''Break file data into three rows containing Date, Size & Filename.

    Output has the following format:
        ['Date', date value: str ]
        ['Size', file size value: int]
        ['Filename', filename value: str].

    Typical file is:
        2016-02-25  22:59     3 TestFile1.txt
    File line is parsed using a regular expression with 3 named groups.

    Args:
        line (str): The text line to be parsed.
        sentinel (re.match): The results of the trigger test on the line.
            Contains 3 named groups: ['date', 'size', 'filename'].
        *args & **kwargs: Catch unused extra parameters passed to file_parse.

    Returns:
        tp.ParseResults: The parsed file information.
            The parsed file information consists of three lines with the
            following format:
                'Date', date value: datetime
                'Size', file size value: int
                'Filename', filename value: str.
    '''
    parsed_line_template = ''.join([
        'Filename, {filename}\n',
        'Date, {date}\n',
        'Size, {size}'
        ])
    date_str = {'date': make_date_time_string(sentinel)}
    file_line_parts = sentinel.groupdict(default='')
    file_line_parts.update(date_str)
    parsed_line_str = parsed_line_template.format(**file_line_parts)
    parsed_line = [new_line.split(',')
                for new_line in parsed_line_str.splitlines()]
    return [parsed_line]

# Regular File Parsing Rule
file_info_trigger = tp.Trigger(file_listing_pt, name='Files')
file_listing_rule = tp.Rule(file_info_trigger, file_parse, name='Files_rule')

# File Count Parsing Rule
def file_count_parse(line: str, sentinel, *args, **kwargs) -> tp.ParseResults:
    '''Break file data into two rows containing:
           Number of files, & Directory size.

    Output has the following format:
        ['Number of files', file count value: int]
        ['Directory Size', directory size value: int]

    Typical line is:
        4 File(s)           3501 bytes
    File count is parsed using a regular expression with 2 named groups.

    Args:
        line (str): The text line to be parsed.
        sentinel (re.match): The results of the trigger test size the line.
            Contains 3 named groups: ['files', 'type', 'size'].
        *args & **kwargs: Catch unused extra parameters passed to file_parse.

    Returns:
        tp.ParseResults: The parsed file information.
            The parsed file information consists of three lines with the
            following format:
                'Number of files', file count value: int
                'Directory Size', directory size value: int
    '''
    file_count_parts = sentinel.groupdict(default='')
    # Manage case where bytes free is given:
    # 23 Dir(s)     63927545856 bytes free
    if line.strip().endswith('free'):
        file_count_parts['size_label'] = 'Free Space'
    else:
        file_count_parts['size_label'] = 'Size'
    parsed_line_template = ''.join([
        'Number of {type}s, {files}\n',
        'Directory {size_label}, {size}'
        ])
    parsed_line_str = parsed_line_template.format(**file_count_parts)
    parsed_line = [new_line.split(',')
                   for new_line in parsed_line_str.splitlines()]
    return parsed_line
file_count_trigger = tp.Trigger(folder_summary_pt, name='Files')
file_count_rule = tp.Rule(file_count_trigger, file_count_parse,
                          name='Files_rule')


# Files / DIRs Parse
def make_files_rule() -> tp.Rule:
    '''If  File(s) or  Dir(s) extract # files & size
        '''
    def files_total_parse(line, sentinel, *args, **kwargs) -> tp.ParseResults:
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
        files_dict = sentinel.groupdict(default='')
        parsed_line_template = ''.join([
            f'Number of {files_dict["type"]}(s),',
            f'{files_dict["files"]}\n',
            f'Size,',
            f'{files_dict["size"]}'
            ])
        parsed_line = [new_line.split(',')
                       for new_line in parsed_line_str.splitlines()]
        return parsed_line

    files_total_trigger = tp.Trigger(folder_summary_pt, name='Files')
    files_total_rule = tp.Rule(files_total_trigger, files_total_parse,
                         name='Files_Total_rule')
    return files_total_rule


default_csv = tp.define_csv_parser('dir_files', delimiter=':',
                                       skipinitialspace=True)




#%% Line Processing
def print_lines(parsed_list):
    output = list()
    for item in parsed_list:
        pprint(item)
        output.append(item)
    return output


def to_folder_dict(folder_list):
    '''Combine folder Info dictionaries into dictionary of dictionaries.
    '''
    # TODO remove top dir here
    # TODO create full path
    # TODO separate directory info from file info
    output_dict = dict()
    for folder_dict in folder_list:
        plan_name = plan_info_dict.get('Plan')
        if not plan_name:
            plan_name = plan_info_dict.get('Plan sum')
            if not plan_name:
                plan_name = 'Plan'
        plan_info_dict['Plan'] = plan_name
        output_dict[plan_name] = plan_info_dict
    return output_dict


#%% Reader definitions
default_parser = tp.define_csv_parser('dir_files', delimiter=':',
                                       skipinitialspace=True)
heading_reader = tp.SectionReader(
    parsing_rules=[],
    default_parser=default_parser,
    post_processing_methods=[tp.trim_items])
folder_reader = tp.SectionReader(
    parsing_rules=[skip_dir_rule, file_listing_rule, dir_header_rule,
                   file_count_rule],
    default_parser=default_parser,
    post_processing_methods=[tp.drop_blanks])
summary_reader = tp.SectionReader(
    parsing_rules=[file_count_rule, skip_totals_rule],
    default_parser=default_parser,
    post_processing_methods=[tp.drop_blanks]
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
    offset='Before'
    )


#%% SectionBoundaries definitions
header_break = tp.SectionBoundaries(
    start_section=None,
    end_section=folder_start
    )
folder_break = tp.SectionBoundaries(
    start_section=folder_start,
    end_section=folder_end
    )
all_folders_break = tp.SectionBoundaries(
    start_section=folder_start,
    end_section=summary_start
    )
summary_break = tp.SectionBoundaries(
    start_section=summary_start,
    end_section=None
    )



#%% Section definitions
header_section = tp.Section(
    section_name='Header',
    boundaries=header_break,
    reader=heading_reader,
    aggregate=print_lines
    )
folder_section = tp.Section(
    section_name='Folder',
    boundaries=folder_break,
    reader=folder_reader,
    aggregate=tp.to_dict
    )
all_folder_section = tp.Section(
    section_name='All Folders',
    boundaries=all_folders_break,
    reader=[folder_section],
    aggregate=print_lines
    )
summary_section = tp.Section(
    section_name='Summary',
    boundaries=summary_break,
    reader=summary_reader,
    aggregate=tp.to_dict
    )


#%% Main Iteration
def main():
    # Test File
    base_path = Path.cwd()

    test_file_path = base_path / 'Text Files'
    test_file = test_file_path / 'test_DIR_Data.txt'

    # Call Primary routine
    context = {
        'File Name': test_file.name,
        'File Path': test_file.parent,
        'top_dir': str(test_file_path),
        'tree_name': 'Test folder Tree'
        }

    source = tp.file_reader(test_file)

    #dir_info = header_section.read(source, **context)
    file_info = all_folder_section.read(source, **context)
    summary = summary_section.read(source, **context)

    # Output  Data

    print('done')

if __name__ == '__main__':
    main()

# pylint: disable=anomalous-backslash-in-string
# pylint: disable=unused-argument
'''Initial testing of Dir output parsing
Using test file  .\Text Files\test_DIR_Data.txt
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


#%% Imports
from pathlib import Path
from pprint import pprint
import re
import pandas as pd
import xlwings as xw

import logging_tools as lg
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

def extract_directory(line: str, event, *args,
                    context=None, **kwargs) -> tp.ParseResults:
    '''Extract Directory path from folder header.
    '''
    full_dir = line.replace('Directory of', '').strip()
    return [[full_dir]]


dir_header_rule = tp.Rule(
    name='Dir Header Rule',
    sentinel='Directory of ',
    pass_method=extract_directory
    )


# skip <DIR>
def blank_line(*args, **kwargs) -> tp.ParseResults:
    return [['']]


skip_dir_rule = tp.Rule(
    name='Skip <DIR> Rule',
    sentinel=' <DIR> ',
    pass_method=blank_line
    )
skip_totals_rule = tp.Rule(
    name='Skip Total Files Header Rule',
    sentinel='Total Files Listed:',
    pass_method=blank_line
    )


# Regular file listings
def file_parse(line: str, event, *args, **kwargs) -> tp.ParseResults:
    '''Break file data into three columns containing Filename, Date, Size.

    Typical file is:
        2016-02-25  22:59     3 TestFile1.txt
    File line is parsed using a regular expression with 3 named groups.
    Output for the example above is:
        [[TestFile1.txt , 2016-02-25  22:59, 3]]

    Args:
        line (str): The text line to be parsed.
        event (re.match): The results of the trigger test on the line.
            Contains 3 named groups: ['date', 'size', 'filename'].
        *args & **kwargs: Catch unused extra parameters passed to file_parse.

    Returns:
        tp.ParseResults: A one-item list containing the parsed file
            information as a 3-item tuple:
                [(filename: str, date: str, file size: int)].
    '''
    file_line_parts = event.groupdict(default='')
    parsed_line = tuple([
        file_line_parts['filename'],
        make_date_time_string(event),
        int(file_line_parts['size'])
        ])
    return [parsed_line]


# Regular File Parsing Rule
file_listing_rule = tp.Rule(file_listing_pt, pass_method=file_parse,
                            name='Files_rule')


# File Count Parsing Rule
def file_count_parse(line: str, event, *args, **kwargs) -> tp.ParseResults:
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
        event (re.match): The results of the trigger test size the line.
            Contains 3 named groups: ['files', 'type', 'size'].
        *args & **kwargs: Catch unused extra parameters passed to file_parse.

    Returns:
        tp.ParseResults: The parsed file information.
            The parsed file information consists of three lines with the
            following format:
                'Number of files', file count value: int
                'Directory Size', directory size value: int
    '''
    file_count_parts = event.groupdict(default='')
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
file_count_rule = tp.Rule(folder_summary_pt, pass_method=file_count_parse,
                          name='Files_rule')


skip_file_count_rule = tp.Rule(
    name='Skip File(s) Rule',
    sentinel=folder_summary_pt,
    pass_method=blank_line
    )


# Files / DIRs Parse
def make_files_rule() -> tp.Rule:
    '''If  File(s) or  Dir(s) extract # files & size
        '''
    def files_total_parse(line, event, *args, **kwargs) -> tp.ParseResults:
        '''Break file counts into three columns containing:
           Type (File or Dir), Count, Size.

        The line:
               11 File(s)          72507 bytes
        Results in:
            [('File', 11, 3501)]
        The line:
           23 Dir(s)     63927545856 bytes free
        Results in:
            [('Dir', 23, 3501)]

    Args:
        line (str): The text line to be parsed.
        event (re.match): The results of the trigger test on the line.
            Contains 3 named groups: ['type', 'files', 'size'].
        *args & **kwargs: Catch unused extra parameters passed to file_parse.

    Returns:
        tp.ParseResults: A one-item list containing the parsed file count
            information as a 3-item tuple:
                [(Type: str (File or Dir), Count: int, Size: int)].
        '''
        files_dict = event.test_value.groupdict(default='')
        parsed_line = tuple([
            files_dict["type"],
            files_dict["files"],
            files_dict["size"]
            ])
        return [parsed_line]

    files_total_rule = tp.Rule(folder_summary_pt,
                               pass_method=files_total_parse,
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


def to_folder_dict(folder_gen):
    '''Combine folder info into dictionary.
    '''
    # TODO separate directory info from file info
    #The first line in the folder list is the directory path
    directory = folder_gen.__next__()[0]
    folder_dict = {'Directory': directory}
    for folder_info in folder_gen:
        filename, date, file_size = folder_info
        full_path = '\\'.join([directory, filename])
        file_parts = filename.rsplit('.', 1)
        if len(file_parts) > 1:
            extension = file_parts[1]
        else:
            extension = ''
        folder_dict = {
            'Path': full_path,
            'Directory': directory,
            'Filename': filename,
            'Extension': extension,
            'Date': date,
            'Size': file_size
            }
    return folder_dict


def make_files_table(dir_gen):
    '''Combine folder info dictionaries into Pandas DataFrame.
    '''
    list_of_folders = list(dir_gen)
    files_table = pd.DataFrame(list_of_folders)
    files_table.set_index('Path')
    return files_table


#%% Reader definitions
default_parser = tp.define_csv_parser('dir_files', delimiter=':',
                                       skipinitialspace=True)
heading_reader = tp.ProcessingMethods([
    default_parser,
    tp.trim_items
    ])
folder_reader = tp.ProcessingMethods([
    tp.RuleSet([skip_dir_rule, file_listing_rule, dir_header_rule,
             skip_file_count_rule], default=default_parser),
    tp.drop_blanks
    ])
summary_reader = tp.ProcessingMethods([
    tp.RuleSet([file_count_rule, skip_totals_rule], default=default_parser),
    tp.drop_blanks
    ])


#%% SectionBreak definitions
folder_start = tp.SectionBreak(
    name='Start of Folder', sentinel='Directory of', break_offset='Before')
folder_end = tp.SectionBreak(name='End of Folder',sentinel=folder_summary_pt,
                             break_offset='After')
summary_start = tp.SectionBreak(sentinel='Total Files Listed:',
                                name='Start of DIR Summary', break_offset='Before')


#%% Section definitions
header_section = tp.Section(
    section_name='Header',
    start_section=None,
    end_section=folder_start,
    processor=heading_reader,
    aggregate=print_lines
    )
folder_section = tp.Section(
    section_name='Folder',
    start_section=folder_start,
    end_section=folder_end,
    processor=folder_reader,
    aggregate=to_folder_dict
    )
all_folder_section = tp.Section(
    section_name='All Folders',
    start_section=folder_start,
    end_section=summary_start,
    processor=[folder_section],
    aggregate=make_files_table
    )
summary_section = tp.Section(
    section_name='Summary',
    start_section=summary_start,
    end_section=None,
    processor=summary_reader,
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
    file_info = all_folder_section.read(source, context)
    #summary = summary_section.read(source, **context)

    # Output  Data
    xw.view(file_info)
    print('done')

if __name__ == '__main__':
    main()

'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string

#%% Imports
from pathlib import Path
from pprint import pprint

from typing import List
from typing import List
import csv
import re
import logging_tools as lg
from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorValueError
from buffered_iterator import BufferOverflowWarning
import Text_Processing as tp


#%% Logging
logger = lg.config_logger(prefix='read_dvh.file', level='INFO')


#%% Line Parsing
def make_prescribed_dose_trigger():
        prescribed_dose_pattern = (
            r'^'                # Beginning of string
            r'Prescribed dose'  # Row Label
            r'\s*'              # Skip whitespace
            r'[[]'              # Unit start delimiter
            r'(?P<unit>'        # Beginning of unit group
            r'[A-Za-z]+'        # Unit text
            r')'                # end of unit string group
            r'[]]'              # Unit end delimiter
            r'\s*'              # Skip whitespace
            r':'                # Dose delimiter
            r'\s*'              # Skip whitespace
            r'(?P<dose>'        # Beginning of dose group
            r'[0-9.]+'          # Dose value
            r'|not defined'     # Undefined dose alternate
            r')'                # end of value string group
            r'\s*'              # drop trailing whitespace
            r'$'                # end of string
            )
        re_pattern = re.compile(prescribed_dose_pattern)
        dose_trigger = tp.Trigger(re_pattern, name='Prescribed Dose')
        return dose_trigger

def parse_prescribed_dose(sentinel):
    '''Split "Prescribed dose [cGy]" into 2 lines:
        Prescribed dose
        Prescribed dose Unit
        '''
    parse_template = [
        ['Prescribed dose', '{dose}'],
        ['Prescribed dose Unit', '{unit}']
        ]
    match_results = sentinel.groupdict()
    if match_results['dose'] == 'not defined':
        parsed_lines = [
            ['Prescribed dose', None],
            ['Prescribed dose Unit', None]
            ]
    else:
        parsed_lines = [
            [string_item.format(**match_results) for string_item in line_tmpl]
            for line_tmpl in parse_template
            ]
    return parsed_lines

def prescribed_dose_rule(context, line):
    dose_trigger = make_prescribed_dose_trigger()
    is_match, sentinel = dose_trigger.apply(context, line)
    if is_match:
        parsed_lines = parse_prescribed_dose(sentinel)
        return parsed_lines
    return None

def date_rule(context, line):
    '''If Treatment Approved, Split "Plan Status" into 3 lines:
        Plan Status
        Approved on
        Approved by


        Next rule
        By -> new row
            Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal
            Plan Status: Planning Approved
            Plan Status: Unapproved

        '''
    date_trigger = tp.Trigger('Date', name='Starts With Date', location='START')
    is_match, sentinel = date_trigger.apply(context, line)
    if is_match:
        parsed_lines = [[sentinel, line.split(':',maxsplit=1)[1]]]
        return parsed_lines
    return None

def approved_status_rule(context, line):
    approved_status_trigger = tp.Trigger('Treatment Approved', location='IN',
                                      name='Treatment Approved')
    is_match, sentinel = approved_status_trigger.apply(context, line)
    if is_match:
        break1 = line.find(sentinel)
        break2 = break1 + len(sentinel)
        break3 = line.find('by')
        break4 = break3 + 3
        parsed_lines = [
            ['Plan Status', line[break1:break2]],
            ['Approved on', line[break2:break3]],
            ['Approved by', line[break4:]]
            ]
        return parsed_lines
    return None


#%% Section definitions
def break_iterator(source, context, break_triggers: List[tp.SectionBreak]):
    logger.debug('In break_iterator')
    for line in source:
        logger.debug(f'In section_breaks, received line: {line}')
        for break_trigger in break_triggers:
            logger.debug(f'Checking Trigger: {break_trigger.name}')
            is_break, context = break_trigger.check(context, line)
            if is_break:
                logger.debug(f'Section Break Detected')
                raise tp.StopSection(context=context)
        logger.debug('No Break Triggered')
        yield line
    raise EOF(context=context)

def line_parser(active_lines):
    csv.register_dialect('test',
                         delimiter=',',
                         doublequote=True,
                         quoting=csv.QUOTE_MINIMAL,
                         quotechar='"',
                         escapechar=None,
                         lineterminator='\r\n',
                         skipinitialspace=False,
                         strict=False)
    a = csv.get_dialect('test')
    csvreader = csv.reader(active_lines, dialect='test')
    csvreader = csv.reader(active_lines, delimiter=':', quotechar='"')
    tp.Trigger(['Prescribed dose'])
    # Test: Cleaned Line contains 'Prescribed dose'
    # Action -> Split  Prescribed dose [cGy]: 4140.0 into 2 lines:
    # [['Prescribed dose', '4140.0'],
    # ['Prescribed dose Unit', 'cGy']]
    #
    # Don't split date portion
    # By -> new row
    # Plan Status: Treatment Approved Thursday, January 02, 2020 12:55:56 by gsal
    # Plan Status: Planning Approved
    prescribed_dose_pattern = (
        r'^'                # Beginning of string
        r'Prescribed dose'  # Row Label
        r'\s*'              # Skip whitespace
        r'[[]'              # Unit start delimiter
        r'(?P<unit>'        # Beginning of unit group
        r'[A-Za-z]+'        # Unit text
        r')'                # end of unit string group
        r'[]]'              # Unit end delimiter
        r'\s*'              # Skip whitespace
        r':'                # Dose delimiter
        r'\s*'              # Skip whitespace
        r'(?P<dose>'        # Beginning of dose group
        r'[0-9.]+'          # Dose value
        r'|not defined'     # Undefined dose alternate
        r')'                # end of value string group
        r'\s*'              # drop trailing whitespace
        r'$'                # end of string
        )
    find_dose_pattern = re.compile(prescribed_dose_pattern)

def scan_section(context, section_name, break_triggers: List[tp.SectionBreak]):
# Apply Section Cleaning -> clean_lines
# Check for End of Section Break -> break_triggers

# Call Line Parser, passing Context & Lines -> Dialect, Special Lines

# Apply Line Processing Rules -> trim_lines

# Apply Section Formatting ->
    context['Current Section'] = section_name
    logger.debug(f'Starting New Section: {section_name}.')
    cleaned_lines = tp.clean_lines(context['Source'])
    active_lines = break_iterator(cleaned_lines, context, break_triggers)
    csvreader = csv.reader(active_lines, delimiter=':', quotechar='"')
    trimmed_lines = tp.trim_lines(csvreader)

    # Section iterator
    section_lines = list()
    while True:
        row = None
        try:
            row = trimmed_lines.__next__()
        except tp.StopSection as stop_sign:
            #pprint(stop_sign)
            print()
            logger.debug('end of the section')
            break
        except tp.EOF as eof:
            #pprint(eof)
            print()
            logger.debug('End of Source')
            break
        logger.debug(f'Found row: {row}.')
        if row is not None:
            section_lines.append(row)
        logger.debug('next line')
    return section_lines


def section_manager(context):
    dvh_info_break = [
        tp.SectionBreak(tp.Trigger(['Plan:', 'Plan sum:']),name='dvh_info')
        ]

    plan_info_break = [
        tp.SectionBreak(tp.Trigger(['% for dose (%):']), offset='After',
                     name='End of Plan Info')
        ]

    plan_data_break = [
        tp.SectionBreak(tp.Trigger(['Structure:']), offset='Before',
                     name='End of Plan Info')
        ]

    section_lines = scan_section(context, section_name = 'DVH Info',
                                 break_triggers = dvh_info_break)
    pprint(section_lines)
    section_lines = scan_section(context, section_name = 'Plan Info',
                                 break_triggers = plan_info_break)
    pprint(section_lines)
    section_lines = scan_section(context, section_name = 'Plan Info',
                                 break_triggers = plan_data_break)
    pprint(section_lines)
    return context, section_lines


def file_reader(test_file):
    with open(test_file, newline='') as csvfile:
        raw_lines = tp.BufferedIterator(csvfile)
        context = {
            'File Name': test_file.name,
            'File Path': test_file.parent,
            'Line Count': 0,
            'Source': raw_lines
            }
        context, section_lines = section_manager(context)
    return context, section_lines

def process_lines(section_lines):
    parsed_lines = tp.BufferedIterator(section_lines)
    pass



def merge_rows(parsed_lines):
    for parsed_line in parsed_lines:
        if len(parsed_line) > 0:
            yield line

def drop_blanks(parsed_lines):
    for parsed_line in parsed_lines:
        if len(parsed_line) > 0:
            yield line


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

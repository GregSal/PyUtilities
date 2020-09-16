'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string

#%% Imports
from pathlib import Path
from pprint import pprint
from functools import partial
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

def parse_prescribed_dose(sentinel)->List[List[str]]:
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

def prescribed_dose_rule(context, line)->List[List[str]]:
    dose_trigger = make_prescribed_dose_trigger()
    is_match, sentinel = dose_trigger.apply(context, line)
    if is_match:
        parsed_lines = parse_prescribed_dose(sentinel)
        return parsed_lines
    return None

def date_rule(context, line)->List[List[str]]:
    '''If Date,don't split beyond first :'''
    date_trigger = tp.Trigger('Date', name='Starts With Date', location='START')
    is_match, sentinel = date_trigger.apply(context, line)
    if is_match:
        parsed_lines = [[sentinel, line.split(':',maxsplit=1)[1]]]
        return parsed_lines
    return None


def approved_status_rule(context, line)->List[List[str]]:
    '''If Treatment Approved, Split "Plan Status" into 3 lines:
        Plan Status
        Approved on
        Approved by
        '''
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


def csv_parser(dialect_name: str, context, line):
    csvreader = csv.reader([line], dialect=dialect_name)
    parsed_lines = [parsed_line for parsed_line in csvreader]
    return parsed_lines

#%% Line Processing

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


def line_parser(context, source):
    csv.register_dialect('dvh_info',
                         delimiter=':',
                         lineterminator='\r\n',
                         skipinitialspace=True,
                         strict=False)
    default_parser = partial(csv_parser, dialect_name='dvh_info')
    rule_iter = (rule for rule in [
            prescribed_dose_rule,
            date_rule,
            approved_status_rule,
            default_parser])
    logger.debug('In line_parser')
    parsed_lines = None
    for line in source:
        logger.debug(f'In line_parser, received line: {line}')
        try:
            while parsed_lines is None:
                rule = rule_iter.__next__()
                parsed_lines = rule(context, line)
        except StopIteration:
            continue
        else:
            for parsed_line in parsed_lines:
                yield parsed_line
    raise EOF(context=context)


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
    parsed_lines = line_parser(context, active_lines)
    processed_lines = tp.merge_continued_rows(
        tp.merge_extra_items(
            tp.drop_empty_lines(
                tp.trim_lines(parsed_lines)
                )
            )
        )


    # Section iterator
    section_lines = list()
    while True:
        row = None
        try:
            row = processed_lines.__next__()
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

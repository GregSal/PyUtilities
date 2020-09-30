'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string

#%% Imports
from pathlib import Path
from pprint import pprint
from functools import partial
from itertools import chain
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


#%% Line Parsing Functions
def date_parse(line: str, *args, **kwargs) -> tp.ParseResults:
    '''If Date,don't split beyond first :.'''
    parsed_line = line.split(':', maxsplit=1)
    return [parsed_line]


def approved_status_parse(line, *args, **kwargs) -> tp.ParseResults:
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


#%% Prescribed Dose Rule
def make_prescribed_dose_rule()->List[List[str]]:

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


def date_rule(context, line)->List[List[str]]:
    '''If Date,don't split beyond first :'''
    date_trigger = tp.Trigger('Date', name='Starts With Date', location='START')
    is_match, sentinel = date_trigger.apply(context, line)
    if is_match:
        parsed_lines = [
            [sentinel,
             line.split(':',maxsplit=1)[1]]
            ]
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
        idx1 = line.find(sentinel)
        idx2 = idx1 + len(sentinel)
        idx3 = line.find('by')
        idx4 = idx3 + 3
        parsed_lines = [
            ['Plan Status', line[idx1:idx2]],
            ['Approved on', line[idx2:idx3]],
            ['Approved by', line[idx4:]]
            ]
        return parsed_lines
    return None


def csv_parser(context, line, dialect_name: str):
    csvreader = csv.reader([line], dialect=dialect_name)
    parsed_lines = [parsed_line for parsed_line in csvreader]
    return parsed_lines


#%% Line Processing

#%% Section definitions
#TODO Create Section Class
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
    rules = [
        prescribed_dose_rule,
        date_rule,
        approved_status_rule,
        default_parser
        ]
    logger.debug('In line_parser')
    for line in source:
        logger.debug(f'In line_parser, received line: {line}')
        for rule in rules:
            parsed_lines = rule(context, line)
            if parsed_lines is not None:
                break
        if parsed_lines is not None:
            for parsed_line in parsed_lines:
                yield parsed_line


def section_iter(processed_lines):
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
            yield row
        logger.debug('next line')


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
    processed_lines = tp.convert_numbers(
        tp.merge_continued_rows(
            tp.merge_extra_items(
                tp.drop_blanks(
                    tp.trim_lines(
                        parsed_lines
                        )
                    )
                )
            )
        )

    section_output = tp.to_dict(section_iter(processed_lines))
    return section_output


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

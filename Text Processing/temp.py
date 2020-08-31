#%% Imports
from pathlib import Path
from pprint import pprint
from collections import deque
import csv
from file_utilities import clean_ascii_text
import logging_tools as lg


#%% Logging
logger = lg.config_logger(prefix='read_dvh.file')

#%% Exceptions
class StopSection(GeneratorExit): pass
#%% Classes
class LineIterator():
    '''Iterate through line sequence.
    '''
    def __init__(self, source, max_lines=5):
        self.source = source
        self.previous_lines = deque(maxlen=max_lines)
        self._step_back = 0
        self.repeat_lines = deque(maxlen=max_lines)
        return 

    @property
    def step_back(self):
        return self._step_back

    @step_back.setter
    def step_back(self, num_lines):
        if num_lines < 0:
            raise ValueError("Can't step back negative lines")
        if len(self.previous_lines) < num_lines:
            msg = (f"Can't step back {num_lines} lines.\n\t"
                   f"only have {len(self.previous_lines)} previous lines "
                    "available.")
            raise ValueError(msg)
        else:
            self._step_back =  num_lines

    def __iter__(self):
        '''Step through a line sequence allowing for retracing steps.
        '''
        for line in self.source:            
            if self._step_back:
                self.rewind(line)
            while len(self.repeat_lines) > 0:
                old_line = self.repeat_lines.pop()
                self.previous_lines.append(old_line)
                logger.debug(f'In LineIterator.__iter__, yielding old_line: {old_line}')
                yield old_line
            self.previous_lines.append(line)
            logger.debug(f'In LineIterator.__iter__, yielding line: {line}')
            yield line
        return

    def rewind(self, current_line):
        self.repeat_lines.append(current_line)
        for step in range(self._step_back):
            self._step_back -= 1
            if len(self.previous_lines) > 0:
                self.repeat_lines.append(self.previous_lines.pop())
        self._step_back = 0

     #%% Test File
base_path = Path.cwd()

test_file_path = r'..\Testing\Test Data\Text Files'
test_file = base_path / test_file_path / 'PlanSum vs Original.dvh'

#%% Functions
def clean_lines(file):
    for raw_line in file:
        logger.debug(f'In clean_lines, yielding raw_line: {raw_line}')
        yield clean_ascii_text(raw_line)

def trim_lines(parsed_lines):
    for parsed_line in parsed_lines:
        trimed_lines = [item.strip() for item in parsed_line]
        logger.debug(f'In trim_lines, yielding trimed_lines: {trimed_lines}')
        yield trimed_lines

def dvh_info_section(cleaned_lines):
    logger.debug('in dvh_info section')
    for cleaned_line in cleaned_lines:
        if 'Plan:' in cleaned_line:
            raise StopSection
        elif 'Plan sum:' in cleaned_line:
            raise StopSection
        else:
            logger.debug(f'In dvh_info_section, yielding cleaned_line: {cleaned_line}')
            yield cleaned_line

def plan_info_section(cleaned_lines):
    logger.debug('in plan_info section')
    for cleaned_line in cleaned_lines:
        if '% for dose (%)' in cleaned_line:
            logger.debug(f'In plan_info_section, yielding cleaned_line: {cleaned_line}')
            yield cleaned_line
            raise StopSection
        else:
            logger.debug(f'In plan_info_section, yielding cleaned_line: {cleaned_line}')
            yield cleaned_line

def plan_data_section(cleaned_lines):
    logger.debug('in plan_data section')
    for cleaned_line in cleaned_lines:
        if 'Plan:' in cleaned_line:
            cleaned_lines.step_back = 2
            logger.debug(f'In plan_data_section, yielding cleaned_lines')
            yield from plan_info_section(cleaned_lines)
        elif 'Plan sum:' in cleaned_line:
            cleaned_lines.step_back = 2
            logger.debug(f'In plan_data_section, yielding cleaned_lines')
            yield from plan_info_section(cleaned_lines)
        elif 'Structure' in cleaned_line:
            cleaned_lines.step_back = 2
            raise StopSection
        else:
            continue


def drop_units(text: str)->float:
    number_value_pattern = (
        '^'                # beginning of string
        '\s*'              # Skip leading whitespace
        '(?P<value>'       # beginning of value integer group
        '[-+]?'            # initial sign
        '\d+'              # float value before decimal
        '[.]?'             # decimal Place
        '\d*'              # float value after decimal
        ')'                # end of value string group
        '\s*'              # skip whitespace
        '(?P<unit>'        # beginning of value integer group
        '[^\s]*'           # units do not contain spaces
        ')'                # end of unit string group
        '\s*'              # drop trailing whitespace
        '$'                # end of string
        )
    #find_num = re.compile(number_value_pattern)
    find_num = re.findall(number_value_pattern, text)
    if find_num:
        value, unit = find_num[0]
        return value
    return text


#%% Main Iteration

def scan_section(this_section):
    cleaned_lines.step_back = 2
    section = this_section(cleaned_lines)
    csvreader = csv.reader(section, delimiter=':', quotechar='"')
    trimmed_lined = trim_lines(csvreader)
    section_lines = list()
    while True:
        try:
            row = trimmed_lined.__next__()
            logger.debug(row)
            section_lines.append(row)
        except StopSection as stop_sign:
            pprint(stop_sign)
            logger.debug('end of the section')
            break
        except IndexError as eof:
            pprint(eof)
            logger.debug('End of lines')
            break
        else:
            logger.debug('next line')
            continue
    return section_lines

           


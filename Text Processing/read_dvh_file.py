'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string

#%% Imports
from pathlib import Path
from pprint import pprint
from collections import deque
from typing import List, Dict, Any
import csv
import re
from file_utilities import clean_ascii_text
import logging_tools as lg


#%% Logging
logger = lg.config_logger(prefix='read_dvh.file')

#%% Exceptions
class TextReadException(Exception): pass


class StopSection(GeneratorExit):
    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context

    def get_context(self):
        return self.context


#%% Classes
class TextTrigger():
    '''
     Trigger Types:
     None
     List[str]
     Regex
     Callable
     n
     If None continue  to end of file  / Stream
     If list of strings, a match with any string in the list will be a pass
     The matched string will be added to the Context dict.
     If Regex the re.match object will be added to the Context dict.
     If Callable, a non-None return value will be a pass
     The return value will be added to the Context dict.
     Triggers can be chained for "AND" operations.
     If n skip n lines then trigger
     If Repeating sub-sections, can be number of repetitions
     '''
    def __init__(self, sentinel_list: List[str], name='TextTrigger'):
        '''Define Text strings that signal a trigger event.
        sentinel
        '''
        self.sentinels = sentinel_list

    def apply(self, context: Dict[str, any], line: str)->(bool, str):
        logger.debug('in apply trigger')
        for sentinel in self.sentinels:
            if sentinel in line:
                logger.debug(f'Triggered on {sentinel}')
                return True,  sentinel
            else:
                return False, None


class SectionBreak():
    def __init__(self, trigger: TextTrigger,
                 offset='Before', name='SectionBreak'):
        '''
        starting_offset	[Int or str] if str, one of Before or After
        if 0 or 'Before, Include the line that activates the Trigger in the section.
        if 1 or 'After, Skip the line that activates the Trigger.
        '''
        self.name = name
        self.step_back = 0
        self.set_step_back(offset)
        self.trigger = trigger

    def set_step_back(self, offset):
        try:
            self.step_back = -(int(offset) - 1)
        except ValueError:
            if isinstance(offset, str):
                if 'Before' in offset:
                    self.step_back = 1
                elif 'After' in offset:
                    self.step_back = 0

    def check(self, context: Dict[str, any], line: str):
        logger.debug('in section_break.check')
        is_break, sentinel = self.trigger.apply(context, line)
        if is_break:
            logger.debug(f'Break triggered by {sentinel}')
            context['sentinel'] = sentinel
        return is_break, context


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
        self._step_back =  num_lines

    def __iter__(self):
        '''Step through a line sequence allowing for retracing steps.
        '''
        for line in self.source:
            if self._step_back:
                self.rewind()
            while len(self.repeat_lines) > 0:
                old_line = self.repeat_lines.pop()
                self.previous_lines.append(old_line)
                logger.debug(f'\n\nIn LineIterator.__iter__, yielding old_line: {old_line}')
                yield old_line
            self.previous_lines.append(line)
            logger.debug(f'\n\nIn LineIterator.__iter__, yielding line: {line}')
            yield line


    def rewind(self):
        for step in range(self._step_back):
            self._step_back -= 1
            if len(self.previous_lines) > 0:
                self.repeat_lines.append(self.previous_lines.pop())
        self._step_back = 0


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



#%% Section definitions

def section_breaks(source, context, break_triggers: List[SectionBreak]):
    logger.debug('in section_breaks')
    for line in source:
        logger.debug(f'In section_breaks, received line: {line}')
        for break_trigger in break_triggers:
            logger.debug(f'Checking Trigger: {break_trigger.name}')            
            is_break, context = break_trigger.check(context, line)
            if is_break:
                logger.debug(f'Section Break Detected')
                if break_trigger.step_back > 0: # Don't use current line
                    logger.debug(f'Stepping back {break_trigger.step_back} lines')                    
                    context['Source'].step_back = break_trigger.step_back
                else: # Use more lines before activating break
                    logger.debug(f'Using {break_trigger.step_back + 1} more lines before break')                    
                    for step in range(break_trigger.step_back + 1):
                        logger.debug(f'Using {step} more lines')
                        yield line
                raise StopSection(context=context)        
        logger.debug('No Break Triggered')
        yield line
    raise StopSection(context=context)

def scan_section(context, section_name, break_triggers):
    context['Current Section'] = section_name
    logger.debug(f'Starting New Section: {section_name}.')
    cleaned_lines = clean_lines(context['Source'])
    section = section_breaks(cleaned_lines, context, break_triggers)
    csvreader = csv.reader(section, delimiter=':', quotechar='"')
    trimmed_lined = trim_lines(csvreader)
    section_lines = list()
    while True:
        row = None
        try:
            row = trimmed_lined.__next__()
        except StopSection as stop_sign:
            pprint(stop_sign)
            print()
            logger.debug('end of the section')
            break
        except IndexError as eof:
            pprint(eof)
            print()
            logger.debug('End of Source')
            break
        logger.debug(f'found row: {row}.')
        if row is not None:
            section_lines.append(row)
        logger.debug('next line')
    return section_lines


def plan_data_section(cleaned_lines):
    logger.debug('in plan_data section')
    for cleaned_line in cleaned_lines:
        if 'Plan:' in cleaned_line:
            cleaned_lines.step_back = 2
            logger.debug('In plan_data_section, yielding cleaned_lines')
            yield from plan_info_section(cleaned_lines)
        elif 'Plan sum:' in cleaned_line:
            cleaned_lines.step_back = 2
            logger.debug('In plan_data_section, yielding cleaned_lines')
            yield from plan_info_section(cleaned_lines)
        elif 'Structure' in cleaned_line:
            cleaned_lines.step_back = 2
            raise StopSection
        else:
            continue

#%% Test File
base_path = Path.cwd()

test_file_path = r'..\Testing\Test Data\Text Files'
test_file = base_path / test_file_path / 'PlanSum vs Original.dvh'
#test_file = Path.cwd() / 'PlanSum vs Original.dvh'


#%% Main Iteration
with open(test_file, newline='') as csvfile:
    raw_lines = LineIterator(csvfile)
    context = {
        'File Name': test_file.name,
        'File Path': test_file.parent,
        'Line Count': 0,
        'Source': raw_lines
        }
    dvh_info_break = SectionBreak(TextTrigger(['Plan', 'Plan sum']), 
                                   name='dvh_info')
    section_lines = scan_section(context, section_name = 'DVH Info',
                                 break_triggers = [dvh_info_break])
    pprint(section_lines)
    plan_info_break = SectionBreak(TextTrigger(['% for dose (%):']), 
                                   offset='After', 
                                   name='plan_info')
    plan_data_break = SectionBreak(TextTrigger(['Structure']), 
                                   offset='Before', 
                                   name='plan_data')
    section_lines = scan_section(context, section_name = 'Plan Info',
                                 break_triggers = [plan_info_break,                                                            
                                                   plan_data_break])
    pprint(section_lines)
print('done')

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
from data_utilities import true_iterable
import logging_tools as lg


#%% Logging
logger = lg.config_logger(prefix='read_dvh.file', level='INFO')


#%% Exceptions
class TextReadException(Exception): pass


class StopSection(TextReadException):
    '''A Section has ended through activation of a trigger.
    '''
    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context

    def get_context(self):
        return self.context


class EOF(TextReadException):
    '''A Section has ended through reaching the end of the source.
    '''
    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context

    def get_context(self):
        return self.context


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


class Trigger():
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
    def __init__(self, sentinel: List[str], name='TextTrigger'):
        '''Define Text strings that signal a trigger event.
        sentinel
        '''
        self.sentinel = sentinel
        self.name = name

    def apply(self, context: Dict[str, any], line: str)->(bool, str):
        logger.debug('in apply trigger')
        for sentinel_string in self.sentinel:
            if sentinel_string in line:
                logger.debug(f'Triggered on {sentinel_string}')
                return True,  sentinel_string
        return False, None


class Trigger():
    '''
     Trigger Types:
       Regex

     If Regex the re.match object will be ??? added to the Context dict.

     ???Triggers can be chained for "AND" operations.
     If n skip n lines then trigger
     If Repeating sub-sections, can be number of repetitions
     '''
    def __init__(self, sentinel: re.Pattern, name='ReTrigger'):
        '''Define a regular expression that signal a trigger event.
        sentinel
        '''
        self.sentinel = sentinel
        self.name = name

    def apply(self, context: Dict[str, any], line: str)->(bool, str):
        logger.debug('in apply trigger')
        sentinel_match = self.sentinel.search(line)
        if sentinel_match is not None:
            logger.debug(f'Triggered on {self.name}')
            return True,  sentinel_match
        return False, None

class Trigger():
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
    def __init__(self, sentinel, name='TextTrigger'):
        '''Define Text strings that signal a trigger event.
        sentinel  : List[str], : re.Pattern
        '''
        self.sentinel = sentinel
        self.name = name
        self.sentinel_type = None
        self.test = None
        self.sentinel_type_test()

    def sentinel_type_test(self):
        if isinstance(self.sentinel, re.Pattern):
            self.sentinel_type = 'RE'
            self.test = self.re_test
        elif true_iterable(self.sentinel):
            if all(isinstance(snt, str) for snt in self.sentinel):
                self.sentinel_type = 'List[str]'
                self.test = self.list_str_test
        elif isinstance(self.sentinel, str):
            self.sentinel_type = 'string'
            self.test = self.str_test
        else:
            self.sentinel_type = None
            self.test = None

    def list_str_test(self, line: str)->(bool, str):
        for sentinel_string in self.sentinel:
            if sentinel_string in line:
                logger.debug(f'Triggered on {sentinel_string}')
                return True, sentinel_string
        return False, None

    def str_test(self, line: str)->(bool, str):
        if sentinel_string in line:
            logger.debug(f'Triggered on {sentinel_string}')
            return True, sentinel_string
        return False, None

    def re_test(self, line: str)->(bool, re.Match):
        sentinel_match = self.sentinel.search(line)
        if sentinel_match is not None:
            logger.debug(f'Triggered on {self.name}')
            return True,  sentinel_match
        return False, None

    def apply(self, context: Dict[str, any], line: str):
        logger.debug('in apply trigger')
        if self.test:
            is_pass, sentinel_output = self.test(line)
        else:
            is_pass = False
            sentinel_output = None
        return is_pass, sentinel_output


class SectionBreak():
    def __init__(self, trigger: Trigger,
                 offset='Before', name='SectionBreak'):
        '''
        starting_offset	[Int or str] if str, one of Before or After
        if -1 or 'Before', Save the line that activates the Trigger for next section.
        if 0 or 'After', Include the line that activates the Trigger in the section.
        '''
        self.name = name
        self.trigger = trigger
        self.offset = self.get_offset(offset)

        self.count_down = None
        self.active_sentinel = None

    @staticmethod
    def get_offset(offset):
        '''Calculate the appropriate step_back value to store.
        Before is a step back of -1
        After is a step back of 0.
        '''
        offset_value = None
        try:
            offset_value = int(offset)
        except ValueError as err:
            if isinstance(offset, str):
                if 'Before' in offset:
                    offset_value = -1
                elif 'After' in offset:
                    offset_value = 0
            else:
                raise err('Offset must be an integer or one of'
                          '"Before" or "After";\t Got {repr(offset)}')
        return offset_value

    def check(self, context: Dict[str, any], line: str):
        '''Check for a Break condition
        If an Active count down situation exists, continue the count down.
        Otherwise, apply the trigger test.
        If the Trigger signals a break, set the appropriate line location for
        the break based on the offset value.
        '''
        logger.debug('in section_break.check')
        if self.count_down is None:  # No Active Count Down
            is_break, sentinel = self.trigger.apply(context, line)
            if is_break:
                is_break, context = self.set_line_location(context,
                                                           is_break, sentinel)
        elif self.count_down == 0:  # End of Count Down Reached
            logger.debug(f'Line count down in {self.name} completed.')
            self.count_down = None  # Remove Active Count Down
            is_break = True
            context['Source'].step_back = 1  # Save current line for next section
            context['sentinel'] = self.active_sentinel
        elif self.count_down > 0:  #  Active Count Down Exists
            logger.debug(f'Line count down in {self.name} Continuing;\t'
                         f'Count down now at {self.count_down}')
            self.count_down -= 1   #  Continue Count Down
            is_break = False
            sentinel = self.active_sentinel
        return is_break, context

    def set_line_location(self, context, is_break, sentinel):
        '''Set the appropriate line location for a break based on the offset
        value.
        '''
        logger.debug(f'Break triggered by {sentinel}')
        self.active_sentinel = sentinel
        if self.offset < 0: # Save current line for next section
            logger.debug(f'Stepping back {-self.offset} lines')
            context['sentinel'] = sentinel
            context['Source'].step_back = -self.offset
        else: # Use more lines before activating break
            logger.debug(f'Using {self.offset} more lines.')
            self.count_down = self.offset  # Begin Active Count Down
            is_break = False
        return is_break, context


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
def break_iterator(source, context, break_triggers: List[SectionBreak]):
    logger.debug('In break_iterator')
    for line in source:
        logger.debug(f'In section_breaks, received line: {line}')
        for break_trigger in break_triggers:
            logger.debug(f'Checking Trigger: {break_trigger.name}')
            is_break, context = break_trigger.check(context, line)
            if is_break:
                logger.debug(f'Section Break Detected')
                raise StopSection(context=context)
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
    Trigger(['Prescribed dose'])
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


def prescribed_dose_parse():
    pass

def plan_status_parse():
    pass

def merge_rows():
    pass

def drop_blanks():
    pass

def date_processing():
    pass

def number_processing():
    pass


def scan_section(context, section_name, break_triggers: List[SectionBreak]):
# Apply Section Cleaning -> clean_lines
# Check for End of Section Break -> break_triggers

# Call Line Parser, passing Context & Lines -> Dialect, Special Lines

# Apply Line Processing Rules -> trim_lines

# Apply Section Formatting ->
    context['Current Section'] = section_name
    logger.debug(f'Starting New Section: {section_name}.')
    cleaned_lines = clean_lines(context['Source'])
    active_lines = break_iterator(cleaned_lines, context, break_triggers)
    csvreader = csv.reader(active_lines, delimiter=':', quotechar='"')
    trimmed_lined = trim_lines(csvreader)

    # Section iterator
    section_lines = list()
    while True:
        row = None
        try:
            row = trimmed_lined.__next__()
        except StopSection as stop_sign:
            #pprint(stop_sign)
            print()
            logger.debug('end of the section')
            break
        except EOF as eof:
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
        SectionBreak(Trigger(['Plan:', 'Plan sum:']),name='dvh_info')
        ]

    plan_info_break = [
        SectionBreak(Trigger(['% for dose (%):']), offset='After',
                     name='End of Plan Info')
        ]

    plan_data_break = [
        SectionBreak(Trigger(['Structure:']), offset='Before',
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
        raw_lines = LineIterator(csvfile)
        context = {
            'File Name': test_file.name,
            'File Path': test_file.parent,
            'Line Count': 0,
            'Source': raw_lines
            }
        context, section_lines = section_manager(context)
    return context, section_lines


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

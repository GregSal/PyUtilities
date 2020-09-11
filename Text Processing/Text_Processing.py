'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string

#%% Imports
from collections import deque
from typing import Dict
from typing import Dict
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
     If n skip n lines then trigger
     If Repeating sub-sections, can be number of repetitions
     '''

    def __init__(self, sentinel, name='TextTrigger', location='IN'):
        '''Define Text strings that signal a trigger event.
        sentinel: {str|re.Pattern|Tuple[str],Tuple[re.Pattern}
        location: 'IN', 'START', 'END', 'FULL'
        if sentinel is a string type:
            location == 'IN' -> sentinel in line,
            location == 'START' -> line.startswith(sentinel), in line,
            location == 'END' -> line.endswith(sentinel),
            location == 'FULL' -> sentinel == line.
        if sentinel is a Regular Expression type:
            location == 'IN' -> sentinel.search(line),
            location == 'START' -> sentinel.match(line),
            location == 'FULL' -> sentinel.fullmatch(line),
            location == 'END' -> raise NotImplementedError.

        '''
        self.sentinel = sentinel
        self.location = location
        self.name = name
        self.sentinel_type = None
        self.test_method = None
        self.test_type = None
        self.test = None
        self.set_sentinel_type_test()

    # Define the return values for a given sentinel type
    def str_test(self, line: str, sentinel_string: str)->(bool, str):
        test_result = self.test_method(sentinel_string, line)
        if test_result:
            logger.debug(f'Triggered on {sentinel_string}')
            return True, sentinel_string
        return False, None

    def re_test(self, line: str, pattern: re.Pattern)->(bool, re.Match):
        sentinel_match = self.test_method(pattern, line)
        if sentinel_match is not None:
            logger.debug(f'Triggered on {sentinel_match.string}')
            return True,  sentinel_match
        return False, None

    # Optional applications of multiple patterns / strings in one trigger
    def multi_test(self, context, line: str)->(bool, str):
        for sentinel_item in self.sentinel:
            test_result, test_value = self.test_type(line, sentinel_item)
            if test_result:
                return test_result, test_value
        return False, None

    def single_test(self, context, line: str) -> (bool, str):
        return self.test_type(line, self.sentinel)

    # Set the required test function
    def set_sentinel_test_location(self):
        '''Set test based on sentinel type and location.
        if sentinel is a string type:
            location == 'IN' -> sentinel in line,
            location == 'START' -> line.startswith(sentinel), in line,
            location == 'END' -> line.endswith(sentinel),
            location == 'FULL' -> sentinel == line.
        if sentinel is a Regular Expression type:
            location == 'IN' -> sentinel.search(line),
            location == 'START' -> sentinel.match(line),
            location == 'FULL' -> sentinel.fullmatch(line),
            location == 'END' -> raise NotImplementedError.
        '''
        if self.sentinel_type == 'String':
            if self.location == 'IN':
                self.test_method = lambda sentinel, line: sentinel in line
            elif self.location == 'START':
                self.test_method = lambda sentinel, line: line.startswith(sentinel)
            elif self.location == 'END':
                self.test_method = lambda sentinel, line: line.endswith(sentinel)
            elif self.location == 'FULL':
                self.test_method = lambda sentinel, line: sentinel == line
        elif self.sentinel_type == 'RE':
            if self.location == 'IN':
                self.test_method = lambda sentinel, line: sentinel.search(line)
            elif self.location == 'START':
                self.test_method = lambda sentinel, line: sentinel.match(line)
            elif self.location == 'FULL':
                self.test_method = lambda sentinel, line: sentinel.fullmatch(line)
            elif self.location == 'END':
                raise NotImplementedError('The location "END" is not'
                                          'compatible with a regular '
                                          'expression test.')
        else:
            self.test_method = None

    def set_sentinel_type_test(self):
        if self.sentinel is None:
            self.sentinel_type = 'None'
            self.test_type = None
            self.test = None
        elif true_iterable(self.sentinel):
            if all(isinstance(snt, str) for snt in self.sentinel):
                self.sentinel_type = 'String'
                self.test_type = self.str_test
                self.test = self.multi_test
            elif all(isinstance(snt, re.Pattern) for snt in self.sentinel):
                self.sentinel_type = 'RE'
                self.test_type = self.re_test
                self.test = self.multi_test
            else:
                raise NotImplementedError(
                    'Only String and Regular Expression tests are currently '
                    'supported.'
                    )
        elif isinstance(self.sentinel, str):
            self.sentinel_type = 'String'
            self.test_type = self.str_test
            self.test = self.single_test
        elif isinstance(self.sentinel, re.Pattern):
            self.sentinel_type = 'RE'
            self.test_type = self.re_test
            self.test = self.single_test
        else:
            raise NotImplementedError(
                'Only String and Regular Expression tests are currently '
                'supported.'
                )
        self.set_sentinel_test_location()

    # Apply the defined test and return the results
    def apply(self, context: Dict[str, any], line: str):
        logger.debug('in apply trigger')
        if self.test is None:
            is_pass = False
            sentinel_output = None
        else:
            is_pass, sentinel_output = self.test(context, line)
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


'''Classes and functions used for reading and parsing text files.

Leave one blank line.  The rest of this docstring should contain an
overall description of the module or program.  Optionally, it may also
contain a brief description of exported classes and functions and/or usage
examples.

  Typical usage example:

  foo = ClassFoo()
  bar = foo.FunctionBar()
'''
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=logging-fstring-interpolation
#%% Imports
import re
import csv
from inspect import isgeneratorfunction
from functools import partial
from typing import Dict, List, Sequence, TypeVar, Iterator, Any, Callable, Union

from file_utilities import clean_ascii_text
from data_utilities import true_iterable
import logging_tools as lg

from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorValueError
from buffered_iterator import BufferOverflowWarning
from buffered_iterator import BufferedIteratorEOF
T = TypeVar('T')

Strings = Union[str, List[str]]
OptStrings = Union[Strings, None]
OptStr = Union[str, None]
AlphaNumeric = Union[float, str]
ParseResults = Union[List[List[str]], None]

# TODO create type definitions: Line, ParsedLine ...
#%% Logging
logger = lg.config_logger(prefix='read_dvh.file', level='DEBUG')


#%% Exceptions
class TextReadWarnings(UserWarning): pass


class TextReadException(Exception): pass


class StopSection(TextReadException):
    '''A Section has ended through activation of a trigger.'''

    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = context

    def get_context(self):
        '''Return the context that existed when StopSection was raised.'''
        return self.context


#%% String Functions
# These functions act on a string or list of strings.
# They are often applied to a generator using partial.

def join_strings(text1: Strings, text2: OptStr = None, join_char=' ') -> str:
    '''Join text2 to the end of text1 using join_char.

    If text1 is a list of strings they will be joined together and text2, if
    present, will be joind to the end of the resulting string.

    Args:
        text1: first string or list of strings to be joined.
        text2: Optional second string.
        join_char: Optional character to place between strings.
            Default is no character.
    Returns:
        The string reulting from joining text1 and text2.
    '''
    if true_iterable(text1):
        if text2 is None:
            text_list = text1
        else:
            text_list = text1.append(text2)
    else:
        text_list = [text1, text2]
    return join_char.join(text_list)


def str2float(text: str) -> AlphaNumeric:
    '''Convert a text number to float.

    If text is not a valid number return the original text.

    Args:
        text: The string to be converted.

    Returns:
        Either the float value represented by text or the original text.
    '''
    return_value = text
    try:
        return_value = float(text)
    except ValueError:
        pass
    return return_value


#%% Iteration Tools
def func_to_iter(source: Iterator, func: Callable) -> Iterator:
    '''Create a iterator that applies func to each item in source.

    If func is a generator fuction, return the iterator creates by calling
    func with source.  otherwise use a generator expression to return an
    iterator that returns the result of calling func on each item in source.
    No type checking is performed.

    Args:
        source: An iterator that returns the apropriate data types for func.
        func: A function or generator that takes one argument with type
            compatible to that produced by source.   If func is a generator
            function its argument must be an iterator with type
            compatible to that produced by source.

    Returns:
        An iterator that returns the result of calling func on each item in
        source. For example:
    '''
    if isgeneratorfunction(func):
        return func(source)
    return (func(item) for item in source)


def cascading_iterators(source: Iterator, func_list: List[Callable])->Iterator:
    '''Creates a sequence of nested iterator, taking as input the ouput from
    the previous ietrator.

    Calls func_to_iter to create each nested iterator.

    Args:
        source: An iterator that returns the apropriate data types for the
            first function in func.
        func_list: A list of functions or generators that takes one argument.
            The functions do not nessesarily all take the same data type, but
            the input type for each function muct be compatible with the output
            type of the previous function in the sequence. The first function
            in the sequence must be compatible with that produced by source.

    Returns:
        An iterator that returns the result of successivly calling each
        function in func_list on the output of the previous function.
        For example:
            def ml(x): return x*10
            def dv(x): return x/5
            def skip_odd(num_list):
                for i in num_list:
                    if i%2 == 0:
                        yield i
            source = range(5)
            a = tp.cascading_iterators(source, [skip_odd, ml, dv])
            [i for i in a] -> [0.0, 4.0, 8.0]
    Raises:
    '''
    next_source = source
    for func in func_list:
        next_source = func_to_iter(next_source, func)
    return iter(next_source)


# CSV parser
def csv_parser(line: str, *args, dialect_name='excel',
               **kwargs) -> ParseResults:
    '''Convert a single text line into one or more rows of parsed text.

    Uses the pre-defined csv Dialect for the line parsing rules.

    Args:
        line: A text string for parsing.
        dialect_name: the name of the pre-defined csv Dialect to be used for
            parsing.
        *args: Place holder for positional arguments to maintain compatibility
            for all parsing methods.
        **kwargs: Place holder for keyword arguments to maintain compatibility
            for all parsing methods.

    Returns:
        A list of lists of strings obtained by parsing line.
        For example:
            csv_parser('Part 1,"Part 2a, Part 2b"') ->
                [['Part 1', 'Part 2a, Part 2b']]
    '''
    csv_iter = csv.reader([line], dialect_name)
    parsed_lines = [row for row in csv_iter]
    return parsed_lines


def define_csv_parser(name='csv', **dialect_parameters) -> Callable:
    '''Create a function that applies the defined csv parsing rules.

    Create a unique csv parsing Dialect refered to by name. Use the partial
    method to create and return a function that applies the defines parsing
    rules to a string.

    Args:
        name: Optional, The name for the new Dialect. Defauly is 'csv'.
        **dialect_parameters: Any valid csv reader parameter.
            default values are:
                delimiter=',',
                doublequote=True,
                quoting=csv.QUOTE_MINIMAL,
                quotechar='"',
                escapechar=None,
                lineterminator='\r\n',
                skipinitialspace=False,
                strict=False
            See documentation on the csv module for explanatiojns of these
            parameters.

    Returns:
        A csv parser method.  For example:
            default_parser = define_csv_parser(name='Default csv')
            default_parser('Part 1,"Part 2a, Part 2b"') ->
                [['Part 1', 'Part 2a, Part 2b']]
    '''
    parameters = dict(
        delimiter=',',
        doublequote=True,
        quoting=csv.QUOTE_MINIMAL,
        quotechar='"',
        escapechar=None,
        lineterminator='\r\n',
        skipinitialspace=False,
        strict=False
        )
    parameters.update(dialect_parameters)
    csv.register_dialect(name, **parameters)
    parse_csv = partial(csv_parser, dialect_name=name)
    return parse_csv


#%% Parsed Line Iterators
# These functions take a sequence of lists of strings and return a generator.
def merge_continued_rows(parsed_lines: Sequence[List[str]],
                         max_lines=5) -> Iterator[List[str]]:
    '''If a parsed line has 2 items, and the next parsed line has only 1 item;
        join the next parsed line item to the end of the second item in the
        current line with " ".

    If func is a generator fuction, return the iterator creates by calling
    func with source.  otherwise use a generator expression to return an
    iterator that returns the result of calling func on each item in source.
    No type checking is performed.

    Args:
        source: An iterator that returns the apropriate data types for func.
        func: A function or generator that takes one argument with type
            compatible to that produced by source.   If func is a generator
            function its argument must be an iterator with type
            compatible to that produced by source.

    Returns:
        An iterator that returns the result of calling func on each item in
        source. For example:

    Raises:
        '''

    parsed_line_iter = BufferedIterator(parsed_lines, buffer_size=max_lines)
    for parsed_line in parsed_line_iter:
        completed_line = False
        completed_section = None  # Stores raised StopSection exceptions
        if len(parsed_line) != 2:
            completed_line = True
        while not completed_line:
            # Trap Section breaks so that the current line is returned before
            # the section break is raised
            try:
                next_line = parsed_line_iter.look_ahead()
            except (StopSection, BufferOverflowWarning) as eol:
                completed_line = True
                completed_section = eol
            else:
                if len(next_line) == 1:
                    parsed_line[1] = join_strings(parsed_line[1], next_line[0],
                                                  join_char=' ')
                    parsed_line_iter.skip()
                else:
                    completed_line = True
        yield parsed_line
        if completed_section:
            # If StopSection was raised by look_ahead, re-raise it after
            # yielding the current line.
            raise completed_section


def drop_units(text: str) -> float:
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
# Units to recognize:
# %, CU, cGy, Gy, deg, cm, deg, MU, min, cc, cm3, MU/Gy, MU/min, cm3, cc

#%% output converters
# These functions take a sequence of lists and return a the desired output
#    format.
def to_dict(processed_lines: Sequence[List[str]],
            default_value: Any = None,
            multi_value: Callable = None,
            dict_type: type = dict) -> Dict[str, Any]:
    '''Build a dictionary from a sequence of length 2 lists.
        default_value: Any -- Value to use if len(List) = 1
        multi_value: Callable -- Method to apply if is len(List) > 2
            If None, that List item is Dropped.
        dict_output: type, the type of dictionary to build e.g. ordered_dict.
        '''
    dict_output = dict_type()
    for dict_line in processed_lines:
        if len(dict_line) == 0:
            continue
        if len(dict_line) == 1:
            dict_item = {dict_line[0]: default_value}
        elif len(dict_line) == 2:
            dict_item = {dict_line[0]: dict_line[1]}
        elif multi_value:
            dict_item = multi_value(dict_line)
        else:
            continue
        dict_output.update(dict_item)
    return dict_output

#%% Parsed Line processors
# These functions take a list of strings and a processed list of strings.
def trim_items(parsed_line: List[str]) -> List[str]:
    '''Strip leading and training spaces from each item in the list of strings.
    '''
    try:
        trimed_line = [item.strip() for item in parsed_line]
    except AttributeError:
        trimed_line = parsed_line
    return trimed_line

def convert_numbers(parsed_line: List[str]) -> List[str]:
    '''If an item on a line is a number, convert it to a float.
    '''
    converted_line = [str2float(item) for item in parsed_line]
    return converted_line


def merge_extra_items(parsed_line: List[str]) -> List[str]:
    '''If a parsed line has more than 2 items, join items 2 to n. with " ". '''
    if len(parsed_line) > 2:
        merged = join_strings(parsed_line[1:])
        parsed_line[1] = merged
    return parsed_line

#def convert_numbers(parsed_lines: Sequence[List[str]]) -> Iterator[List[str]]:
#    '''If an item on a line is a number, convert it to a float.
#    '''
#    for parsed_line in parsed_lines:
#        converted_line = [str2float(item) for item in parsed_line]
#        yield converted_line


#def trim_lines(parsed_lines: Sequence[List[str]]) -> Iterator[List[str]]:
#    '''Strip leading and training spaces from each item in the list of strings.
#    '''
#    return (trim_items(parsed_line) for parsed_line in parsed_lines)


#def merge_extra_items(parsed_lines: Sequence[List[str]]) -> Iterator[List[str]]:
#    '''If a parsed line has more than 2 items, join items 2 to n. with " ". '''
#    for parsed_line in parsed_lines:
#        if len(parsed_line) > 2:
#            merged = join_strings(parsed_line[1:])
#            parsed_line[1] = merged
#        yield parsed_line

#%% String Iterators
# These functions take a sequence of strings and return a string generator.
def clean_lines(lines: Sequence[str]) -> Iterator[str]:
    '''Convert each string to ANSI text converting specified
    UTF-Characters to ANSI Equivalents
    '''
    for raw_line in lines:
        logger.debug(f'In clean_lines, yielding raw_line: {raw_line}')
        yield clean_ascii_text(raw_line)


def drop_blanks(lines: Sequence[str]) -> Iterator[str]:
    # TODO lines can also be parsed lines i.e. List[List[str]]
    '''Return all non-empty strings. or non-empty lists
    '''
    return (line for line in lines if len(line) > 0)


#%% Classes
class Trigger():
    '''
     Trigger Types:
     None
     bool
     List[str]
     Regex
     Callable
     n
     If None, the test will never pass
     If bool, the test will always return the boolean value
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
    def str_test(self, line: str, sentinel_string: str) -> (bool, str):
        test_result = self.test_method(sentinel_string, line)
        if test_result:
            logger.debug(f'Triggered on {sentinel_string}')
            return True, sentinel_string
        return False, None

    def re_test(self, line: str, pattern: re.Pattern) -> (bool, re.Match):
        sentinel_match = self.test_method(pattern, line)
        if sentinel_match is not None:
            logger.debug(f'Triggered on {sentinel_match.string}')
            return True, sentinel_match
        return False, None

    def fixed_test(self, line: str, test_result: bool) -> (bool, bool):
        '''Always return the boolean test_result regardless of line content.
        '''
        # pylint: disable=unused-argument
        return self.sentinel, self.sentinel

    # Optional applications of multiple patterns / strings in one trigger
    def multi_test(self, line, context) -> (bool, str):
        # pylint: disable=unused-argument
        for sentinel_item in self.sentinel:
            test_result, test_value = self.test_type(line, sentinel_item)
            if test_result:
                return test_result, test_value
        return False, None

    def single_test(self, line, context) -> (bool, str):
        # pylint: disable=unused-argument
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
        elif isinstance(self.sentinel, bool):
            self.sentinel_type = 'Boolean'
            self.test_type = self.fixed_test
            self.test = self.single_test
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
                raise NotImplementedError('Only String and Regular Expression'
                                          'tests are currently supported.')
        elif isinstance(self.sentinel, str):
            self.sentinel_type = 'String'
            self.test_type = self.str_test
            self.test = self.single_test
        elif isinstance(self.sentinel, re.Pattern):
            self.sentinel_type = 'RE'
            self.test_type = self.re_test
            self.test = self.single_test
        else:
            raise NotImplementedError('Only String and Regular Expression '
                                      'tests are currently supported.')
        self.set_sentinel_test_location()

    # Apply the defined test and return the results
    def apply(self, line, context=None):
        logger.debug('in apply trigger')
        if self.test is None:
            is_pass = False
            sentinel_output = None
        else:
            is_pass, sentinel_output = self.test(line, context)
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
    def get_offset(offset) -> int:
        '''Calculate the appropriate step_back value to store.
        Before is a step back of -1
        After is a step back of 0.
        '''
        offset_value = 0
        try:
            offset_value = int(offset)
        except ValueError as err:
            if isinstance(offset, str):
                if 'Before' in offset:
                    offset_value = -1
                elif 'After' in offset:
                    offset_value = 0
            else:
                msg = ('Offset must be an integer or one of'
                       '"Before" or "After";\t Got {repr(offset)}')
                raise ValueError(msg) from err
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


class Rule():
    @staticmethod
    def always_trigger(test_object, *args, **kwargs):
        return True, test_object

    @staticmethod
    def default_template(test_object, sentinel, *args,
                         default_return=None, **kwargs):
        '''default_method to be set using partial.
        '''
        if 'Original' in default_return:
            return test_object
        if 'Sentinel' in default_return:
            return sentinel
        if 'None' in default_return:
            return None
        return None

    def __init__(self, trigger: Trigger = None,
                 pass_method: Callable = None,
                 fail_method: Callable = None,
                 default='None',
                 name='Rule'):
        '''Apply method based on trigger result.
        pass_method, fail_method: Callable, takes 3 arguments:
            test_object
            sentinel
            context
        default_method: str, one of:
            'None'  -> returns None
            'Original' -> returns test_object
            'Sentinel' -> returns sentinel
        '''
        self.name = name
        self.trigger = trigger
        default_method = partial(self.default_template,
                                 default_return=default)
        if pass_method:
            self.pass_method = pass_method
        else:
            self.pass_method = default_method

        if fail_method:
            self.fail_method = fail_method
        else:
            self.fail_method = default_method


    def apply(self, test_object, *args, **kwargs):
        is_match, sentinel = self.trigger.apply(test_object, *args, **kwargs)
        if is_match:
            result = self.pass_method(test_object, sentinel, *args, **kwargs)
        else:
            result = self.fail_method(test_object, sentinel, *args, **kwargs)
        return result


class LineParser():
    def __init__(self, parsing_rules: List[Rule],
                 default_parser: Callable = None):
        self.parsing_rules = parsing_rules
        default_rule = Rule(Rule.always_trigger, default_parser,
                            name='Default')
        self.parsing_rules.append(default_rule)

    def parser(self, source, context):
        logger.debug('In line_parser')
        for line in source:
            logger.debug(f'In line_parser, received line: {line}')

            for rule in self.parsing_rules:
                parsed_lines = rule.apply(line, context)
                if parsed_lines is not None:
                    break

            if parsed_lines is not None:
                for parsed_line in parsed_lines:
                    yield parsed_line


class Section():
    def __init__(self,
                 section_name,
                 preprocessing,
                 break_rules: List[SectionBreak],
                 parsing_rules,
                 processed_lines,
                 output_method):
        self.section_name = section_name
        self.preprocessing = preprocessing
        self.break_rules = break_rules
        self.parsing_rules = parsing_rules
        self.processed_lines = processed_lines
        self.output_method = output_method

    def scan_section(self, context):
        # Apply Section Cleaning -> clean_lines
        # Check for End of Section Break -> break_triggers
        # Call Line Parser, passing Context & Lines -> Dialect, Special Lines
        # Apply Line Processing Rules -> trim_lines
        # Apply Section Formatting ->

        context['Current Section'] = self.section_name
        logger.debug(f'Starting New Section: {self.section_name}.')
        cleaned_lines = cascading_iterators(context['Source'],
                                            self.preprocessing)
        active_lines = self.break_iterator(context, cleaned_lines)
        parsed_lines = self.line_parser(context, active_lines)
        processed_lines = cascading_iterators(iter(parsed_lines),
                                              self.processed_lines)

        section_output = self.output_method(self.section_iter(processed_lines))
        return section_output

    def section_iter(self, source):
        while True:
            row = None
            try:
                row = source.__next__()
            except StopSection as stop_sign:
                logger.debug('end of the section')
                break
            except BufferedIteratorEOF as eof:
                logger.debug('End of Source')
                break
            logger.debug(f'Found row: {row}.')
            if row is not None:
                yield row
            logger.debug('next line')

    def break_iterator(self, context, source):
        logger.debug('In break_iterator')
        for line in source:
            logger.debug(f'In section_breaks, received line: {line}')
            for break_rule in self.break_rules:
                logger.debug(f'Checking Trigger: {break_rule.name}')
                is_break, context = break_rule.check(context, line)
                if is_break:
                    logger.debug('Section Break Detected')
                    raise StopSection(context=context)
            logger.debug('No Break Triggered')
            yield line
        raise StopSection(context=context)



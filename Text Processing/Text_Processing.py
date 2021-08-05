'''Classes and functions used for reading and parsing text files.

Leave one blank line.  The rest of this docstring should contain an
overall description of the module or program.  Optionally, it may also
contain a brief description of exported classes and functions and/or usage
examples.

  Typical usage example:

  foo = ClassFoo()
  bar = foo.FunctionBar()
'''
from __future__ import annotations
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=logging-fstring-interpolation
#%% Imports
import re
import csv
import inspect
from pathlib import Path
from inspect import isgeneratorfunction
from functools import partial
from typing import Dict, List, Sequence, Tuple, TypeVar, Iterator
from typing import Iterable, Any, Callable, Union, Generator

import pandas as pd

from data_utilities import true_iterable
import logging_tools as lg

from buffered_iterator import BufferedIterator
from buffered_iterator import BufferOverflowWarning
from buffered_iterator import BufferedIteratorEOF
T = TypeVar('T')
# TODO create more type definitions: Line, ...
# TODO more explicit generic type definitions
# TODO Move generic functions to separate module
# TODO copy clean_ascii_text from file_utilities
# TODO copy true_iterable from data_utilities
# Move the major classes:  Section, SectionReader, SectionBreak, ParsingRule,
# Trigger to a separate Module
'''
    Trigger Types:
    None
    bool
    List[str]
    Regex
    Callable   -- Not Yet Implemented
    n          -- Not Yet Implemented
    If None, the test will never pass
    If bool, the test will always return the boolean value
    If list of strings, a match with any string in the list will be a pass
    The matched string will be added to the Context dict.
    If Regex the re.match object will be added to the Context dict.
    If Callable, a non-None return value will be a pass -- Not Yet Implemented
    The return value will be added to the Context dict.
    If n skip n lines then trigger                      -- Not Yet Implemented
    If Repeating sub-sections, can be number of repetitions
    '''
ParsedString = List[str]
Strings = Union[str, ParsedString]
OptStrings = Union[Strings, None]
OptStr = Union[str, None]
AlphaNumeric = Union[float, str]
Integers = Union[int, List[int]]

ParseResults = Union[List[ParsedString], None]

StringSource = Union[Iterator[str], Sequence[str]]
ParsedStringSource = Union[Iterator[ParsedString], Sequence[ParsedString]]
Source = Union[StringSource, ParsedStringSource]


# These type definitions will be redefined as class types.  They are defined
# here to simplify Type annotations.
Section = TypeVar('Section')  # pylint: disable=function-redefined
SectionBreak = TypeVar('SectionBreak')  # pylint: disable=function-redefined
SectionProcessor = TypeVar('SectionProcessor')  # pylint: disable=function-redefined
SectionProcessor = TypeVar('SectionProcessor')  # pylint: disable=function-redefined

# Relevant Type definitions for Section Classes
BreakOptions = Union[SectionBreak, List[SectionBreak], str, None]
ProcessorOptions = Union[SectionProcessor, Section, List[Section]]

#%% Logging
logger = lg.config_logger(prefix='Text Processing', level='DEBUG')


#%% String Functions
# These functions act on a string or list of strings.
# They are often applied to a generator using partial.

def join_strings(text1: Strings, text2: OptStr = None, join_char=' ') -> str:
    '''Join text2 to the end of text1 using join_char.

    If text1 is a list of strings they will be joined together and text2, if
    present, will be joined to the end of the resulting string.

    Args:
        text1: first string or list of strings to be joined.
        text2: Optional second string.
        join_char: Optional character to place between strings.
            Default is no character.
    Returns:
        The string resulting from joining text1 and text2.
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


def convert_numbers(parsed_line: ParsedString) -> ParsedString:
    '''If an item on a line is a number, convert it to a float.
    '''
    converted_line = [str2float(item) for item in parsed_line]
    return converted_line


def drop_units(text: str) -> float:
    number_value_pattern = (
        r'^'                # beginning of string
        r'\s*'              # Skip leading whitespace
        r'(?P<value>'       # beginning of value integer group
        r'[-+]?'            # initial sign
        r'\d+'              # float value before decimal
        r'[.]?'             # decimal Place
        r'\d*'              # float value after decimal
        r')'                # end of value string group
        r'\s*'              # skip whitespace
        r'(?P<unit>'        # beginning of value integer group
        r'[^\s]*'           # units do not contain spaces
        r')'                # end of unit string group
        r'\s*'              # drop trailing whitespace
        r'$'                # end of string
        )
    # Units to recognize:
    # %, CU, cGy, Gy, deg, cm, deg, MU, min, cc, cm3, MU/Gy, MU/min, cm3, cc
    #find_num = re.compile(number_value_pattern)
    find_num = re.findall(number_value_pattern, text)
    if find_num:
        value, unit = find_num[0]  # pylint: disable=unused-variable
        return value
    return text

#%% String Parsers
# CSV parser
def csv_parser(line: str, *args, dialect_name='excel',    # pylint: disable=unused-argument
               **kwargs) -> ParseResults:                 # pylint: disable=unused-argument
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

    Create a unique csv parsing Dialect referred to by name. Use the partial
    method to create and return a function that applies the defines parsing
    rules to a string.

    Args:
        name: Optional, The name for the new Dialect. Default is 'csv'.
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
            See documentation on the csv module for explanations of these
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

# Fixed Width Parser
class FixedWidthParser():
    def __init__(self, widths: Integers = None, number: int = 1,
                 locations: List[int] = None):
        '''Define a parser that will convert a single text line into parsed
        text items of fixed widths.

        number=n, width=w -> widths = [w]*n
        locations=[l1,l2,l3...] -> widths = [l1, l2-l1, l3-l2...]

        Args:
            line: A text string for parsing.
            widths: Optional A list of the widths of the successive items on a row.
                Alternatively a single integer width if all numbers items are of
                equal width.
            number: The number of items in a row if widths is a single integer.
                If widths is a list of integers number represents the number of
                times that the widths sequence is repeated.
            locations: A list of the locations of the item breaks in a row.
                If widths is given, then this value is ignored.
        '''
        if widths:
            if isinstance(widths, int):
                self.item_widths = [widths]*number
            else:
                self.item_widths = widths*number

        elif locations:
            self.item_widths = [
                l2-l1
                for l2, l1 in zip(locations,
                                  [0] + locations[:-1])
                ]
        else:
            self.item_widths = [None]

    def parse_iter(self, line):
        remainder = line
        for w in self.item_widths:
            if w is None:
                continue
            if len(remainder) < w:
                continue
            item = remainder[:w]
            remainder = remainder[w:]
            yield item
        if remainder:
            yield remainder

    def parser(self, line: str, *args, **kwargs) -> ParseResults:  # pylint: disable=unused-argument
        '''Convert a single text line into a single text line into parsed
        text items of fixed widths.

        Args:
            line: A text string for parsing.
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
        parsed_line = [item for item in self.parse_iter(line)]
        return [parsed_line]


def define_fixed_width_parser(widths: List[int] = None, number: int = 1,
                              locations: List[int] = None) -> Callable:
    '''Create a function that will convert a single text line into parsed
        text items of fixed widths.

        Args:
            line: A text string for parsing.
            widths: Optional A list of the widths of the successive items on a row.
                Alternatively a single integer width if all numbers items are of
                equal width.
            number: The number of items in a row if widths is a single integer.
                If widths is a list of integers number represents the number of
                times that the widths sequence is repeated.
                    number=n, width=w -> widths = [w]*n
            locations: A list of the locations of the item breaks in a row.
                If widths is given, then this value is ignored.
                    locations=[l1,l2,l3...] -> widths = [l1, l2-l1, l3-l2...]

    Returns:
        A csv parser method.  For example:
            default_parser = define_csv_parser(name='Default csv')
            default_parser('Part 1,"Part 2a, Part 2b"') ->
                [['Part 1', 'Part 2a, Part 2b']]
    '''
    parser_constructor = FixedWidthParser(widths, number, locations)
    return parser_constructor.parser


#%% Parsed Line Iterators
# These functions take a sequence of lists of strings and return a generator.
def merge_continued_rows(parsed_lines: ParsedStringSource,
                         max_lines=5, join_char=' ') -> ParsedStringSource:
    '''Join lines where the second item continues on the next line.

        If a parsed line has 2 items, and the next parsed line has only 1 item;
        join the next parsed line item to the end of the second item in the
        current line with " ". Treats a raised StopSection as an indicator that
        the line does not continue.

    Args:
        parsed_lines: A sequence or iterator resulting from applying parsing
            rules to multiple lines.
        max_lines:  The maximum number of lines that the second item can
            continue over.
        join_char: Optional character to place between strings.
            Default is ' ' (one space).

    Yields:
        An iterator that returns each ParsedLine, if the next line has 2 items,
            or, the result of joining the next parsed line item to the end of
            the second item in the current line with ". For example:
    '''
        #if completed_section:
        #    # If StopSection was raised by look_ahead, re-raise it after
        #    # yielding the current line.
        #    raise completed_section
    parsed_line_iter = BufferedIterator(parsed_lines, buffer_size=max_lines)
    for parsed_line in parsed_line_iter:
        completed_line = False
        # completed_section = None  # Stores raised StopSection exceptions
        # If the first line doesn't not have exactly 2 parts don't join
        # subsequent lines to it.
        if len(parsed_line) != 2:
            completed_line = True
        while not completed_line:
            # Trap Section breaks so that the current line is returned before
            # the section break is raised
            try:
                next_line = parsed_line_iter.look_ahead()
            except BufferOverflowWarning:
                completed_line = True
            else:
                if len(next_line) == 1:
                    parsed_line[1] = join_strings(parsed_line[1], next_line[0],
                                                  join_char)
                    parsed_line_iter.skip()
                else:
                    completed_line = True
        yield parsed_line


def drop_blanks(lines: Source) -> Source:
    '''Return all non-empty strings. or non-empty lists
    '''
    for line in lines:
        if any(len(text) for text in line) > 0:
            yield line


#%% output converters
# These functions take a sequence of lists and return a the desired output
#    format.
def to_dict(processed_lines: ParsedStringSource,
            default_value: Any = '',
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
        logger.debug(f'dict_line: {dict_line}.')
        if len(dict_line) == 0:
            continue
        elif len(dict_line) == 1:
            if default_value is None:
                continue
            else:
                dict_item = {dict_line[0]: default_value}
        elif len(dict_line) == 2:
            dict_item = {dict_line[0]: dict_line[1]}
        elif multi_value:
            dict_item = multi_value(dict_line)
        else:
            continue
        dict_output.update(dict_item)
    return dict_output

def to_dataframe(processed_lines: ParsedStringSource,
                 header=True) -> pd.DataFrame:
    '''Build a Pandas DataFrame from a sequence of lists.
        header: Bool or int if true or positive int, n, use the first 1 or n
            lines as column names.
    '''
    all_lines = [line for line in processed_lines if len(line) > 0]
    if header:
        header_index = int(header)  # int(True) = 1
        # TODO add ability to handle Multi Line headers
        header_lines = all_lines[:header_index][0]
        data = all_lines[header_index:]
        dataframe = pd.DataFrame(data, columns=header_lines)
    else:
        dataframe = pd.DataFrame(all_lines)
    return dataframe


#%% Parsed Line processors
# These functions take a list of strings and return a processed list of strings.
def trim_items(parsed_line: ParsedString) -> ParsedString:
    '''Strip leading and training spaces from each item in the list of strings.
    '''
    try:
        trimed_line = [item.strip() for item in parsed_line]
    except AttributeError:
        trimed_line = parsed_line
    return trimed_line


def merge_extra_items(parsed_line: ParsedString) -> ParsedString:
    '''If a parsed line has more than 2 items, join items 2 to n. with " ". '''
    if len(parsed_line) > 2:
        merged = join_strings(parsed_line[1:])
        parsed_line[1] = merged
    return parsed_line


#%% Iteration Tools
def file_reader(file_path: Path)->BufferedIterator:
    def file_line_gen(file_path):
        with open(file_path, newline='') as textfile:
            for line in textfile:
                yield line
    source = BufferedIterator(file_line_gen(file_path))
    return source


def func_to_iter(source: Iterator, func: Callable) -> Iterator:
    '''Create a iterator that applies func to each item in source.

    If func is a generator function, return the iterator creates by calling
    func with source.  Otherwise use a generator expression to return an
    iterator that returns the result of calling func on each item in source.
    No type checking is performed.

    Args:
        source: An iterator that returns the appropriate data types for func.
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
    '''Creates a sequence of nested iterator, taking as input the output from
    the previous iterator.

    Calls func_to_iter to create each nested iterator.

    Args:
        source: An iterator that returns the appropriate data types for the
            first function in func.
        func_list: A list of functions or generators that takes one argument.
            The functions do not necessarily all take the same data type, but
            the input type for each function must be compatible with the output
            type of the previous function in the sequence. The first function
            in the sequence must be compatible with that produced by source.

    Returns:
        An iterator that returns the result of successively calling each
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


#%% Section Classes
class Trigger():
    '''
     Trigger Types:
     None
     bool
     List[str]
     Regex
     Callable   -- Not Yet Implemented
     n          -- Not Yet Implemented
     If None, the test will never pass
     If bool, the test will always return the boolean value
     If list of strings, a match with any string in the list will be a pass
        The matched string will be added to the Context dict.
     If Regex the re.match object will be added to the Context dict.
     If Callable, a non-None return value will be a pass -- Not Yet Implemented
        The return value will be added to the Context dict.
     If n skip n lines then trigger                      -- Not Yet Implemented
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
                raise NotImplementedError('Only Boolean, String and '
                                          'Regular Expression '
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
            raise NotImplementedError('Only Boolean, String and '
                                      'Regular Expression '
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


class ParsingRule():
    @staticmethod
    def default_template(test_object, event, *args,    # pylint: disable=unused-argument
                         default_return=None, **kwargs):  # pylint: disable=unused-argument
        '''default_method to be set using partial.
        '''
        if 'Original' in default_return:
            return [test_object]
        if 'Event' in default_return:
            return event  # TODO The format for event should depend on its type
        if 'None' in default_return:
            return None
        # TODO Add option for Rule default method to be a blank line
        return None

    def __init__(self, trigger: Trigger = None,
                 pass_method: Callable = None,
                 fail_method: Callable = None,
                 default='None',
                 name='Rule'):
        '''Apply method based on trigger result.
        pass_method, fail_method: Callable, takes 3 arguments:
            test_object
            event
            context
        default_method: str, one of:
            'None'  -> returns None
            'Original' -> returns test_object
            'Event' -> returns Trigger event object
        '''
        self.name = name
        self.trigger = trigger
        # TODO in Rule __init__ get rid of default and have pass & fail methods check for string.
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
        is_match, event = self.trigger.apply(test_object, *args, **kwargs)
        if is_match:
            result = self.pass_method(test_object, event, *args, **kwargs)
        else:
            result = self.fail_method(test_object, event, *args, **kwargs)
        return result


class LineParser():  # TODO Convert this into RuleSet
    def __init__(self, parsing_rules: List[ParsingRule],
                 default_parser: Callable = None):
        self.parsing_rules = parsing_rules
        default_rule = ParsingRule(Trigger(True), default_parser, name='Default')
        self.parsing_rules.append(default_rule)

    def parse(self, source, *args, **kwargs):
        logger.debug('In line_parser')
        for line in source:
            logger.debug(f'In line_parser, received line: {line}')

            for rule in self.parsing_rules:
                parsed_lines = rule.apply(line, *args, **kwargs)
                if parsed_lines is not None:
                    break

            if parsed_lines is not None:
                for parsed_line in parsed_lines:
                    yield parsed_line


class SectionBreak():  # pylint: disable=function-redefined
    def __init__(self, trigger: Trigger,
                 offset='Before', name='SectionBreak'):
        '''
        starting_offset	[Int or str] if str, one of Before or After
        if -1 or 'Before', Save the line that activates the Trigger for next section.
        if 0 or 'After', Include the line that activates the Trigger in the section.
        '''
        self.name = name
        if isinstance(trigger, str):
            self.trigger = Trigger(trigger)
        elif isinstance(trigger, Trigger):
            self.trigger = trigger
        else:
            raise ValueError('trigger must be string or Trigger instance.')
        self.offset = self.get_offset(offset)

        self.count_down = None
        self.event = None

    @staticmethod  # TODO convert SectionBreak.offset to a property
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

    def check(self, line: str, source: BufferedIterator, **context):
        '''Check for a Break condition
        If an Active count down situation exists, continue the count down.
        Otherwise, apply the trigger test.
        If the Trigger signals a break, set the appropriate line location for
        the break based on the offset value.
        '''
        logger.debug('in section_break.check')
        # Check for a Break condition
        if self.count_down is None:  # No Active Count Down
            # apply the trigger test.
            is_break, event = self.trigger.apply(line, context)
            if is_break:
                logger.debug(f'Break triggered by {event}')
                self.event = event
                is_break = self.set_line_location(source)

        elif self.count_down == 0:  # End of Count Down Reached
            logger.debug(f'Line count down in {self.name} completed.')
            self.count_down = None  # Remove Active Count Down
            is_break = True
            source.step_back = 1  # Save current line for next section
        elif self.count_down > 0:  #  Active Count Down Exists
            logger.debug(f'Line count down in {self.name} Continuing;\t'
                         f'Count down now at {self.count_down}')
            self.count_down -= 1   #  Continue Count Down
            is_break = False
        return is_break

    def set_line_location(self, source: BufferedIterator):
        '''Set the appropriate line location for a break based on the offset
        value.
        '''
        if self.offset < 0: # Save current line for next section
            logger.debug(f'Stepping back {-self.offset} lines')
            source.step_back = -self.offset
            is_break = True
        else: # Use more lines before activating break
            logger.debug(f'Using {self.offset} more lines.')
            self.count_down = self.offset  # Begin Active Count Down
            is_break = False
        return is_break


#%% Section Parser
### Parser methods ###
#  Method Name	Produces	       Action
#  parse	    Single Object	   line in -> list out
#  reader	    Generator	       sequence in -> generator out
#  read	        Sequence (list)	   sequence in -> list of lists out

class SectionProcessor():  # pylint: disable=function-redefined
    '''A SectionProcessor has a .read
                processor method
                which is a generator function, accepting a source text stream
                and yielding the processed text. Defaults to None, which sets
                a basic csv parser.'''
    def __init__(self,
                 section_name = 'SectionParser',
                 preprocessing_methods=None,
                 parsing_rules=None,
                 default_parser=None,
                 post_processing_methods=None):
        self.section_name = section_name
        self.context = dict()
        if preprocessing_methods:
            self.preprocessing_methods = preprocessing_methods
        else:
            self.preprocessing_methods = list()
        if parsing_rules:
            self.parsing_rules = parsing_rules
        else:
            self.parsing_rules = list()
        # TODO SectionReader should use an internally defined parser as default
        if default_parser:
            self.default_parser = default_parser
        else:
            self.default_parser = define_csv_parser()
        if post_processing_methods:
            self.post_processing_methods = post_processing_methods
        else:
            self.post_processing_methods = list()
        # Apply Section Cleaning -> clean_lines
        # Check for End of Section Break -> break_triggers
        # Call Line Parser, passing Context & Lines -> Dialect, Special Lines
        # Apply Line Processing Rules -> trim_lines
        # TODO want line_parser and post processing to access context,
        # but preprocessing_methods only expect 1 argument; the text line to
        # process, Separate stages into successive iterators
        self.section_stages = list()
        self.section_stages.extend(self.preprocessing_methods)
        self.section_stages.append(self.set_line_parser())
        self.section_stages.extend(self.post_processing_methods)

    def set_line_parser(self)->Callable:
        parser_instance = LineParser(self.parsing_rules,
                                     self.default_parser)
        return parser_instance.parse

    def reader(self, buffered_source, **context):
        self.context = context
        return cascading_iterators(buffered_source, self.section_stages)

    def read(self, buffered_source, **context):
        self.context = context
        section_iter = cascading_iterators(buffered_source,
                                           self.section_stages)
        read_list = list()
        while True:
            try:
                read_list.append(next(section_iter))
            except StopIteration:
                break
        return read_list


#%% Section
class Section():  # pylint: disable=function-redefined
    '''Defines a continuous portion of a text stream or other iterable.

    A section definition may include:
        ○ Starting and ending break points.
        ○ Processing instructions.
        ○ An aggregation method.
    A Section instance is created by defining one or more of these components.
    Once a section has been defined, it can be applied to an iterator using:
        section.read(source)
    Where
        source is any iterable supplying the text lines to be parsed.

    section.read, the primary method has the following steps:
        1. Iterate through the text source, checking for the start of the
            section (optional).
        2. Continue to iterate through the text source, applying the defined
            processing rules to each line, while checking for the end of the
            section.
        3. Apply an aggregating function to the processed text to convert it
            to the desired output format.

    section.scan and section.process are alternate methods.
        section.scan returns a generator that starts at the beginning of the
            section and iterates through to the end of the section without
            applying any processing or aggregation.
        section.process returns a generator that starts at the beginning of
            the section and iterates through to the end of the section
            applying the defined processing, but omitting the aggregation.

    Attributes:
            section_name (str): A reference name for the section instance.
            keep_partial (bool): In the case where the reader is
                composed of one or more subsections and the main section ends
                before the subsections end. If keep_partial is true the partial
                subsection(s) will be returned, otherwise they will be dropped.
            scan_status (str): Indicates section reading progress. It is useful
                for providing user feedback when the section reading process
                is lengthy.  scan_status Will contain one of the following
                text strings:
                    'Not Started'
                   'At the start of section {section_name}'
                   'Scan In Progress'
                   'Break Triggered'
                   'Scan Complete'
            context (Dict[str, Any]): Break point information and any
                additional information to be passed to and from break point,
                processing and aggregation methods. This is the primary method
                for different reading stages to pass contextual information.
                When a section boundary is encountered (including sub-sections)
                two items will be added to the context dictionary:
                    'Break': (str): The name of the Trigger instance that
                        activated the boundary condition.
                    'Event' (bool, str, re.match): Information on the
                        boundary condition returned by the Trigger instance.
                            If Trigger always passes, 'Event' will be True.
                            If Trigger matched a string, bool, 'Event' will
                                be the matching string.
                            If Trigger matched a regular expression, 'Event'
                                will be the resulting re.match object.
  '''
    # A SectionBreak that causes the section to start with the first item in
    # the source.
    default_start = SectionBreak(Trigger(True), name='AlwaysBreak',
                                 offset='Before')
    # A SectionBreak that never triggers, causing the section to continue to
    # the end of the source.
    default_end = SectionBreak(Trigger(False), name='NeverBreak')

    def __init__(self,
                 section_name: str = 'Section',
                 start_section: BreakOptions = None,
                 end_section: BreakOptions = None,
                 processor: ProcessorOptions = None,
                 aggregate: Callable = None,
                 keep_partial: bool = False):
        '''Creates an Section instance that defines a continuous portion of a
        text stream to be processed in a specific way.

        Args:
            section_name (str, optional): A label to be applied to the section.
                Defaults to 'Section'.
            start_section (BreakOptions, optional): The SectionBreak(s) used
                to identify the location of the start of the section. Defaults
                to None, indicating the section begins with the first text
                line in the iterator.
            end_section (BreakOptions, optional): The SectionBreak(s) used
                to identify the location of the end of the section. Defaults
                to None, indicating the section ends with the last text line
                in the iterator.
            processor (ProcessorOptions, optional): Instructions for processing
                and the section items.  processor can be None, in which case
                the section will use the default SectionProcessor, it can be a
                SectionProcessor instance, a Section instance, or a list of
                Section instances.
            aggregate (Callable, optional): A function used to collect and
                format, the processor output.  It should step through the
                iterator or generator function, passed as its first argument,
                combining the reader output into a single object.
                Defaults to None, which returns a list of the reader output.
            keep_partial (bool, optional): In the case where the reader is
                composed of one or more subsections and the main section ends
                before the subsections end. If keep_partial is true the partial
                subsection(s) will be returned, otherwise they will be dropped.
                Defaults to False,
        Returns:
            New Section.
        '''
        # Initialize attributes
        self.section_name = section_name
        self.keep_partial = keep_partial

        # The context, scan_status and source attributes must be reset every
        # time the Section instance is applied to a new source iterable.  The
        # reset() method is should set these attributes to the values below.
        # In addition, if the processor contains one or more Sections these
        # attributes in the processor sections will must also be reset.
        self.context = dict()
        self.scan_status = 'Not Started'
        self.source = None
        # Set the start and end section break properties
        self.start_section = start_section
        self.end_section = end_section
        # Initialize the processor properties
        # _section_reader is set when the processor.setter method is called.
        self._section_reader = None
        self.processor = processor
        # Set the Aggregate method
        if aggregate:
            self.aggregate = aggregate
        else:
            self.aggregate = list

    @property
    def source(self):
        '''BufferedIterator: The iterable object (with a BufferedIterator
            wrapper) that the section instance is actively iterating through.
        '''
        return self._source

    @source.setter
    def source(self, source: Source)->BufferedIterator:
        '''Wrap the source in a BufferedIterator if it is not one already.
        '''
        if source:
            # Wrap the source in a BufferedIterator if it is not one already.
            if not isinstance(source, BufferedIterator):
                buffered_source = BufferedIterator(iter(source))
            else:
                buffered_source = source
            self._source = buffered_source  # Begin iteration
        else:
            # Reset the source
            self._source = None

    @property
    def start_section(self):
        '''List[SectionBreak]: SectionBreaks that define the start boundary of
            the section.

            If no start_section definition is supplied, start_section becomes a
            single element list containing a SectionBreak that causes the
            section to start with the first item in the source.
        '''
        return self._start_section


    @start_section.setter
    def start_section(self, section_break: BreakOptions):
        '''List[SectionBreak]: Defined by one of:
                List[SectionBreak], the start_section type.
                SectionBreak, which is converted to a single element list.
                str, which is converted to a single element list containing a
                    SectionBreak that triggers on the supplied string.
                List[str], which is converted to a list containing
                    SectionBreaks that trigger on each of the supplied strings.
            Setting start_section to None will clear existing definitions and
                replace it with a single element list containing
                self.default_start.
        '''
        brk = self.set_break(section_break)
        if brk:
            self._start_section = brk
        else:
            self._start_section = [self.default_start]

    @property
    def end_section(self):
        '''List[SectionBreak]: SectionBreaks that define the ending boundary of
            the section.

            If no end_section definition is supplied, start_section becomes a
            single element list containing a SectionBreak that never triggers,
            causing the section to continue to the end of the source.
        '''
        return self._end_section

    @end_section.setter
    def end_section(self, section_break: BreakOptions):
        '''List[SectionBreak]: Defined by one of:
                List[SectionBreak], the end_section type.
                SectionBreak, which is converted to a single element list.
                str, which is converted to a single element list containing a
                    SectionBreak that triggers on the supplied string.
                List[str], which is converted to a list containing
                    SectionBreaks that trigger on each of the supplied strings.
            Setting end_section to None will clear existing definitions and
            replace it with a single element list containing self.default_end.
        '''
        brk = self.set_break(section_break)
        if brk:
            self._end_section = brk
        else:
            self._end_section = [self.default_end]

    def set_break(self, section_break: BreakOptions) -> List[SectionBreak]:
        '''Convert the supplied BreakOption to a list of SectionBreaks.

        Args:
            section_break (BreakOptions): The supplied BreakOption can be:
                List[SectionBreak], in which case it is returned unchanged.
                SectionBreak, in which case it is converted to a single
                    element list and returned.
                str, in which case it is converted to a single
                    element list containing a SectionBreak that triggers on
                    the supplied string and returned.
                None, in which case the section_break definition is cleared.
        Raises:
            TypeError: If section_break is not a SectionBreak instance, a
                list of SectionBreaks, a string, a list of strings, or None.
        Returns:
            List[SectionBreak]: A list of section breaks to be applied to
                either the start or end boundary of the section.
        '''
        # If not defined use default
        if not section_break:
            validated_section_break = None
        # Convert single Break instance into list
        elif isinstance(section_break, SectionBreak):
            validated_section_break = [section_break]
        # convert a supplied string into a section break that triggers on the
        # supplied string.
        elif isinstance(section_break, str):
            validated_section_break = [SectionBreak(section_break)]
        elif isinstance(section_break, list):
            # Verify that all item is the list are type str
            validated_section_break = list()
            for brk in section_break:
                if isinstance(brk, str):
                    validated_section_break.append(SectionBreak(brk))
                else:
                    raise ValueError('If section_break is a list, the list '
                                     'items may only be of type str.')
        else:
            raise TypeError('section_break must be one of SectionBreak, a '
                            'list of SectionBreaks, a string, or None.')
        return validated_section_break

    @property
    def processor(self):
        '''(SectionProcessor, List[Section]):  Instructions for processing the
            section items. If it is a SectionProcessor instance, each item in
            the source is processed according to the SectionProcessor Rules.
            If it is a list of subsections, the processor returns the
            subsection aggregate results as an item.
        '''
        return self._processor

    @processor.setter
    def processor(self, processing_def: ProcessorOptions = None):
        '''Validates the Section Processor and sets the relevant
            section_reader method.
        Args:
            processing_def (ProcessorOptions): The processing instructions for
                the section. Can be a SectionParser instance, a Section
                instance, or a list of Section instances.
        Raises:
            ValueError: 'If processor is a list where not all of the list items
                is of type Section.
            TypeError: If processor is not one of a SectionParser instance, a
                Section instance, a list of Section instances, or None.
        '''
        if processing_def:
            if isinstance(processing_def, SectionProcessor):
                self._processor = processing_def
                self._section_reader = self.sequence_processor
            elif isinstance(processing_def, Section):
                processing_def.reset()
                self._processor = [processing_def]
                self._section_reader = self.subsection_processor
            elif isinstance(processing_def, list):
                # Verify that all item is the list are type Section
                for sub_rdr in processing_def:
                    if isinstance(sub_rdr, Section):
                        sub_rdr.reset()
                    else:
                        raise ValueError('If processor is a list, the list '
                                         'items may only be of type Section.')
                self._processor = processing_def
                self._section_reader = self.subsection_processor

            else:
                raise TypeError('processor must be one of SectionParser, a '
                                'Section instance, a list of Section '
                                'instances, or None.')
        else:
            # if processor is None return a default SectionProcessor.
            self._processor = SectionProcessor()
            self._section_reader = self.sequence_processor

    def sequence_processor(self, section_iter: Iterator,
                           reader: SectionProcessor,
                           **context) -> Generator[Any, None, None]:
        '''Apply the SectionProcessor to each item in the section.

        Args:
            section_iter (Iterator): The section's source iterator after
                checking for boundaries.
            reader (SectionProcessor): The item processing Rules as a
                SectionProcessor instance.
            **context (Dict[str, Any]): Break point information and any
                additional information to be passed to and from the
                SectionProcessor instance.
        Yields:
            Generator[Any, None, None]: The results of applying the
                SectionProcessor Rules to each item in the section.
        '''
        read_iter = iter(reader.reader(section_iter, **context))
        done = False
        while not done:
            try:
                item_read = next(read_iter)
            except StopIteration:
                done = True
            else:
                yield item_read
            finally:
                self.context.update(reader.context)

    def read_subsections(self, section_iter: Iterator,
                         subreaders: List[Section], **context)->List[Any]:
        '''Read each of the subsections as if they were a single item.

        Args:
            section_iter (Iterator): The section's source iterator after
                checking for boundaries.
            sub-readers (List[Section]): The subsections that together define
                the processing of the main section.
            **context (Dict[str, Any]): Break point information and any
                additional information to be passed to and from the
                subsections instance.
        Returns:
            List[Any]: A list of the aggregate results for all of the
                subsections.
        '''
        if 'GEN_CLOSED' in inspect.getgeneratorstate(section_iter):
            # If the source has closed don't try reading subsections
            return None
        subsection = list()
        for sub_rdr in subreaders:
            if not self.keep_partial:
                if 'GEN_CLOSED' in inspect.getgeneratorstate(section_iter):
                    # If the source ends part way through, drop the partial subsection
                    return None
            sub_rdr.source = self.source
            subsection.append(sub_rdr.read(section_iter, do_reset=False,
                                           **context))
            self.context.update(sub_rdr.context)
        return subsection

    def subsection_processor(self, section_iter: Iterator,
                             subreaders: List[Section],
                             **context)->Generator[Any, None, None]:
        '''Yield processed subsections until the main section is complete.

        Step through section_iter yielding a list of the aggregate results for
        all of the subsections as a single item from the generator.

        Args:
            section_iter (Iterator): The section's source iterator after
                checking for boundaries.
            sub-readers (List[Section]): The subsections that together define
                the processing of the main section.
            **context (Dict[str, Any]): Break point information and any
                additional information to be passed to and from the
                SectionProcessor instance.
        Yields:
            List[Any]: A list of the aggregate results for all subsections.
        '''
        while 'GEN_CLOSED' not in inspect.getgeneratorstate(section_iter):
            # Testing the generator state is required because StopIteration
            # is being trapped before it reached the except statement here.
            try:
                subsection = self.read_subsections(section_iter, subreaders,
                                                    **context)
                if subsection:
                    if len(subsection) == 1:
                        # If the subsection group contains only one section
                        # get rid of the redundant list level.
                        yield subsection[0]
                    else:
                        yield subsection
            except StopIteration:
                break

    def reset(self):
        ''' Return the section attributes back to their initial values.
        source are reset to their
        initial values.

        The attributes: context, scan_status, and source are cleared so that
        the section instance can be re-used with a new source.  If the section
        processor contains one or more Section instances, the same attributes
        in the subsections will also be reset.

        Returns:
            None.
        '''
        self.context = dict()
        self.scan_status = 'Not Started'
        self.source = None
        # Reset subsection attributes
        processor = self.processor
        if isinstance(processor, list):
            for sub_sec in processor:
                sub_sec.reset()

    def is_boundary(self, line: str, break_triggers: List[SectionBreak])->bool:
        '''Test the current item from the source iterable to see if it triggers
        a boundary condition.

        If a boundary condition is triggered, the scan_status attribute
        becomes: 'Break Triggered' and two items in the section context
            attribute are updated:
            'Break': (str): The name of the Trigger instance that activated the
                boundary condition.
            'Event' (bool, str, re.match): Information on the boundary
                condition returned by the Trigger instance:
                    If Trigger always passes, 'Event' will be True.
                    If Trigger matched a string, bool, 'Event' will be the
                        matching string.
                    If Trigger matched a regular expression, 'Event' will be
                        the resulting re.match object.
        Args:
            line (str): The line item from the source iterable.
            break_triggers (List[SectionBreak]): The SectionBreak Rules that
            define the boundary condition.
        Returns:
            bool: Returns True if a boundary event was triggered.
        '''
        for break_trigger in break_triggers:
            logger.debug(f'Checking Trigger: {break_trigger.name}')
            # break_trigger needs to access the base BufferedItterator Source
            # not the top level one, otherwise it will not step back properly.
            is_break = break_trigger.check(line, self.source, **self.context)
            if is_break:
                logger.debug('Section Break Detected')
                self.scan_status = 'Break Triggered'
                self.context['Event'] = break_trigger.event
                self.context['Break'] = break_trigger.name
        return is_break

    def step_source(self, source: Source)->Any:
        '''Advance the source, catching any form of generator exit.

        Call `next` on source, trapping any standard form of generator exit.
        Update the status and context attributes based on the result of
        calling `next`:
            If no exception is raised set scan_status and context['Status'] to:
                    'Scan In Progress'
            If a RuntimeError exception is caught, set scan_status to:
                    'Scan Complete'
                and context['Status'] to:
                    'Scan In Progress'
            If BufferedIteratorEOF, IteratorEOF, or StopIteration exception is
                caught, set scan_status to:
                    'Scan Complete'
                and context['Status'] to:
                    'End of Source'
        Args:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
        Returns:
            Any: The next item from source.
        '''
        break_context = dict()
        next_item = None
        try:
            # next must be called on the top level Source not the base one,
            # otherwise it will not supply the correct item here.
            next_item = next(source)
        except (RuntimeError) as err:
            status = 'Scan Complete'
            break_context['Status'] = 'RuntimeError'
            logger.warning(f'RuntimeError Encountered: {err}')
        except (BufferedIteratorEOF, StopIteration):
            status = 'Scan Complete'
            break_context['Status'] = 'End of Source'
        else:
            status = 'Scan In Progress'
            break_context['Status'] = 'Scan In Progress'
            logger.debug(f'In:\t{self.section_name}\tGot item:\t{next_item}')
        finally:
            self.scan_status = status
            self.context.update(break_context)
            logger.debug(f'Break Status:\t{break_context["Status"]}')
        return next_item

    def advance_to_start(self, source: Source)->List[Any]:
        '''Step through the source until the start of the section is reached.

        Args:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
        Returns:
            list[Any]: The items preceding the beginning of the section.
        '''
        skipped_lines = list()
        self.scan_status = 'Not Started'
        while True:
            next_item = self.step_source(source)
            if 'Scan Complete' in self.scan_status:
                break
            if self.is_boundary(next_item, self.start_section):
                break
            skipped_lines.append(next_item)
        self.context['Skipped Lines'] = skipped_lines
        return skipped_lines

    def initialize(self, source: Source, start_search: bool = True,
                   do_reset: bool = True, **context)->BufferedIterator:
        '''
        Args:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or
                assume that the section begins at the start of the source.
                Defaults to True, meaning advance until the start boundary is
                found.
            do_reset (bool, optional): Indicate whether to reset the source-
                related properties when initializing the source. Normally
                the properties should be reset, but if the section is being
                used as a subsection, then it should inherit properties from
                the parent section and not be reset. Defaults to True, meaning
                reset the properties.
            **context (Dict[str, Any]): Break point information and any
                additional information to be passed to and from the
                Section instance.
        Returns:
            BufferedIterator: The iterable object (with a BufferedIterator
            wrapper) that the section instance is actively iterating through.
        '''
        # Reset variables and Update context
        if do_reset:
            self.reset()  # This clears source, context and scan_status
            self.source = source
            active_source = self.source  # Get cleaned and buffered source
        elif self.source:
            # self.source is pre-existing root BufferedIterator, active_source
            # iterates self.source, but adds boundary checking.  This is needed
            # when using sub-sections.
            active_source = source
        else:
            self.source = source
            active_source = self.source  # Get cleaned and buffered source

        self.context.update(context)
        # If requested, advance through the source to the section start.
        if start_search:
            self.advance_to_start(active_source)
        # Update Section Status
        logger.debug(f'Starting New Section: {self.section_name}.')
        self.context['Current Section'] = self.section_name
        self.scan_status = f'At the start of section {self.section_name}'
        return active_source

    def gen(self, source: Source)->Generator[Any, None, None]:
        '''The internal section generator function.

        Step through all items from source that are in section; starting and
        stopping at the defined start and end boundaries of the section.

        Args:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
        Yields:
            Generator[Any, None, None]: An iterator containing all source items
                within the section.
        '''
        # Read source until end boundary is found or source ends
        while True:
            next_item = self.step_source(source)
            if 'Scan Complete' in self.scan_status:
                # self.scan_status stays local self.context gets updated
                # by sub-sections.
                break
            if self.is_boundary(next_item, self.end_section):
                break
            yield next_item

    def scan(self, source: Source, start_search: bool = True,
             do_reset: bool = True, **context)->Generator[Any, None, None]:
        '''The primary outward facing section generator function.

        Initialize the source and then provide the generator that will step
        through all items from source that are in section; starting and
        stopping at the defined start and end boundaries of the section.

        Args:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or
                assume that the section begins at the start of the source.
                Defaults to True, meaning advance until the start boundary is
                found.
            do_reset (bool, optional): Indicate whether to reset the source-
                related properties when initializing the source. Normally
                the properties should be reset, but if the section is being
                used as a subsection, then it should inherit properties from
                the parent section and not be reset. Defaults to True, meaning
                reset the properties.
            **context (Dict[str, Any]): Break point information and any
                additional information to be passed to and from the
                Section instance.
        Returns:
            Generator[Any, None, None]: A generator that will step
        through all items from source that are in section; starting and
        stopping at the defined start and end boundaries of the section.
        '''
        # Initialize the section
        source = self.initialize(source, start_search, do_reset, **context)
        section_iter = self.gen(source)
        return section_iter

    def process(self, source: Source, start_search: bool = True,
             do_reset: bool = True, **context)->Generator[Any, None, None]:
        '''
        Args:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or
                assume that the section begins at the start of the source.
                Defaults to True, meaning advance until the start boundary is
                found.
            do_reset (bool, optional): Indicate whether to reset the source-
                related properties when initializing the source. Normally
                the properties should be reset, but if the section is being
                used as a subsection, then it should inherit properties from
                the parent section and not be reset. Defaults to True, meaning
                reset the properties.
            **context (Dict[str, Any]): Break point information and any
                additional information to be passed to and from the
                Section instance.
        Yields:
            Generator[Any, None, None]: A generator that will step
                through all items from source that are within the section
                boundaries; returning the results of applying the
                SectionProcessor Rules to each item in the section.
        '''
        # Initialize the section
        source = self.initialize(source, start_search, do_reset, **context)
        section_iter = self.gen(source)
        section_reader = self._section_reader(section_iter, self.processor,
                                              **context)
        try:
            yield from section_reader
        except StopIteration:
            pass

    def read(self, source: Source, start_search: bool = True,
             do_reset: bool = True, **context)->Any:
        '''
        Args:
            source (Source): An iterable where some of the content meets the
                section boundary conditions.
            start_search (bool, optional): Indicates whether to advance through
                the source until the beginning of the section is found or
                assume that the section begins at the start of the source.
                Defaults to True, meaning advance until the start boundary is
                found.
            do_reset (bool, optional): Indicate whether to reset the source-
                related properties when initializing the source. Normally
                the properties should be reset, but if the section is being
                used as a subsection, then it should inherit properties from
                the parent section and not be reset. Defaults to True, meaning
                reset the properties.
            **context (Dict[str, Any]): Break point information and any
                additional information to be passed to and from the
                Section instance.
        Returns:
            Any: The result of applying the aggregate function to all processed
                items from source that are within the section boundaries.
        '''
        # Initialize the section
        source = self.initialize(source, start_search, do_reset, **context)
        section_iter = self.gen(source)
        section_reader = self._section_reader(section_iter, self.processor,
                                              **context)
        section_items = list()
        while True:
            try:
                section_items.append(next(section_reader))
            except StopIteration:
                break
        # Apply the aggregate function
        section_aggregate = self.aggregate(section_items)
        return section_aggregate

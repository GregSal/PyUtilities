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
from typing import Iterable, Any, Callable, Union, Generator, NamedTuple

import pandas as pd

from data_utilities import true_iterable
import logging_tools as lg

from buffered_iterator import BufferedIterator
from buffered_iterator import BufferOverflowWarning
from buffered_iterator import BufferedIteratorEOF


#%% Logging
logger = lg.config_logger(prefix='Text Processing', level='DEBUG')


#%% Type Definitions
# These type definitions will be redefined as class types.  They are defined
# here to simplify Type annotations.
Section = TypeVar('Section')  # pylint: disable=function-redefined
SectionBreak = TypeVar('SectionBreak')  # pylint: disable=function-redefined
SectionProcessor = TypeVar('SectionProcessor')  # pylint: disable=function-redefined
SectionProcessor = TypeVar('SectionProcessor')  # pylint: disable=function-redefined
TriggerEvent = TypeVar('TriggerEvent')  # pylint: disable=function-redefined

# NonStringSource represents the non-string type iterables used as a source
NonStringSource = TypeVar('NonStringSource')
ProcessedItem = TypeVar('ProcessedItem')
ParsedString = List[str]
SourceItem = Union[str, ParsedString, NonStringSource]
Source = Iterable[SourceItem]

ContextType = Union[Dict[str, Any], None]

# Relevant Type definitions for Trigger Class
TriggerSingleTypes = Union[None, bool, int]
TriggerListOptions = Union[str, re.Pattern, Callable]
TriggerTypes = Union[TriggerSingleTypes, TriggerListOptions]
TriggerOptions = Union[TriggerTypes, List[TriggerListOptions]]
CallableResult = TypeVar('CallableResult')  # Represents the return from a Trigger Callable
EventType = Union[bool, int, str, re.match, CallableResult, None]
TestResult = Union[bool, re.match, CallableResult]

# Relevant Type definitions for SectionBreak Class
OffsetTypes = Union[int, str]

# Relevant Type definitions for Rule Class
RuleResult = TypeVar('RuleResult')  # Represents the return from a Rule Method
SingleItemFunc = Callable[[SourceItem], RuleResult]
ItemEventFunc = Callable[[SourceItem, TriggerEvent], RuleResult]
RuleFunc = Callable[[SourceItem, TriggerEvent, ContextType], RuleResult]
RuleMethodOptions = Union[str, SingleItemFunc, ItemEventFunc, RuleFunc, None]

TestType = Callable[[TriggerTypes, SourceItem, ContextType], TestResult]
Strings = Union[str, ParsedString]
OptStrings = Union[Strings, None]
OptStr = Union[str, None]
AlphaNumeric = Union[float, str]
Integers = Union[int, List[int]]

ParseResults = Union[List[ParsedString], None]

StringSource = Iterable[str]
ParsedStringSource = Union[Iterator[ParsedString], Sequence[ParsedString]]

# Relevant Type definitions for Section Classes
BreakOptions = Union[SectionBreak, List[SectionBreak], str, None]
ProcessorOptions = Union[SectionProcessor, Section, List[Section]]

# TODO create more type definitions: Line, ...
# TODO more explicit generic type definitions
# TODO Move generic functions to separate module
# TODO copy clean_ascii_text from file_utilities
# TODO copy true_iterable from data_utilities
# Move the major classes:  Section, SectionReader, SectionBreak, ParsingRule,
# Trigger to a separate Module


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
def csv_parser(line: str, dialect_name='excel') -> ParseResults:
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


def define_csv_parser(name='csv', **parameters) -> Callable[[str,],List[str]]:
    '''Create a function that applies the defined csv parsing rules.

    Create a unique csv parsing Dialect referred to by name. Use the partial
    method to create and return a function that applies the defines parsing
    rules to a string.

    Args:
        name: Optional, The name for the new Dialect. Default is 'csv'.
        **parameters: Any valid csv reader parameter.
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
    default_parameters = dict(
        delimiter=',',
        doublequote=True,
        quoting=csv.QUOTE_MINIMAL,
        quotechar='"',
        escapechar=None,
        lineterminator='\r\n',
        skipinitialspace=False,
        strict=False
        )
    default_parameters.update(parameters)
    csv.register_dialect(name, **default_parameters)
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



def file_reader(file_path: Path)->BufferedIterator:
    def file_line_gen(file_path):
        with open(file_path, newline='') as textfile:
            for line in textfile:
                yield line
    source = BufferedIterator(file_line_gen(file_path))
    return source

###### These all belong in their own module

#%% Iteration Tools
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


class TriggerEvent(): # pylint: disable=function-redefined
    '''Trigger test result information.

    Attributes:
        trigger_name (str): The name of the trigger the test is associated
            with.
        test_result (bool): True if one of the applied tests passed; otherwise
            False.
        test_name (str): Label describing the passed text. Defaults to ''.
            The test name type depends on sentinel_type:
            type(sentinel)      test_name
              None                'None'
              bool                str(sentinel)
              int                 str(sentinel)
              str                 sentinel
              List[str]           The sentinel item triggering the event
              re.Pattern          sentinel.pattern
              List[re.Pattern]    sentinel.pattern for the triggering item.
              Callable            sentinel.__name__
              List[Callable]      sentinel.__name__ for the triggering item.
        test_value (EventType): Information resulting from applying the test.
            The test_value object type depends on sentinel_type:
                type(sentinel)      type(test_value)
                  None                bool = False
                  bool                bool
                  int                 int = sentinel
                  str                 str = sentinel
                  List[str]           str = one of sentinel items
                  re.Pattern          re.match
                  List[re.Pattern]    re.match
                  Callable            CallableResult
                  List[Callable]      CallableResult
    '''

    def __init__(self):
        '''Initialize a TriggerEvent with default values.
        '''
        self.trigger_name: str = ''
        self.test_result: bool = False
        self.test_name: str = ''
        self.test_value: EventType = None
        self.reset()

    def reset(self):
        '''Set the event to its default values.

        Default values are:
            test_result = False
            trigger_name = ''
            test_name = ''
            event = None
        '''
        self.trigger_name = ''
        self.test_result = False
        self.test_name = ''
        self.test_value = None

    def record_event(self, test_result: TestResult, sentinel: TriggerTypes,
                     trigger_name: str, sentinel_type: str):
        '''Set the appropriate event values a passed test.

        The event object and label type depend on sentinel_type:
            sentinel_type        type(test_value)      test_name
              'None'             bool = False         'None'
              'Boolean'          bool                  str(sentinel)
              'Count'            int = sentinel        str(sentinel)
              'String'           str = sentinel        sentinel
              'RE'               re.match              sentinel.pattern
              'Function'         CallableResult        sentinel.__name__
        Args:
            test_result (TestResult): The value returned by the test function.
            sentinel (TriggerTypes): The individual object used to define the
                test.
            trigger_name (str): A reference label for the Trigger.
            sentinel_type (str): The type of sentinel supplied. Can be one of:
                'None':     A place holder conditional that will never pass.
                'Boolean':  A conditional that does not depend on the object
                            being tested.
                'String':   A conditional that will pass if the item being
                            tested matches with a string.
                'RE':       A conditional that will pass if an re.pattern
                            successfully matches in the item being tested.
                'Function': A conditional that will pass if the sentinel
                            function returns a non-blank value.
                'Count':    A conditional that will pass after being called the
                            specified number of times. -- Not Yet Implemented.
        '''
        self.reset()
        if test_result:
            self.test_result = True
            self.trigger_name = trigger_name
            if sentinel_type ==  'None':
                self.test_value = test_result
                self.test_name = 'None'
            elif sentinel_type ==  'Boolean':
                self.test_value = test_result
                self.test_name = str(test_result)
            elif sentinel_type ==  'String':
                self.test_value = sentinel
                self.test_name = str(sentinel)
            elif sentinel_type ==  'RE':
                self.test_value = test_result
                self.test_name = sentinel.pattern
            elif sentinel_type ==  'Function':
                self.test_value = test_result
                self.test_name = sentinel.__name__
            elif sentinel_type ==  'Count':
                self.test_value = sentinel
                self.test_name = str(sentinel)


#%% Section Classes
class Trigger():
    '''Test definition for evaluating a source item.

    A trigger is formed by a conditional definition to be applied to source
    items.  The conditional definition is generated from one of the following
    sentinel types:
        None:   A place holder conditional that will never pass.
        bool:   A conditional that will either always pass or always fail.
        int:    A conditional that will pass after being called the specified
                number of times. -- Not Yet Implemented.
        str or List[str]:
                A conditional that will pass if the item being tested matches
                with the string (or with any of the strings in the list).  The
                location attribute dictates the type of match required.
        re.Pattern or List[re.Pattern]:  Compiled regular expression pattern(s)
                re.Pattern objects are generated with re.compile(string).
                Regular Expression patterns must be compiled to distinguish
                them from plain text sentinels.
                A conditional that will pass if the pattern (or one of the
                patterns in the list) successfully matches in the item being
                tested. The location attribute dictates the type of regular
                expression match required.
        Callable or List[Callable]:
                A conditional that will pass if the sentinel function (or one
                of the functions in the list) returns a non-blank
                (None, '', []) value when applied to the item being tested.
                -- Not Yet Implemented.

    The location argument is a sentinel modifier that applies to str or
        re.Pattern types of sentinels. location can be one of:
            location    str test                    re.Pattern test
              IN      sentinel in item            sentinel.search(item)
              START   item.startswith(sentinel)   sentinel.match(item)
              END     item.endswith(sentinel),    NotImplementedError
              FULL    sentinel == item            sentinel.fullmatch(item)

    When a test is applied, the event property is updated based on whether the
        test passes and the type of test.
        If the test fails:
            event -> None.
        If the test passes:
            sentinel Type                   event Type
            bool (True)                     bool (True)
            int:                            int: the integer value of the
                                                sentinel.
            str or List[str]                str: the specific string in the
                                                list that caused the pass.
            re.Pattern or List[re.Pattern]  re.match: the match object
                                                generated by applying the
                                                pattern to the item.
            Callable or List[Callable]      Any: The return value of the
                                                successful function.
    If the supplied sentinel is a list of strings, compiled regular expressions
    or functions, the trigger will step through each sentinel element in the
    list, evaluating them against the supplied item to test.  When a test
    passes, no additional items in the list will be tested.
    Attributes:
            sentinel (None, bool, int,
                      str or List[str],
                      re.Pattern or List[re.Pattern],
                      Callable or List[Callable]):
                the object(s) used to generate the conditional definition.
                Note: int type sentinel is not yet implemented.
            name (str, optional): A reference label for the Trigger.
                A reference name for the section instance.
            event (TriggerEvent): Information resulting from applying the test.
    '''
    def __init__(self, sentinel: TriggerOptions, location=None,
                 name='Trigger'):
        '''Define test(s) that signal a trigger event.

        Arguments:
            name (str, optional): A reference label for the Trigger.
            sentinel (TriggerOptions): Object(s) used to generate the
                conditional definition.
                Note: int type sentinel is not yet implemented.
            location (str, optional):  A sentinel modifier that applies to str
                or re.Pattern types of sentinels. For other sentinel types it
                is ignored. One of  ['IN', 'START', 'END', 'FULL', None].
                Default is None, which is treated as 'IN'
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
        self.name = name
        # Private attributes
        self._is_multi_test = False
        self._sentinel_type = self.set_sentinel_type()
        self._test_func = self.set_test_func(location)
        self._event = TriggerEvent()

    def set_sentinel_type(self)->str:
        '''Identify the type of sentinel supplied.

        The sentinel type returned can be one of:

            type(sentinel)  sentinel_type string
              None                'None'
              bool                'Boolean'
              int                 'Count'
              str                 'String'
              List[str]           'String'
              re.Pattern          'RE'
              List[re.Pattern]    'RE'
              Callable            'Function'
              List[Callable]      'Function'

        If the sentinel is a list of strings, re patterns or functions, set
        the self._is_multi_test = True.

        Raises:
            NotImplementedError: If self.sentinel is not one of the above types.

        Returns:
            str: The string matching the self.sentinel type.
        '''
        test_type = None
        if self.sentinel is None:
            test_type = 'None'
        elif isinstance(self.sentinel, bool):
            test_type = 'Boolean'
        elif isinstance(self.sentinel, str):
            test_type = 'String'
        elif isinstance(self.sentinel, re.Pattern):
            test_type = 'RE'
        elif callable(self.sentinel):
            test_type = 'Function'
        elif true_iterable(self.sentinel):
            # Set the indicator that sentinel contains a list of conditions.
            self._is_multi_test = True
            if all(isinstance(snt, str) for snt in self.sentinel):
                test_type = 'String'
            elif all(isinstance(snt, re.Pattern) for snt in self.sentinel):
                test_type = 'RE'
            elif all(callable(snt) for snt in self.sentinel):
                test_type = 'Function'
        if not test_type:
            raise NotImplementedError('Only Boolean, String, Regular '
                                      'Expression and Callable tests are '
                                      'supported.')
        return test_type

    def set_test_func(self, location: str)->TestType:
        '''Determine the appropriate test function for the sentinel type.

        The test function is set based on based on the sentinel type and
        location value.
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
        if sentinel is a Boolean type:
            sentinel
        if sentinel is a Function type:
            sentinel(line, **context)
        if sentinel is None:
            False
        Args:
            location (str): Indicates how string and regular expression
                sentinels will be applied as a test. One of:
                    'IN', 'START', 'END', 'FULL'
            location is only relevant for String' and 'RE' sentinel types.
            For all other types it will be ignored.
        Returns:
            (Callable[[TriggerTypes, SourceItem, ContextType], TestResult]:
            The test function to apply.
        '''
        test_options = {
            ('String', None):  # The default if location is not specified
                lambda sentinel, line, context: sentinel in line,
            ('String', 'IN'):
                lambda sentinel, line, context: sentinel in line,
            ('String', 'START'):
                lambda sentinel, line, context: line.startswith(sentinel),
            ('String', 'END'):
                lambda sentinel, line, context: line.endswith(sentinel),
            ('String', 'FULL'):
                lambda sentinel, line, context: sentinel == line,
            ('RE', None):  # The default if location is not specified
                lambda sentinel, line, context: sentinel.search(line),
            ('RE', 'IN'):
                lambda sentinel, line, context: sentinel.search(line),
            ('RE', 'START'):
                lambda sentinel, line, context: sentinel.match(line),
            ('RE', 'FULL'):
                lambda sentinel, line, context: sentinel.fullmatch(line),
            ('RE', 'END'):
                NotImplementedError('The location "END" is not compatible with '
                                    'a regular expression test.'),
            ('Boolean', None):
                lambda sentinel, line, context: sentinel,
            ('Function', None):
                lambda sentinel, line, context: sentinel(line, **context),
            (None, None):
                lambda sentinel, line, context: False
            }
        t_method = test_options[(self._sentinel_type, location)]
        if isinstance(t_method, Exception):
            raise t_method
        return t_method

    @property
    def event(self):
        '''TriggerEvent: Information on the result of the Trigger test, see the
        TriggerEvent for details.
        '''
        return self._event

    def evaluate(self, item: SourceItem, **context)->bool:
        '''Call the appropriate test(s) on the supplied item.

        The designated test(s) are applied to the item.  No testing is done to
        ensure that item has an appropriate data type.  If the test passes,
        event and event_name are appropriately updated and test_result=True.
        If the test does not pass, event and event_name are reset to default
        values and test_result=False.

        If sentinel is a list, each sentinel element is used to test item.
        When one of these tests pass, the particular sentinel element that
        passed the test is used to update event and event_name.

        Args:


        Returns:
            (bool): True if the supplied item passed a test, False otherwise.
        '''
        result = False
        self._event.reset()
        if self._is_multi_test:
            for sentinel_item in self.sentinel:
                test_result = self._test_func(sentinel_item, item, context)
                if test_result:
                    result = True
                    self._event.record_event(test_result, sentinel_item,
                                             self.name, self._sentinel_type)
                    break
        else:
            test_result = self._test_func(self.sentinel, item, context)
            if test_result:
                result = True
                self._event.record_event(test_result, self.sentinel,
                                         self.name, self._sentinel_type)
        return result


class SectionBreak(Trigger):  # pylint: disable=function-redefined
    '''Defines the method of identifying the start or end of a section.

    A SectionBreak is a subclass of Trigger, with an additional offset
    attribute and related methods. offset is used to identify a location in the
    Source sequence, and an offset, specifying the distance (in number of
    Source items) between the identified location and the break point.

    Offset is an integer indicating the number of additional Source items to
    include in the section.  The two most popular offset options, have text
    equivalents:
        'After'  -> offset =  0  -> The SectionBreak location is between the
                                    current item and the next.
        'Before' -> offset = -1 -> The SectionBreak location is just before the
                                   current item (Step back 1 item).
    Attributes:
        sentinel (None, bool, int,
                    str or List[str],
                    re.Pattern or List[re.Pattern],
                    Callable or List[Callable]):
            the object(s) used to generate the conditional definition.
        event (TriggerEvent): Information resulting from applying the test.
        See Trigger class for more information on the sentinel and event
        attributes.

        name (str): A text label for the boundary.
        offset (int): Specifies the distance (in number of Source items)
            between the location identified by trigger and the boundary.
    '''
    def __init__(self, sentinel: TriggerOptions, location: str = None,
                 break_offset: OffsetTypes = 'Before', name='SectionBreak'):
        '''Defines trigger and offset for a Boundary point.

        Arguments:
            sentinel (TriggerOptions): Object(s) used to generate the
                conditional definition.
            location (str, optional):  A sentinel modifier that applies to str
                or re.Pattern types of sentinels. For other sentinel types it
                is ignored. One of  ['IN', 'START', 'END', 'FULL', None].
                Default is None, which is treated as 'IN'

            See Trigger class for more information on the sentinel and event
            arguments.

            offset (int, str, optional): The number of Source items
                before (negative) or after (positive) between the item that
                causes a trigger event and the boundary.  offset can also be
                one of
                    'After' =  0, or
                    'Before' = -1
                Defaults to 'Before'.
            name (str, optional): A reference label for the Boundary.
        '''
        super().__init__(sentinel, location, name)
        self._offset = -1  # Equivalent to 'Before'
        self.offset = break_offset
        # Condition tracking attribute for internal use
        self._count_down = None

    @property
    def offset(self)->int:
        '''int: The number of Source items before (negative) or after
        (positive) between the item that causes a trigger event and the
        boundary.
        '''
        return self._offset

    @offset.setter
    def offset(self, break_offset: OffsetTypes):
        '''Set the offset value converting the strings 'After' to  0, and
        'Before' to -1.

        Argument:
            offset (int, str): An integer or one of ['After', 'Before'].
        Raises:
            ValueError if offset is not an integer or a string containing one
                of ['After', 'Before']
        '''
        offset_value = self._offset # If new value fails keep original.
        try:
            offset_value = int(break_offset)
        except ValueError as err:
            if isinstance(break_offset, str):
                if 'before' == break_offset.lower():
                    offset_value = -1
                elif 'after' == break_offset.lower():
                    offset_value = 0
            else:
                msg = ('Offset must be an integer or one of'
                       '"Before" or "After";\t Got {repr(offset)}')
                raise ValueError(msg) from err
        self._offset = offset_value


    def check(self, item: SourceItem, source: BufferedIterator, **context):
        '''Check for a Break condition.

        If an Active count down situation exists, continue the count down.
        Otherwise, apply the trigger test.  If the Trigger signals a break,
        set the appropriate line location for the break based on the offset
        value.

        Arguments:
            item (SourceItem): The current Source item to apply a boundary
                check to.
            source (BufferedIterator): The primary source from which item is
                obtained.  Access to this object is required for negative
                offsets.
            **context (Dict[str, Any], optional): Additional information to be
                passed to the trigger object.
        '''
        logger.debug('in section_break.check')
        # Check for a Break condition
        if self._count_down is None:  # No Active Count Down
            # apply the trigger test.
            is_event = self.evaluate(item, **context)
            if is_event:
                logger.debug(f'Break triggered by {self.event.test_name}')
                is_break = self.set_line_location(source)
            else:
                is_break = False
        elif self._count_down == 0:  # End of Count Down Reached
            logger.debug(f'Line count down in {self.name} completed.')
            self._count_down = None  # Remove Active Count Down
            is_break = True
            source.step_back = 1  # Save current line for next section
        elif self._count_down > 0:  #  Active Count Down Exists
            logger.debug(f'Line count down in {self.name} Continuing;\t'
                         f'Count down now at {self._count_down}')
            self._count_down -= 1   #  Continue Count Down
            is_break = False
        return is_break

    def set_line_location(self, source: BufferedIterator):
        '''Set the appropriate line location for a break based on the offset
        value.

        Arguments:
            source (BufferedIterator): The primary source from which item is
                obtained.  Access to this object is required for negative
                offsets.
        Returns (bool): True if the current BufferedIterator line pointer is
            at a break point.  False otherwise
        '''
        if self.offset < 0: # Save current line for next section
            logger.debug(f'Stepping back {-self.offset:d} lines')  # pylint: disable=invalid-unary-operand-type
            source.step_back = -self.offset  # pylint: disable=invalid-unary-operand-type
            is_break = True
        else: # Use more lines before activating break
            logger.debug(f'Using {self.offset} more lines.')
            self._count_down = self.offset  # Begin Active Count Down
            is_break = False
        return is_break

#%% Rule Class
class Rule(Trigger):
    '''Defines action to take on an item depending on the result of a test.

    A Rule is a subclass of Trigger, with two additional attributes and
    related methods:
        pass_method RuleMethod: The method to apply if the test passes.
        fail_method RuleMethod: The method to apply if the test fails.

    An additional default_method class attribute defines the action to assign
    for undefined pass or fail methods.

    All three methods (pass, fail, default) should have the following signature:
        rule_method(test_object: SourceItem, event: TriggerEvent, **context)
                Name              Kind                       Type
             test_object       Positional or Keyword      SourceItem
             event             Positional or Keyword      TriggerEvent
             context           Var Keyword                Any

    All three methods (pass, fail, default) should return the same data type.
        No checking is done to validate this.

    In addition to a callable, the pass, fail and default attributes can be
    the names of standard actions:
        'Original': return the item being.
        'Event': return the self.event object.
        'None': return None
        'Blank': return ''  (an empty string)

    Attributes:
        sentinel (None, bool, int,
                    str or List[str],
                    re.Pattern or List[re.Pattern],
                    Callable or List[Callable]):
            the object(s) used to generate the conditional definition.
        event (TriggerEvent): Information resulting from applying the test.
        See Trigger class for more information on the sentinel and event
        attributes.

        name (str): A text label for the rule.
        pass_method (Callable, str, optional): The method to apply if the test
            passes.
        fail_method (Callable, str, optional): The method to apply if the test
            fails.
    ClassLevelAttribute:
        default_method (Callable, str, optional): The method to use as the
            pass or fail method if not specified defaults to 'Original'.
    '''

    #The default method below returns the supplied item.
    _default_method = None

    def __init__(self, sentinel: TriggerOptions, location=None,
                 pass_method: RuleMethodOptions = None,
                 fail_method: RuleMethodOptions = None,
                 name='Rule'):
        '''Apply a method based on trigger test result.

        Arguments:
            sentinel (TriggerOptions): Object(s) used to generate the
                conditional definition.
            location (str, optional):  A sentinel modifier that applies to str
                or re.Pattern types of sentinels. For other sentinel types it
                is ignored. One of  ['IN', 'START', 'END', 'FULL', None].
                Default is None, which is treated as 'IN'

            See Trigger class for more information on the sentinel and event
            arguments.

            name (str, optional): A reference label for the Rule.

            pass_method (RuleMethodOptions): A function, or the name of a
                standard action to be implemented if the test passes on the
                supplied item.
            fail_method (RuleMethodOptions): A function, or the name of a
                standard action to be implemented if the test fails on the
                supplied item.

        Both pass_method and fail_method should have one of the following
        argument signatures:
            rule_method(item: SourceItem)
            rule_method(item: SourceItem, event: TriggerEvent)
            rule_method(item: SourceItem, event: TriggerEvent, **context)
        Instead of a callable, pass_method and fail_method can be the name of a
        standard actions:
                'Original': return the item being.
                'Event': return the self.event object.
                'None': return None
                'Blank': return ''  (an empty string)
        Both pass_method and fail_method should return the same data type. No
        checking is done to validate this.
        '''
        super().__init__(sentinel, location, name)
        self.default_method = lambda test_object, event, **context: test_object
        self.pass_method = self.set_method(pass_method)
        self.fail_method = self.set_method(fail_method)

    @staticmethod
    def drop_context(rule_method: ItemEventFunc, test_object: SourceItem,   # pylint: disable=unused-argument
                     event: TriggerEvent,
                     **context)->RuleResult: # pylint: disable=unused-argument
        '''wrapper that removes context.

        This wrapper is provided to easily use functions that don't include
        the context Var Keyword.

        Args:
            rule_method (ItemEventFunc): A function with the signature:
                rule_method(test_object: SourceItem, event: TriggerEvent)
            test_object (SourceItem): The value to be tested.
                        item (SourceItem): The value to be tested.
            event (TriggerEvent): Trigger test result information.  See the
                TriggerEvent class for more information.
            **context (Dict[str, Any], Optional): Any additional information to
                be passed as keyword arguments to a sentinel function.  Ignored
                for other sentinel types.
        Returns:
            RuleResult: The result of the supplied rule_method when called with
            test_object, event.
         '''
        return rule_method(test_object, event)

    @staticmethod
    def single_argument(rule_method: SingleItemFunc, test_object: SourceItem,   # pylint: disable=unused-argument
                        event: TriggerEvent,   # pylint: disable=unused-argument
                        **context)->RuleFunc:  # pylint: disable=unused-argument
        '''Wrapper that removes event & context parameters.

        This wrapper is provided to allow for use of single argument functions
        as Rule methods by using the signature expected for a Rule method, but
        calling the wrapped function with only the test_item argument.

        Args:
            rule_method (ItemEventFunc): A function with the signature:
                rule_method(test_object: SourceItem)
            test_object (SourceItem): The value to be tested.
                        item (SourceItem): The value to be tested.
            event (TriggerEvent): Trigger test result information.  See the
                TriggerEvent class for more information.
            **context (Dict[str, Any], Optional): Any additional information to
                be passed as keyword arguments to a sentinel function.  Ignored
                for other sentinel types.
        Returns:
            RuleResult: The result of applying rule_method to the supplied
                test_object.
        '''
        return rule_method(test_object)

    @staticmethod
    def standard_action(action_name: str)->RuleFunc:
        '''Convert a Method name to a Standard Function.

        Take the name of a standard actions and return the matching function.

        Argument:
            action_name (str): The name of the standard action.
                Valid Action names are:
                    'Original': return the item being.
                    'Event': return the self.event object.
                    'None': return None
                    'Blank': return ''  (an empty string)
        Raises: ValueError If the string supplied is not one of the valid
            action names.
        Returns:
            RuleFunc: One of the standard action functions.
        '''
        action_dict = {
            'Original': lambda test_object, event, **context: test_object,
            'Event':  lambda test_object, event, **context: event,
            'Blank':  lambda test_object, event, **context: '',
            'None':  lambda test_object, event, **context: None
            }
        use_function = action_dict.get(action_name)
        if not use_function:
            raise ValueError('Standard Action names are: '
                             '["Original", "Event", "None", "Blank"]'
                             f'Got {action_name}')
        return use_function

    def set_method(self, rule_method: RuleMethodOptions)->RuleFunc:
        '''Convert the supplied function or action name to a Function with
        the standard signature.

        Argument:
            rule_method (RuleMethodOptions): A function, or the name of a
                standard action.
        Raises: ValueError If rule_method is a string and is not one of the
            valid action names, or if rule_method is a function and does not
            have length 1, 2, or 3  argument signature.
        Returns:
            RuleFunc: A function with the standard Rule Method argument
            signature:
         rule_method(test_object: SourceItem, event: TriggerEvent, **context)
        '''
        # FIXME use inspect.getfullargspec
        #FullArgSpec(args=['line', 'event'], varargs=None, varkw='context',
        #defaults=('', None), kwonlyargs=[], kwonlydefaults=None, annotations={})
        # Count args, check for varkw=None
        if not rule_method:
            use_function = self.default_method
        elif isinstance(rule_method, str):
            use_function = self.standard_action(rule_method)
        else:
            arg_spec = inspect.getfullargspec(rule_method)
            if len(arg_spec.args) == 1:
                use_function = partial(self.single_argument, rule_method)
            elif ((len(arg_spec.args) == 2) & (arg_spec.varkw is None)):
                use_function = partial(self.drop_context, rule_method)
            elif ((len(arg_spec.args) == 2) & (arg_spec.varkw is not None)):
                use_function = rule_method
            else:
                raise ValueError('Invalid function type.')
        return use_function

    @property
    def default_method(self)->RuleFunc:
        '''The Rule method to be used whenever the instance pass_method
        or fail_method is not supplied.

        Returns:
            RuleFunc: A function with the standard Rule Method argument
                signature:
        '''
        return self._default_method

    @default_method.setter
    def default_method(self, rule_method: RuleMethodOptions):
        '''Convert the supplied function or action name to a Function with
        the standard signature and set it as the class default method.

        Argument:
            rule_method (RuleMethodOptions): A function, or the name of a
                standard action.
        '''
        self._default_method = self.set_method(rule_method)

    def apply(self, test_object, **context)->RuleResult:
        '''Apply the Rule to the supplied test item and return the output of
        the relevant method based on the test result.

        Argument:
            test_object (SourceItem): The object to be tested.

        Returns:
            RuleResult: The result of applying the relevant rule_method to the
                supplied test_object.
        '''
        is_match = self.evaluate(test_object, **context)
        if is_match:
            result = self.pass_method(test_object, self.event, **context)
        else:
            result = self.fail_method(test_object, self.event, **context)
        return result


    ############# Done To Here  ##################


class LineParser():  # TODO Convert this into RuleSet
    def __init__(self, parsing_rules: List[Rule],
                 default_parser: Callable = None):
        self.parsing_rules = parsing_rules
        default_rule = Rule(True, pass_method=default_parser, name='Default')
        self.parsing_rules.append(default_rule)

    def parse(self, source, **context):
        logger.debug('In line_parser')
        for line in source:
            logger.debug(f'In line_parser, received line: {line}')

            for rule in self.parsing_rules:
                parsed_lines = rule.apply(line, **context)
                if rule.event.test_result:
                    break

            if parsed_lines is not None:
                for parsed_line in parsed_lines:
                    yield parsed_line


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
    default_start = SectionBreak(True, name='AlwaysBreak', break_offset='Before')
    # A SectionBreak that never triggers, causing the section to continue to
    # the end of the source.
    default_end = SectionBreak(False, name='NeverBreak')

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
                self.context['Event'] = break_trigger.event.test_value
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

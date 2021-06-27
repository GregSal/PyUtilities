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
from pathlib import Path
from inspect import isgeneratorfunction
from functools import partial, partialmethod
from typing import Dict, List, Sequence, TypeVar, Iterator, Any, Callable, Union
import pandas as pd

from file_utilities import clean_ascii_text
from data_utilities import true_iterable
import logging_tools as lg

from buffered_iterator import BufferedIterator
from buffered_iterator import BufferedIteratorValueError
from buffered_iterator import BufferOverflowWarning
from buffered_iterator import BufferedIteratorEOF
T = TypeVar('T')
# TODO create more type definitions: Line, ...
# TODO more explicit generic type definitions
# TODO DIstinguish between Sentinal and sentinal output
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


#%% Logging
logger = lg.config_logger(prefix='Text Processing', level='DEBUG')


#%% Exceptions
class TextReadWarnings(UserWarning): pass


class TextReadException(Exception): pass


class TextReadBreaks(GeneratorExit):
    '''Base class for indicating that a Section has changed.'''

    def __init__(self, *args, context: Dict[str, Any] = None, **kwargs):
        super().__init__(*args, **kwargs)
        if context:
            self.context = context
        else:
            self.context = dict()

    def get_context(self):
        '''Return the context that existed when StopSection was raised.'''
        return self.context


class StartSection(TextReadBreaks):
    '''A Section has started through activation of a trigger.'''
    pass


class StopSection(TextReadBreaks):
    '''A Section has ended through activation of a trigger.'''
    pass


class IteratorEOF(TextReadBreaks):
    '''A Section has ended through end of source.'''


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
    # Units to recognize:
    # %, CU, cGy, Gy, deg, cm, deg, MU, min, cc, cm3, MU/Gy, MU/min, cm3, cc
    #find_num = re.compile(number_value_pattern)
    find_num = re.findall(number_value_pattern, text)
    if find_num:
        value, unit = find_num[0]
        return value
    return text


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

    def parser(self, line: str, *args, **kwargs) -> ParseResults:
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
    parsed_line_iter = BufferedIterator(parsed_lines, buffer_size=max_lines)
    for parsed_line in parsed_line_iter:
        completed_line = False
        completed_section = None  # Stores raised StopSection exceptions
        # If the first line doesn't not have exactly 2 parts don't join
        # subsequent lines to it.
        if len(parsed_line) != 2:
            completed_line = True
        while not completed_line:
            # Trap Section breaks so that the current line is returned before
            # the section break is raised
            try:
                next_line = parsed_line_iter.look_ahead()
            except (StopSection, BufferOverflowWarning) as eol:
                completed_line = True
                #completed_section = eol
            else:
                if len(next_line) == 1:
                    parsed_line[1] = join_strings(parsed_line[1], next_line[0],
                                                  join_char)
                    parsed_line_iter.skip()
                else:
                    completed_line = True
        yield parsed_line
        #if completed_section:
        #    # If StopSection was raised by look_ahead, re-raise it after
        #    # yielding the current line.
        #    raise completed_section


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


#%% Classes
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


class Rule():
    @staticmethod
    def default_template(test_object, sentinel, *args,
                         default_return=None, **kwargs):
        '''default_method to be set using partial.
        '''
        if 'Original' in default_return:
            return [test_object]
        if 'Sentinel' in default_return:
            return sentinel  # TODO The format for sentinel should depend on its type
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
            sentinel
            context
        default_method: str, one of:
            'None'  -> returns None
            'Original' -> returns test_object
            'Sentinel' -> returns sentinel
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
        default_rule = Rule(Trigger(True), default_parser, name='Default')
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
            is_break, sentinel = self.trigger.apply(line, context)
            if is_break:
                logger.debug(f'Break triggered by {sentinel}')
                self.active_sentinel = sentinel
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


class SectionBoundaries():
    def __init__(self,
                 start_section: List[SectionBreak] = None,
                 end_section: List[SectionBreak] = None):
        # start_section = None -> Always Break
        # end_section = None -> Never Break
        if not start_section:
            self.start_section = [SectionBreak(Trigger(True),
                                              name='AlwaysBreak')]
        elif isinstance(start_section, SectionBreak):
            self.start_section = [start_section]
        else:
            self.start_section = start_section

        if not end_section:
            self.end_section = [SectionBreak(Trigger(False),
                                            name='NeverBreak')]
        elif isinstance(end_section, SectionBreak):
            self.end_section = [end_section]
        else:
            self.end_section = end_section

    def check(self, line, source: BufferedIterator, location='End',
              **context):
        logger.debug(f'In SectionBoundaries.check, received line: {line}')
        if 'Start' in location:
            break_triggers = self.start_section
            trigger_exception = StartSection
        else:
            break_triggers = self.end_section
            trigger_exception = StopSection
        for break_trigger in break_triggers:
            logger.debug(f'Checking Trigger: {break_trigger.name}')
            is_break = break_trigger.check(line, source, **context)
            if is_break:
                logger.debug('Section Break Detected')
                break_context = {
                    'Sentinel': break_trigger.active_sentinel,
                    'Break': break_trigger.name,
                    'Location': location
                    }
                #raise BufferError('STOP')
                raise trigger_exception(context=break_context)
        logger.debug('No Break Triggered')
        return line

    def scan(self, location, source, section_name='Boundary', **context):
        for line in source:
            yield self.check(line, source, location, **context)
        break_context = {
            'Sentinel': 'End of Source',
            'Break': 'EOF',
            'Location': location
            }
        raise IteratorEOF(context=break_context)

    def check_start(self, **context):
        # TODO Is check_start Necessary?
        return partial(self.check, location='Start', **context)

    def check_end(self, **context):
        # TODO Is check_end Necessary?
        return partial(self.check, location='End', **context)


#%% Reader
class SectionReader():
    def __init__(self,
                 section_name = 'SectionReader',
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

    def read(self, buffered_source, **context):
        self.context = context
        section_iter = cascading_iterators(buffered_source,
                                           self.section_stages)
        for item in section_iter:
            yield item


#%% Section
class Section():
        # check for start
        # read section while checking for end
        # Apply Section Formatting ->
        # TODO Use property methods to update context
    def __init__(self,
                 section_name = 'Section',
                 boundaries: SectionBoundaries = None,
                 reader: SectionReader = None,
                 aggregate: Callable = None):
        self.section_name = section_name
        self.context = dict()
        self.scan_status = 'Not Started'
        self.source = None
        if reader:
            self.reader = reader
        else:
            self.reader = SectionReader()
        if boundaries:
            self.boundaries = boundaries
        else:
            self.boundaries = SectionBoundaries()
        if aggregate:
            self.aggregate = aggregate
        else:
            self.aggregate = list  # TODO create subclass of list that returns ParsedStringSource

    def list_aggregate(self, section_lines: ParsedStringSource) -> List[Any]:
        '''Iterate through section.
        '''
        # TODO list_aggregate is not needed
        list_output = [line for line in section_lines]
        return list_output

    def catch_break(self, buffered_source):
        break_context = {'Status': 'No Break Found'}
        try:
            status = 'Scan In Progress'
            break_context['Status'] = 'No Break Found'
            for item in buffered_source:
                yield item
        except (RuntimeError) as err:
            break_context['Status'] = 'RuntimeError'
            logger.warning(f'RuntimeError Encountered: {err}')
            status = 'Scan Complete'
        except (BufferedIteratorEOF, IteratorEOF, StopIteration) as eof:
            break_context['Status'] = 'End of Source'
            status = 'Scan Complete'
        except (StartSection, StopSection) as marker:
            break_context = marker.get_context()
            location = break_context['Location']
            break_context['Status'] = f'{location} of {self.section_name}'
            status = 'Scan Complete'
        finally:
            self.context.update(break_context)
            self.scan_status = status
            logger.debug(f'break_context:\t{break_context["Status"]}')
    def find_start(self, buffered_source):
        # Skip lines before start
        scan_start = self.boundaries.scan('Start', buffered_source,
                                          section_name=self.section_name,
                                          **self.context)
        skipped_lines = [row for row in self.catch_break(scan_start)]
        self.scan_status = 'Not Started'
        return skipped_lines

    def initialize_source(self, source, context):
        if isinstance(source, BufferedIterator):
            buffered_source = source
        else:
            buffered_source = BufferedIterator(source)
        self.source = buffered_source

    def initialize_scan(self, source, start_search=True,
                        **context)->BufferedIterator:
        self.context.update(context)
        self.initialize_source(source, context)
        if start_search:
            skipped_lines = self.find_start(self.source)
        else:
            skipped_lines = []
        logger.debug(f'Starting New Section: {self.section_name}.')
        self.context['Current Section'] = self.section_name
        return skipped_lines

    def section_gen(self)->BufferedIterator:
        '''Create the iterator that will read source until the section ends.
        '''
        section_scan = self.boundaries.scan('End', self.source,
                                            section_name=self.section_name,
                                            **self.context)
        section_iter = BufferedIterator(self.catch_break(section_scan))
        return section_iter

    def scan(self, source, start_search=True, **context):
        #TODO Check if Section.scan is still used
        section_scan = self.initialize_scan(source, start_search, **context)
        self.scan_status = 'Scan Starting'
        while 'Complete' not in self.scan_status:
            scan_iter = self.reader.read(self.catch_break(section_scan),
                                         **self.context)
            yield scan_iter
        print(f'Done scanning {self.section_name}')

    def read_gen(self, read_method, section_iter):
        while 'Complete' not in self.scan_status:
            section_item = read_method(section_iter, **self.context)
            yield section_item

    def group_reader_gen(self, reader_list, section_iter):
        while 'Complete' not in self.scan_status:
            group_read = (
                    sub_rdr.read(section_iter, **self.context)
                    for sub_rdr in reader_list
                    )
            section_item = list(group_read)
            yield section_item

    def read_section(self):
        reader = self.reader
        section_iter = self.section_gen()
        # TODO Make the list of readers test more general i.e. any sequence of readers
        # TODO the test for reader type can be done in Section.__init__
        if isinstance(reader, list):
            section_items = self.group_reader_gen(reader, section_iter)
        elif isgeneratorfunction(reader.read):
            section_items = reader.read(section_iter, **self.context)
        else:
            section_items = self.read_gen(reader.read, section_iter)
        return section_items

    def read(self, source, start_search=True, **context)->Any:
        self.initialize_scan(source, start_search, **context)
        self.scan_status = 'Scan Starting'
        section_items = self.read_section()
        section_aggregate = self.aggregate(section_items)
        return section_aggregate

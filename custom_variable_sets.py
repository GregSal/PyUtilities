'''CustomVariable objects with defined validity conditions and defaults.
'''

from pathlib import Path
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Optional, List, Dict, Tuple, Set, Any, Union
from file_utilities import FileTypes, set_base_dir, make_full_path
from file_utilities import PathInput, FileTypeError
from data_utilities import true_iterable, logic_match
import logging_tools

# pylint: disable=invalid-name
VariableSelection = Union[str, List[str], Dict[str, Any]]
VariableValues = Union[Any, List[Any], Dict[str, Any]]
ErrorString = Optional[str]
IntValue = Union[str, float, int]


class VariableError(Exception):
    '''Base Exception for CustomParameter
    '''
    pass


class NotValidError(VariableError):
    '''Base Exception for invalid CustomVariable value
    '''
    pass


class NotVariableError(VariableError):
    '''The class does not inherit from the CustomVariable class
    '''
    pass


class NoVariableError(VariableError):
    '''The value request from the CustomVariable set did not contain a valid
    CustomVariable name.
    '''
    pass


class UnMatchedValuesError(VariableError):
    '''The list of values does not match with the expected number of values.
    '''
    pass


class UpdateError(VariableError):
    '''An error occurred attempting to modify a CustomVariable attribute.'''
    pass


class MissingRequiredError(VariableError):
    '''A required CustomVariable was not initialized.'''
    pass


def get_class_name(class_type: type)->str:
    '''parse the full class type string to get the abbreviated class name.
    It expects the class string to be in the form:
        "<class '__module__.ClassName'>"
    Returns:
        str: The name of the class.
    '''
    # TODO Move to data_utilities
    full_class_name = str(class_type)
    name_portion = full_class_name.replace("<class '", "").replace("'>", "")
    class_name = name_portion.rsplit('.', 1)[-1]
    return class_name


class CustomVariable(ABC):
    '''This is an abstract base class for all of the CustomVariable sub-classes.
    '''
    _type = object
    initial_settings: Dict[str, Any] = {'default': None}

    @abstractmethod
    def __init__(self, value=None, name=None, messages=None, **kwds):
        '''Create a new instance of the CustomVariable object.'''
        super().__init__()
        self.initialized = False
        self._value = None
        self.default = None
        self.status = BaseException
        if name:
            self._name = name
        else:
            self._name = get_class_name(type(self))
        self._messages = dict(not_valid='')
        self.initialize_messages(messages)
        if value is not None:
            self.set_value(value)
        self.initialize_attributes(kwds)

    def get_name(self):
        '''Return the name of the CustomVariable.
        '''
        return self._name

    name = property(get_name)

    def get_type(self):
        '''Return the name of the CustomVariable.
        '''
        return self._type

    value_type = property(get_type)

    def initialize_attributes(self, kwds):
        '''Add values for all attributes.
        '''
        settings = self.initial_settings.copy()
        settings.update(kwds)
        for attr, value in settings.items():
            self.__setattr__(attr, value)

    def initialize_messages(self, messages: dict):
        '''Update message templates.
        '''
        message_templates = dict(
            not_valid='{new_value} is an invalid value for {name}.',
            display='{name} CustomVariable of class {cls},\n'
                    '\tCurrent value is:\t{value}\n'
                    '\tDefault value is:\t{default}'
            )
        if messages:
            message_templates.update(messages)
        self._messages.update(message_templates)

    def set_attributes(self, **settings):
        '''Update values for the supplied attributes.
        '''
        for attr, value in settings.items():
            self.__setattr__(attr, value)

    def update_messages(self, messages: dict):
        '''Update message templates.
        '''
        self._messages.update(messages)

    def build_message(self, message: str, **value_set)->str:
        '''Return a message string using format and a message template.
        if message is a key in self.messages use the corresponding template,
        otherwise treat message as a template.
        '''
        values = self.__dict__
        values.update({'name': self.name,
                       'value': str(self),
                       'value_type': get_class_name(self.value_type),
                       'cls': get_class_name(type(self))})
        values.update(value_set)
        msg = self._messages[message]
        msg_str = msg.format(**values)
        return msg_str

    @abstractmethod
    def check_validity(self, value)->bool:
        '''Test to see if value is a valid CustomVariable value.
        If valid return True.
        If not valid, build an error message, set the status attribute to
        NotValidError and return False.
        '''
        if isinstance(value, self.value_type):
            return True
        msg = self.build_message('not_valid', new_value=value)
        self.status = NotValidError(msg)
        return False

    def get_value(self):
        '''Return the set value of the CustomVariable.
        If no value is defined return the default value.
        '''
        if self._value is None:
            if self.default is None:
                return None
            return self.value_type(self.default)
        return self.value_type(self._value)

    def set_value(self, value):
        '''Set a new value for CustomVariable.
        '''
        if self.check_validity(value):
            self._value = self._type(value)
            self.initialized = True
        else:
            raise self.status

    value = property(get_value, set_value)

    def copy(self):
        '''Duplicate the CustomVariable including all relevant attributes
        '''
        cls = type(self)
        attrs = self.__dict__
        copied = cls(**attrs)
        return copied

    def __str__(self)->str:
        '''A string version of the value
        '''
        return str(self.get_value())

    def disp(self)->str:
        '''A template formatted string
        '''
        return self.build_message('display')

    def __eq__(self, value):
        '''Test to see if self is set to "value".
        Equality is only based on value not on other attributes.
        '''
        if self.check_validity(value):
            return self.get_value() == value
        return False

    def reset_value(self):
        '''Set CustomVariable to it's default value.'''
        self._value = self.default

    def drop_value(self):
        '''Set CustomVariable to it's default value.'''
        self._value = None
        self.initialized = False

    def set_default(self, value=None):
        '''set the default value of CustomVariable to the supplied "value".
        if no value is supplied set the default to the current value of the
        CustomVariable.
        '''
        if value is None:
            self.default = self._value
        elif self.check_validity(value):
            self.default = value
        else:
            raise self.status

    def is_initialized(self):
        '''Test whether a value has been explicitly assigned to the CustomVariable
        '''
        return self.initialized


class StringV(CustomVariable):
    '''A String CustomVariable with:
        Optional limited values (value_set), or
        Optional size limit (max_length)
        If value_set is defined, the size limit will not be checked.
    '''
    _name = 'string_variable'
    _type = str

    def __init__(self, *args, value_set=None, max_length=None, **kwds):
        '''Create a new instance of the string CustomVariable.
        If both value and value_set are given, include value in the value set.
        '''
        self._value = None
        self._max_length = None # type int
        self._value_set = set() # type: Set[str]
        super().__init__(*args, **kwds)
        if value_set is not None:
            for item in value_set:
                self.add_item(item)
            if self._value is not None and self._value not in self.value_set:
                self.add_item(self._value)
        if max_length is not None:
            self.max_length = max_length

    def get_max_length(self):
        '''Getter for max_length.'''
        return self._max_length

    def set_max_length(self, length: int = None):
        '''If valid, change maximum string length.
        Arguments:
            length {int} -- The new maximum string length limit.
        '''
        if length is None:
            self._max_length = None
        else:
            max_length = int(length)
            if (self.value is None) or (max_length >= len(self.value)):
                self._max_length = max_length
            else:
                msg = self.build_message('length_conflict',
                                         max_length=max_length)
                raise UpdateError(msg)

    max_length = property(get_max_length, set_max_length)

    def get_value_set(self):
        '''Getter for value_set.'''
        return self._value_set

    value_set = property(get_value_set)

    def add_item(self, item: str):
        '''Add additional items to the set of possible values.
        Arguments:
            item {str} -- The item to add to the list of valid string values
        '''
        if super().check_validity(item):
            self._value_set.add(item)
        else:
            raise self.status

    def drop_item(self, item: str):
        '''Drop an item from the set of possible values.
        Arguments:
            item {str} -- The item to drop from the list of valid string
                values.
        '''
        if item in self._value_set:
            if self.value == item:
                msg = self.build_message('value_conflict', new_value=item)
                raise UpdateError(msg)
            self._value_set.remove(item)
        else:
            msg = self.build_message('not_in_value_set', new_value=item)
            raise UnMatchedValuesError(msg)

    def check_validity(self, value)->bool:
        '''Check that value is a string.
        If the value is not valid the status attribute is set with the error
        message describing the reason the value is not valid.
        Arguments:
            value {str} -- The value to be tested.
        Returns
            True if the value is valid, False otherwise.
        '''
        if not super().check_validity(value):
            return False
        if self._value_set:
            if value not in self._value_set:
                msg = self.build_message('disp_value_set', new_value=value)
                self.status = NotValidError(msg)
                return False
        elif self._max_length:
            if len(value) > self._max_length:
                msg = self.build_message('too_long', new_value=value)
                self.status = NotValidError(msg)
                return False
        return True

    def initialize_messages(self, messages: Dict[str, str]):
        '''Update message templates.
        Arguments:
            messages -- A dictionary of message templates referencing
                StringV attributes.
        '''
        message_templates = dict(
            too_long='{new_value} is longer than the maximum allowable '
                     'length of {max_length}.',
            disp_value_set='{new_value} is an invalid value for {name}.'
                           '\n\tPossible values are: {value_set}',
            not_in_value_set='{new_value} is not in the set of possible '
                             'values:\n\t{value_set}',
            value_conflict='{value} cannot be removed from the list of '
                           'possible values because it is the current value',
            length_conflict='new maximum length of {max_length} is less '
                            'than the length of the current value: {value}.'
                            '\n\tmax_value was not changed.',
            value_set='\n\tPossible values are:\t{value_set}',
            max_length='\n\tThe maximum allowable length is: {max_length}'
            )
        if messages:
            message_templates.update(messages)
        super().initialize_messages(message_templates)

    def build_message(self, message: str, **value_set)->str:
        '''Return a message string using format and a message template.
        if message is a key in self.messages use the corresponding template,
        otherwise treat message as a template.
        Arguments:
            message {str} -- Either a key in self.messages, or
                a custom message template.
            value_set {dict} -- value definition overrides for the message
                templates.
        '''
        values = {'max_length': self.max_length,
                  'value_set': self.value_set}
        values.update(value_set)
        return super().build_message(message, **values)

    def disp(self)->str:
        '''A template formatted string
        '''
        value_str = super().disp()
        if self._value_set is not None:
            disp_str = value_str + self.build_message('value_set')
        elif self.max_length is not None:
            disp_str = value_str + self.build_message('max_length')
        return disp_str


class IntegerV(CustomVariable):
    '''An Integer CustomVariable with optional:
        maximum and minimum values (max_value, min_value), or
        a limited set of values (value_set)
    If value_set is defined, the max_value and min_value will not be checked.
    '''
    _name = 'integer_variable'
    _type = int

    def __init__(self, *args, value_set=None, min_value=None, max_value=None,
                 **kwds):
        '''Create a new instance of the integer CustomVariable.
        If both value and value_set are given, include value in the value set.
        '''
        self._value = None # type int
        self._min_value = None # type int
        self._max_value = None # type int
        self._value_set = set() # type: Set[int]
        super().__init__(*args, **kwds)
        if value_set is not None:
            self.add_items(value_set)
            if self._value is not None and self._value not in self.value_set:
                self.add_items(self._value)
        if min_value is not None:
            self.min_value = min_value
        if max_value is not None:
            self.max_value = max_value

    def int_value(self, value: IntValue)->int:
        '''Convert a string or float representation of an integer to an integer.
        '''
        try:
            float_value = float(value)
        except ValueError:
            msg = self.build_message('not_valid', new_value=value)
            raise NotValidError(msg)
        if float_value.is_integer():
            int_value = int(float_value)
        else:
            msg = self.build_message('not_valid', new_value=value)
            raise NotValidError(msg)
        return int_value

    def no_limit_conflict(self, limit_type: str, new_limit: int,
                          other_limit: int, current_value: int)->bool:
        '''Check for limit conflicts.
        Compare new Maximum or Minimum limit with the opposing limit and
        the current value to identify any conflicts.
        Arguments:
            limit_type {str} -- The type of limit, can be:
                "Maximum" or "Minimum".
            new_limit {int} -- The limit being tested.
            other_limit {int} -- The current opposite limit value.
            current_value {int} -- The current CustomVariable value.
        Raises
            UpdateError -- if a limit conflict exists.
            ValueError -- If limit_type is not valid.
        Returns
            True if no limit conflict exists.
        '''

        def bad_limit(limit_type: str, new_limit: int, value: int)->bool:
            '''compare values based on limit type.
            if limit_type is Maximum return True if new_limit < value.
            if limit_type is Minimum return True if new_limit > value.
        Arguments:
            limit_type {str} -- The type of limit, can be:
                "Maximum" or "Minimum".
            new_limit {int} -- The limit being tested.
            value {int} -- The value to test new_limit against.
        Raises:
            ValueError -- If limit_type is not valid.
        Returns
            True new_limit is on the wrong side of value.
            False if  new_limit is OK or value is None.
        '''
            is_bad = False
            if value is None:
                is_bad = False
            elif limit_type == 'Minimum':
                is_bad = (new_limit > value)
            elif limit_type == 'Maximum':
                is_bad = (new_limit < value)
            else:
                raise ValueError(
                    'limit_type must be "Minimum" or "Maximum"')
            return is_bad

        direction = {'Minimum': 'greater', 'Maximum': 'less'}
        opposite = {'Minimum': 'Maximum', 'Maximum': 'Minimum'}
        msg_names = {'limit_type': limit_type, 'limit_value': new_limit,
                     'direction': direction[limit_type],
                     'conflict_type': opposite[limit_type], 'value': None}
        if bad_limit(limit_type, new_limit, other_limit):
            msg_names['value'] = other_limit
            msg = self.build_message('limit_conflict', **msg_names)
            raise UpdateError(msg)
        elif bad_limit(limit_type, new_limit, current_value):
            msg_names.update({'conflict_type': 'value',
                              'value': current_value})
            msg = self.build_message('limit_conflict', **msg_names)
            raise UpdateError(msg)
        return True

    def get_min_value(self):
        '''Getter for min_value.'''
        return self._min_value

    def set_min_value(self, min_limit: int = None):
        '''If valid, change the minimum value.
        Arguments:
            min_limit {int} -- The new minimum value.
        '''
        if min_limit is None:
            self._min_value = None
        else:
            min_value = self.int_value(min_limit)
            if self.no_limit_conflict('Minimum', min_value,
                                      self.max_value, self.value):
                self._min_value = min_value

    min_value = property(get_min_value, set_min_value)

    def get_max_value(self):
        '''Getter for max_value.'''
        return self._max_value

    def set_max_value(self, max_limit: int = None):
        '''If valid, change the maximum value.
        Arguments:
            max_limit {int} -- The new maximum value.
        '''
        if max_limit is None:
            self._max_value = None
        else:
            max_value = self.int_value(max_limit)
            if self.no_limit_conflict('Maximum', max_value,
                                      self.min_value, self.value):
                self._max_value = max_value

    max_value = property(get_max_value, set_max_value)

    def get_value_set(self):
        '''Getter for value_set.'''
        return self._value_set

    value_set = property(get_value_set)

    def add_items(self, items):
        '''Add additional items to the set of possible values.
        Arguments:
            items{int, List[int]} -- The items to add to the list of valid
                integer values
        '''
        if true_iterable(items):
            item_list = items
        else:
            item_list = (items,)
        for item in item_list:
            if super().check_validity(item):
                int_item = self.int_value(item)
                self._value_set.add(int_item)
            else:
                raise self.status

    def drop_item(self, item: int):
        '''Drop an item from the set of possible values.
        Arguments:
            item {int} -- The item to drop from the list of valid integer
                values.
        '''
        int_value = self.int_value(item)
        if self.value == int_value:
            msg = self.build_message('value_conflict', new_value=item)
            raise UpdateError(msg)
        elif int_value not in self._value_set:
            msg = self.build_message('not_in_value_set',
                                        new_value=int_value)
            raise UnMatchedValuesError(msg)
        else:
            self._value_set.remove(item)

    def check_validity(self, value)->bool:
        '''Check that value is an integer and is a member of the value set, or
        within the minimum to maximum range, if specified.
        If the value is not valid the status attribute is set with the error
        message describing the reason the value is not valid.
        Arguments:
            value {int} -- The value to be tested.
        Returns
            True if the value is valid, False otherwise.
        '''
        # Test for integer as float or string
        try:
            int_value = self.int_value(value)
        except NotValidError:
            msg = self.build_message('not_valid', new_value=value)
            self.status = NotValidError(msg)
            return False
        if not super().check_validity(int_value):
            return False
        # Test integer values
        if self._value_set and (int_value not in self._value_set):
            msg = self.build_message('disp_value_set', new_value=value)
            self.status = NotValidError(msg)
            return False
        elif (self.max_value is not None) and (int_value > self.max_value):
            msg = self.build_message('too_high', new_value=value)
            self.status = NotValidError(msg)
            return False
        elif (self.min_value is not None) and (int_value < self.min_value):
            msg = self.build_message('too_low', new_value=value)
            self.status = NotValidError(msg)
            return False
        return True

    def set_value(self, value):
        '''Set a new value for CustomVariable.
        '''
        try:
            int_value = self.int_value(value)
        except NotValidError:
            msg = self.build_message('not_valid', new_value=value)
            self.status = NotValidError(msg)
            raise self.status
        super().set_value(int_value)

    def initialize_messages(self, messages: Dict[str, str]):
        '''Update message templates.
        Arguments:
            length -- A dictionary of message templates referencing
                IntegerV attributes.
        '''
        message_templates = dict(
            too_high='{new_value} is greater than the maximum allowable '
                     'value of {max_value}.',
            too_low='{new_value} is less than the minimum allowable '
                     'value of {min_value}.',
            disp_value_set='{new_value} is an invalid value for {name}.'
                           '\n\tPossible values are: {value_set}',
            not_in_value_set='{new_value} is not in the set of possible '
                             'values:\n\t{value_set}',
            value_conflict='{value} cannot be removed from the list of '
                           'possible values because it is the current value',
            limit_conflict='new {limit_type} value of {limit_value} is '
                               '{direction} than the current {conflict_type}: '
                               '{value}.\n\t'
                               'The {limit_type} value was not changed.',
            value_set='\n\tPossible values are:\t{value_set}',
            max_value='\n\tThe maximum allowable value is: {max_value}',
            min_value='\n\tThe minimum allowable value is: {min_value}'
            )
        if messages:
            message_templates.update(messages)
        super().initialize_messages(message_templates)

    def build_message(self, message: str, **value_set)->str:
        '''Return a message string using format and a message template.
        if message is a key in self.messages use the corresponding template,
        otherwise treat message as a template.
        Arguments:
            message {str} -- Either a key in self.messages, or
                a custom message template.
            value_set {dict} -- value definition overrides for the message
                templates.
        '''
        values = {'max_value': self.max_value, 'min_value': self.min_value,
                  'value_set': self.value_set}
        values.update(value_set)
        return super().build_message(message, **values)

    def disp(self)->str:
        '''A template formatted string
        '''
        disp_str = super().disp()
        if self._value_set is not None:
            disp_str = disp_str + self.build_message('value_set')
        else:
            if self.max_value is not None:
                disp_str = disp_str + self.build_message('max_value')
            if self.min_value is not None:
                disp_str = disp_str + self.build_message('min_value')
        return disp_str


class PathV(CustomVariable):
    '''A File or Directory CustomVariable with:
    Optional limited File Types (file_types),
    Optional Base directory for building the full path (base_directory),
    Option to allow non-existing File or Directory paths (must_exist),
    Optional nickname for a top portion of the full path (top_path_name),
    '''
    # TODO Add disp method that uses the nickname
    _name = 'path_variable'
    _type = Path
    initial_settings = {'default': Path.cwd()}

    def __init__(self, *args, file_types: List[str] = None,
        base_directory: Path = None, must_exist=True, **kwds):
        '''Create a new instance of the path CustomVariable.
        '''
        self._value = None # type Path
        self.must_exist = must_exist # type bool
        if file_types:
            self._file_types = FileTypes(file_types)
        else:
            self._file_types = FileTypes('All Files')
        if base_directory:
            self.base_directory = base_directory
        else:
            self.base_directory = set_base_dir()
        super().__init__(*args, **kwds)

    def get_types(self)->List[str]:
        '''Return the file categories selected.
        Extract and return the names of the file types in use.
        '''
        type_names = [type_set[0] for type_set in self._file_types]
        return type_names

    def set_types(self, file_types: List[str]):
        '''Define the valid file types.
        Create a FileTypes instance defining valid file types.
        Args:
            file_types (List[str]): The list of valid file types.
        '''
        self._file_types = FileTypes(file_types)

    file_types = property(get_types, set_types)

    def add_type(self, file_type: str):
        '''Add a new type to the set of valid file types.
        Args:
            file_types (str): The new file type to add.
        '''
        current_types = set(self.file_types)
        new_type_set = current_types.add(file_type)
        self._file_types = FileTypes(new_type_set)

    def drop_type(self, file_type: str):
        '''Drop the file type if it exists.
        Args:
            file_types (str): The file type to drop.
        '''
        current_types = set(self.file_types)
        new_type_set = current_types.discard(file_type)
        self._file_types = FileTypes(new_type_set)

    @property
    def type_list(self)->Set[str]:
        '''Return a set of valid file suffixes.
        '''
        return self._file_types.type_select

    def check_validity(self, value: PathInput)->bool:
        '''Check that value produces a valid path.
        Test whether value can be built into a valid path.
        If the value cannot be built into a valid path the status attribute
        is set with the error message describing the reason the value is not
        valid.
        Arguments:
            value {Path, str} -- The value to be tested.
        Returns
            True if the value is valid, False otherwise.
        '''
        try:
            make_full_path(value, self._file_types, self.must_exist,
                           self.base_directory)
        except (FileTypeError, FileNotFoundError) as err:
            self.status = err
            return False
        return True

    def set_value(self, value):
        '''Set a new value for CustomVariable.
        '''
        try:
            path_value = make_full_path(value, self._file_types,
                                        self.must_exist,
                                        self.base_directory)
        except (FileTypeError, FileNotFoundError) as err:
            self.status = err
            raise self.status
        super().set_value(path_value)

class BoolV(CustomVariable):
    '''A True/False CustomVariable.
    BoolV can be customized to recognize additional true/false inputs:
    By default, it recognizes:
        'YES', 'Y', 'TRUE', 'T', 1 as True
        'NO', 'N', 'FALSE', 'F', 0, -1 as False
    '''
    _name = 'bool_variable'
    _type = bool
    initial_settings = {
        'default': True,
        'truth_values': {'YES', 'Y', 'TRUE', 'T', '1'},
        'false_values': {'NO', 'N', 'FALSE', 'F', '0', '-1'}
        }

    def __init__(self, *args, truth_values: Set[str] = None,
                 false_values: Set[str] = None, **kwds):
        '''Create a new instance of the bool CustomVariable.
        '''
        self._value = None # type Path
        super().__init__(*args, **kwds)
        if truth_values:
            self.truth_values = truth_values
        if false_values:
            self.false_values = false_values

    def check_validity(self, value: Any)->bool:
        '''Check that value produces a valid boolean.
        If the value cannot be built into a valid boolean, the status
        attribute is set with the error message describing the reason the
        value is not valid.
        Arguments:
            value {Any} -- The value to be tested.
        Returns
            True if the value is valid, False otherwise.
        '''
        try:
            logic_match(value, self.truth_values, self.false_values)
        except (TypeError) as err:
            self.status = err
            return False
        return True

    def set_value(self, value):
        '''Set a new value for CustomVariable.
        '''
        try:
            bool_value = logic_match(value, self.truth_values,
                                                          self.false_values)
        except (TypeError) as err:
            self.status = err
            raise err
        super().set_value(bool_value)

    def initialize_messages(self, messages: Dict[str, str]):
        '''Update message templates.
        Arguments:
            messages -- A dictionary of message templates referencing
                StringV attributes.
        '''
        message_templates = dict(
            truth_values='Input values that return True are:'
                         '\n\t{truth_values}.',
            false_values='Input values that return False are:'
                         '\n\t{false_values}.'
            )
        if messages:
            message_templates.update(messages)
        super().initialize_messages(message_templates)

    def disp(self)->str:
        '''A template formatted string
        '''
        value_str = super().disp()
        disp_str = value_str + self.build_message('truth_values') + '\n'
        disp_str = disp_str + self.build_message('false_values')
        return disp_str



class CustomVariableSet(OrderedDict):
    '''This defines a collection of custom variables.
        For each CustomVariable the following instance attributes are added:
            required (bool): True if the CustomVariable is required. Default is True
            on_update (method):  Method of the CustomVariableSet SubClass to execute
                when the CustomVariable is updated. Default is None.

        New CustomVariable sets can be defined as a combination of other
        CustomVariableSet subclasses
        The  CustomVariableSet subclasses being combined must not contain
        custom variables with the same name.

        A new CustomVariableSet class can be defined dynamically by passing an
        existing class a list of CustomVariables.  For a CustomVariableSet subclass,
        the new class will be an extension of the exiting class with the new
        CustomVariable definitions.

        Can access individual custom variables as items of the CustomVariable set
    '''
    variable_definitions = list() # type: List[Dict[str, Any]]
    defaults = {'required': True, 'on_update': None}
    logger = logging_tools.config_logger()
    def __init__(self, variable_definitions: List[Dict[str, Any]] = None, **variable_values):
        '''Create a new instance of the CustomVariableSet.
         Arguments:
            variable_definitions (optional, List[Dict[str, Any]] ) -- A list of variable definitions.
                 Each VariableDefinition must be a dictionary that contains either the key: 'name' - the name of the new Variable; or the : 'test_string1',
         'variable_type': StringV,
         'default': 'default_value',
         'required': False},
         {'CustomVariable': test_int,  'required': True}
        ]
            variable_values {dict} -- The keys are CustomVariable names,
                The values are dictionaries containing one or more of the
                CustomVariable's attribute values to set.
                Any keys not matching a CustomVariable name are added as .
                variable_definitions = [
        {'name': 'test_string1',
         'variable_type': StringV,
         'default': 'default_value',
         'required': False},
         {'CustomVariable': test_int,  'required': True}
        ]

       '''
       #FIXME add ability to pass new variable definitions to init
       #FIXME variable_values should only pass values and not set other attributes
        super().__init__()
#append passed variable definitions to class variable definition and pass to define_variables
        self.define_variables()
        remaining_items = self.initialize_variables(variable_values)
        self.update(remaining_items)

    def define_variables(self):
        '''Insert the CustomVariable class definitions.
        '''
        for variable_def in self.variable_definitions:
            local_variable_def = self.defaults.copy()
            local_variable_def.update(variable_def)
            logging_tools.log_dict(self.logger, local_variable_def, 'local_variable_def')
            if 'CustomVariable' in local_variable_def:
                new_variable = local_variable_def.pop('CustomVariable')
                new_variable.set_attributes(**local_variable_def)
            else:
                var_type = local_variable_def.pop('variable_type')
                logging_tools.log_dict(self.logger, local_variable_def, 'variable attributes')
                new_variable = var_type(**local_variable_def)
            self[new_variable.name] = new_variable

    def initialize_variables(self, variable_values: dict)->dict:
        '''set initial values for parameters.
        Arguments:
            variable_values {dict} -- The keys are CustomVariable names,
                The values are dictionaries containing one or more of the
                CustomVariable's attribute values to set.
                Any keys not matching a CustomVariable name are returned.
        Returns:
            dict -- The remaining items in parameter_values that do not
                correspond to a defined CustomVariable
        '''
        logging_tools.log_dict(self.logger, variable_values, 'variable_values')
        local_values_def = variable_values.copy()
        for variable_name in self.keys():
            if variable_name in local_values_def:
                new_value = local_values_def.pop(variable_name)
                self[variable_name].value = new_value
            elif (self[variable_name].required and not
                    self[variable_name].is_initialized() and
                    self[variable_name].default is None):
                msg = 'The variable: {} is required, but was not initialized.'.format(variable_name)
                raise MissingRequiredError(msg)
        return local_values_def

    def update_variables(self, variable_attr: dict):
        '''Update CustomVariable attributes.
        Arguments:
            variable_attr {dict} -- The keys are CustomVariable names,
                The values are dictionaries containing one or more of the
                CustomVariable's attribute values to set.
        '''
        for variable_name, attribute_def in variable_attr.keys():
            if variable_name in self:
                self[variable_name].set_attributes(attribute_def)
            else:
                msg = '{} is not a valid CustomVariable name'.format(variable_name)
                raise NoVariableError(msg)

    def to_dict(self)->dict:
        '''Return a dictionary with items corresponding to all initialized
        variables and default values for any required variables
        Returns:
            dict -- All items corresponding to all initialized variables and
                the default values for any non-initialized required variables.
        '''
        values_dict = dict()
        for name, variable in self.items():
            if not issubclass(type(variable), CustomVariable):
                values_dict[name] = variable
            elif variable.is_initialized():
                values_dict[name] = variable.value
            elif variable.required:
                values_dict[name] = variable.value
        return values_dict

    def get_values(self, selection: VariableSelection)->VariableValues:
        '''Return the values of the requested variables
        Arguments:
            selection {VariableSelection} -- can be one of:
                String: The name of a CustomVariable in the CustomVariableSet.
                List: A list of CustomVariable names
                Dictionary: Containing at least one key matching a
                    CustomVariable name
        Returns:
            Value of the requested CustomVariable
            List of values for the list of CustomVariable names
            The dictionary passed to get_values where for each key matching a
                CustomVariable name the value is replaced with the CustomVariable value;
                All non matching items remain unchanged
        Raises:
            NoVariableError:
                If the String does not correspond to a CustomVariable,
                If any of the names in the list don't match a CustomVariable name,
                If no dictionary key matches a CustomVariable name.
        '''
        return_values = None
        if isinstance(selection, str):
            if selection in self:
                return_values = self[selection].value
            else:
                raise NoVariableError(
                    '{} is not a valid CustomVariable name'.format(selection))
        elif isinstance(selection, dict):
            values_dict = selection.copy()
            found_variable = False
            for key in selection.keys():
                try:
                    item_value = self[key].value
                except KeyError:
                    continue
                except AttributeError:
                    item_value = self[key]
                else:
                    values_dict[key] = item_value
                    found_variable = True
            if not found_variable:
                raise NoVariableError(
                    'No CustomVariable was found in {}'.format(str(selection)))
            else:
                return_values = values_dict
        else:
            values_list = list()
            for name in selection:
                if name in self:
                    values_list.append(self[name].value)
                else:
                    raise NoVariableError(
                        '{} is not a valid CustomVariable name'.format(selection))
            return_values = values_list
        return return_values

    def set_values(self, *value_set, **variable_values):
        '''Set the values of parameters.
        Args:
            variable_values (dict): Defines the parameters and the values
                to set.
                The key is the name of the CustomVariable and the value is its new
                value.
        Raises:
            UnMatchedValuesError:
                If the number of values given does not match the number of CustomVariables
            NotVariableError: If any key in parameter_values does not
                correspond to a CustomVariable in the set.
        '''
        if value_set:
            self.logger.debug('value_set: %s', value_set)
            if len(value_set) == len(self):
                for parameter_name, new_value in zip(self.keys(), value_set):
                    self[parameter_name].value = new_value
            else:
                msg_template = 'Expected {} values, got {} values.'
                msg = msg_template.format(len(self), len(value_set))
                raise UnMatchedValuesError(msg)
        elif variable_values:
            for name, value in variable_values.items():
                if name in self:
                    self[name].value = value
                else:
                    msg = '{} is not contained in the CustomVariable Set'
                    msg_str = msg.format(name)
                    raise NotVariableError(msg_str)

    def drop(self, *variable_names: Tuple[str]):
        '''Set a CustomVariable to its uninitialized state.
        Arguments:
            variable_names {str} -- The name of the CustomVariable
        '''
        for variable_name in variable_names:
            if variable_name in self:
                self[variable_name].drop_value()
            else:
                msg = '{} is not contained in the CustomVariable Set'
                msg_str = msg.format(variable_name)
                raise NotVariableError(msg_str)

    def extract_set(self, set_type: type):
        '''extract a sub-CustomVariable set.
        Arguments:
            set_type {type} -- One or more CustomVariableSet class(es) or
                                instance(s)
        Returns
            Extracted CustomVariable set instance(s)
            Remainder CustomVariableSet
                (does not need to match a defined class, but update methods
                that call missing variables will raise errors)
        '''
        pass

    @classmethod
    def add_variable(cls, variable_definitions):
        '''Return new CustomVariable Set class, by extending the current one with
        additional variables
           If called from an instance, return an instance of the new class
           rather than the class
        Arguments:
            variable_definitions {[type]} -- [description]
        '''
        pass

'''Parameter objects with defined validity conditions and defaults.
'''

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Optional, List, Dict, Tuple, Set, Iterable, Any, Union
import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
# pylint: disable=invalid-name
ParameterSelection = Union[str, List[str], Dict[str, Any]]
ParameterValues = Union[Any, List[Any], Dict[str, Any]]
ErrorString = Optional[str]
IntValue = Union[str, float, int]


class ParameterError(Exception):
    '''Base Exception for Parameters
    '''
    pass


class NotValidError(ParameterError):
    '''Base Exception for invalid parameter value
    '''
    pass


class NotParameterError(ParameterError):
    '''The class does not inherit from the Parameter class
    '''
    pass


class NoParameterError(ParameterError):
    '''The value request from the parameter set did not contain a valid
    parameter name.
    '''
    pass


class UnMatchedValuesError(ParameterError):
    '''The list of values does not match with the expected number of values.
    '''
    pass


class UpdateError(ParameterError):
    '''An error occurred attempting to modify a parameter attribute.
    '''
    pass


def get_class_name(class_type: type)->str:
    '''parse the full class type string to get the abbreviated class name.
    It expects the class string to be in the form:
    "<class '__module__.ClassName'>"
    '''
    full_class_name = str(class_type)
    name_portion = full_class_name.replace("<class '", "").replace("'>", "")
    class_name = name_portion.rsplit('.', 1)[-1]
    return class_name


class Parameter(ABC):
    '''This is an abstract base class for all of the parameter sub-classes.
    '''
    _type = object
    initial_settings = dict(default=None)

    @abstractmethod
    def __init__(self, value=None, name=None, messages=None, **kwds):
        '''Create a new instance of the Parameter object.'''
        super().__init__()
        self.initialized = False
        self._value = None
        self.default = None
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
        '''Return the name of the parameter.
        '''
        return self._name

    name = property(get_name)

    def get_type(self):
        '''Return the name of the parameter.
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
            display='{name} parameter of class {cls},\n'
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
    def check_validity(self, value):
        '''Test to see if value is a valid parameter value.
        If valid return None.
        If not valid, return the name if the error message template to use.
        '''
        if isinstance(value, self.value_type):
            return None
        return 'not_valid'

    def get_value(self):
        '''Return the set value of the parameter.
        If no value is defined return the default value.
        '''
        if self._value is None:
            if self.default is None:
                return None
            return self.value_type(self.default)
        return self.value_type(self._value)

    def set_value(self, value):
        '''Set a new value for parameter.
        '''
        error_message = self.check_validity(value)
        if error_message is None:
            self._value = self._type(value)
            self.initialized = True
        else:
            msg = self.build_message(error_message, new_value=value)
            raise NotValidError(msg)

    value = property(get_value, set_value)

    def copy(self):
        '''Duplicate the parameter including all relevant attributes
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
        if self.check_validity(value) is None:
            return self.get_value() == value
        return False

    def reset_value(self):
        '''Set parameter to it's default value.'''
        self._value = self.default

    def drop_value(self):
        '''Set parameter to it's default value.'''
        self._value = None
        self.initialized = False

    def set_default(self, value=None):
        '''set the default value of Parameter to the supplied "value".
        if no value is supplied set the default to the current value of the
        parameter.
        '''
        if value is None:
            self.default = self._value
        else:
            error_message = self.check_validity(value)
            if error_message is None:
                self.default = value
            else:
                msg = self.build_message(error_message, new_value=value)
                raise NotValidError(msg)

    def is_initialized(self):
        '''Test whether a value has been explicitly assigned to the parameter
        '''
        return self.initialized


class StringP(Parameter):
    '''A String Parameter with:
        Optional limited values (value_set), or
        Optional size limit (max_length)
        If value_set is defined, the size limit will not be checked.
    '''
    _name = 'string_parameter'
    _type = str

    def __init__(self, *args, value_set=None, max_length=None, **kwds):
        '''Create a new instance of the string parameter.
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
        error_message = super().check_validity(item)
        if error_message is None:
            self._value_set.add(item)
        else:
            msg = self.build_message(error_message, new_value=item)
            raise NotValidError(msg)

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

    def check_validity(self, value)->ErrorString:
        '''Check that value is a string.
        Arguments:
            value {str} -- The value to be tested.
        Returns
            The error message describing the reason the value is not valid, or
            None - if the value is valid.
        '''
        error_message = super().check_validity(value)
        if error_message is None:
            if self._value_set:
                if value not in self._value_set:
                    error_message = 'disp_value_set'
            elif ((self._max_length is not None) and
                  (len(value) > self._max_length)):
                error_message = 'too_long'
        return error_message

    def initialize_messages(self, messages: Dict[str, str]):
        '''Update message templates.
        Arguments:
            messages -- A dictionary of message templates referencing
                StringP attributes.
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


class IntegerP(Parameter):
    '''An Integer Parameter with optional:
        maximum and minimum values (max_value, min_value), or
        a limited set of values (value_set)
    If value_set is defined, the max_value and min_value will not be checked.
    '''
    _name = 'integer_parameter'
    _type = int

    def __init__(self, *args, value_set=None, min_value=None, max_value=None,
                 **kwds):
        '''Create a new instance of the integer parameter.
        If both value and value_set are given, include value in the value set.
        '''
        self._value = None # type int
        self._min_value = None # type int
        self._max_value = None # type int
        self._value_set = set() # type: Set[int]
        super().__init__(*args, **kwds)
        if value_set is not None:
            self.add_items(*value_set) # FIXME change back
            if self._value is not None and self._value not in self.value_set:
                self.add_items(self._value)
        if min_value is not None:
            self._min_value = min_value
        if max_value is not None:
            self._max_value = max_value

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

    def get_min_value(self):
        '''Getter for min_value.'''
        return self._min_value

    def set_min_value(self, limit: int = None):
        '''If valid, change the minimum value.
        Arguments:
            limit {int} -- The new minimum value.
        '''
        # TODO Check for minimum greater than maximum
        if limit is None:
            self._min_value = None
        else:
            min_value = self.int_value(limit)
            if (self.value is None) or (min_value <= self.value):
                self._min_value = min_value
            else:
                msg = self.build_message('length_conflict',
                                         min_value=min_value)
                raise UpdateError(msg)

    min_value = property(get_min_value, set_min_value)

    def get_max_value(self):
        '''Getter for max_value.'''
        return self._max_value

    def set_max_value(self, limit: int = None):
        '''If valid, change the maximum value.
        Arguments:
            limit {int} -- The new maximum value.
        '''
        # TODO Check for maximum less than minimum
        if limit is None:
            self._max_value = None
        else:
            max_value = self.int_value(limit)
            if (self.value is None) or (max_value >= self.value):
                self._max_value = max_value
            else:
                msg = self.build_message('length_conflict',
                                         max_value=max_value)
                raise UpdateError(msg)

    max_value = property(get_max_value, set_max_value)

    def get_value_set(self):
        '''Getter for value_set.'''
        return self._value_set

    value_set = property(get_value_set)

    def add_items(self, *items): # FIXME Need to check for itterator
        '''Add additional items to the set of possible values.
        Arguments:
            items{int, List[int]} -- The items to add to the list of valid
                integer values
        '''
        item_list = list(items)
        for item in item_list:
            error_message = super().check_validity(item)
            if error_message is None:
                int_item = self.int_value(item)
                self._value_set.add(int_item)
            else:
                msg = self.build_message(error_message, new_value=item)
                raise NotValidError(msg)

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

    def check_validity(self, value)->ErrorString:
        '''Check that value is an integer and is a member of the value set, or
        within the minimum to maximum range, if specified.
        Arguments:
            value {int} -- The value to be tested.
        Returns
            The error message describing the reason the value is not valid, or
            None - if the value is valid.
        '''
        # Test for integer as float or string
        try:
            int_value = self.int_value(value)
        except NotValidError:
            error_message = 'not_valid'
        else:
            error_message = super().check_validity(int_value)
        # Test integer values
        if error_message is None:
            if self._value_set and (int_value not in self._value_set):
               error_message = 'disp_value_set'
            elif (self.max_value is not None) and (int_value > self.max_value):
                error_message = 'too_high'
            elif (self.min_value is not None) and (int_value < self.min_value):
                error_message = 'too_low'
        return error_message

    def set_value(self, value):
        '''Set a new value for parameter.
        '''
        int_value = self.int_value(value)
        super().set_value(int_value)

    def initialize_messages(self, messages: Dict[str, str]):
        '''Update message templates.
        Arguments:
            length -- A dictionary of message templates referencing
                IntegerP attributes.
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
            max_limit_conflict='new maximum value of {max_value} is less '
                               'than the current value: {value}.'
                               '\n\tmax_value was not changed.',
            min_limit_conflict='new minimum value of {min_value} is less '
                               'than the current value: {value}.'
                               '\n\tmin_value was not changed.',
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




class ParameterSet(OrderedDict):
    '''This defines a collection of parameters.
        For each parameter the following instance attributes are added:
            required (bool): True if the parameter is required. Default is True
            on_update (method):  Method of the ParameterSet SubClass to execute
                when the parameter is updated. Default is None.

        New Parameter sets can be defined as a combination of other
        ParameterSet subclasses
        The  ParameterSet subclasses being combined must not contain
        parameters with the same name.

        A new ParameterSet class can be defined dynamically by passing an
        existing class a list of Parameters.  For a ParameterSet subclass,
        the new class will be an extension of the exiting class with the new
        parameter definitions.

        Can access individual parameters as items of the parameter set
    '''
    parameter_definitions = list() # type: List[Dict[str, Any]]
    defaults = {'required': True,
                'on_update': None}

    def __init__(self, **parameter_values):
        '''Create a new instance of the ParameterSet.
        '''
        super().__init__()
        self.define_parameters()
        remaining_items = self.initialize_parameters(parameter_values)
        self.update(remaining_items)

    def define_parameters(self):
        '''Insert the parameter class definitions.
        '''
        for parameter_def in self.parameter_definitions:
            local_parameter_def = parameter_def.copy()
            self.add_defaults(local_parameter_def)
            if 'parameter' in local_parameter_def:
                new_parameter = local_parameter_def.pop('parameter')
            else:
                param_type = local_parameter_def.pop('parameter_type')
                new_parameter = param_type(**local_parameter_def)
            self[new_parameter.name] = new_parameter

    def add_defaults(self, parameter_def: dict)->dict:
        '''Add any missing default arguments to the parameter definition.
        Arguments:
            parameter_def {dict} -- [The attributes defining a parameter.]
        Returns:
            dict -- [The updated attributes including any missing default
                     values.]
        '''
        for attr_name, default_value in self.defaults.items():
            if attr_name not in parameter_def:
                parameter_def[attr_name] = default_value
        return parameter_def

    def initialize_parameters(self, parameter_values: dict)->dict:
        '''set initial values for parameters.
        Arguments:
            parameter_values {dict} -- The keys are parameter names,
                The values are dictionaries containing one or more of the
                parameter's attribute values to set.
                Any keys not matching a parameter name are returned.
        Returns:
            dict -- The remaining items in parameter_values that do not
                correspond to a defined parameter
        '''
        local_values_def = parameter_values.copy()
        for parameter_name in self.keys():
            if parameter_name in local_values_def:
                attribute_def = local_values_def.pop(parameter_name)
                self[parameter_name].set_attributes(**attribute_def)
            elif self[parameter_name].required:
                initial_value = self[parameter_name].default
                self[parameter_name].value = initial_value
        return local_values_def

    def update_parameters(self, parameter_attr: dict):
        '''Update parameter attributes.
        Arguments:
            parameter_attr {dict} -- The keys are parameter names,
                The values are dictionaries containing one or more of the
                parameter's attribute values to set.
        '''
        for parameter_name, attribute_def in parameter_attr.keys():
            if parameter_name in self:
                self[parameter_name].set_attributes(attribute_def)
            else:
                msg = '{} is not a valid Parameter name'.format(parameter_name)
                raise NoParameterError(msg)

    def to_dict(self)->dict:
        '''Return a dictionary with items corresponding to all initialized
        parameters and default values for any required parameters
        Returns:
            dict -- All items corresponding to all initialized parameters and
                the default values for any non-initialized required parameters.
        '''
        values_dict = dict()
        for name, parameter in self.items():
            if not issubclass(type(parameter), Parameter):
                values_dict[name] = parameter
            elif parameter.is_initialized():
                values_dict[name] = parameter.value
            elif parameter.required:
                values_dict[name] = parameter.value
        return values_dict

    def get_values(self, selection: ParameterSelection)->ParameterValues:
        '''Return the values of the requested parameters
        Arguments:
            selection {ParameterSelection} -- can be one of:
                String: The name of a parameter in the parameter set.
                List: A list of parameter names
                Dictionary: Containing at least one key matching a
                    parameter name
        Returns:
            Value of the requested parameter
            List of values for the list of parameter names
            The dictionary passed to get_values where for each key matching a
                parameter name the value is replaced with the parameter value;
                All non matching items remain unchanged
        Raises:
            NoParameterError:
                If the String does not correspond to a parameter,
                If any of the names in the list don't match a parameter name,
                If no dictionary key matches a parameter name.
        '''
        return_values = None
        if isinstance(selection, str):
            if selection in self:
                return_values = self[selection].value
            else:
                raise NoParameterError(
                    '{} is not a valid Parameter name'.format(selection))
        elif isinstance(selection, dict):
            values_dict = selection.copy()
            found_parameter = False
            for key in selection.keys():
                try:
                    item_value = self[key].value
                except KeyError:
                    continue
                except AttributeError:
                    item_value = self[key]
                else:
                    values_dict[key] = item_value
                    found_parameter = True
            if not found_parameter:
                raise NoParameterError(
                    'No Parameter was found in {}'.format(str(selection)))
            else:
                return_values = values_dict
        else:
            values_list = list()
            for name in selection:
                if name in self:
                    values_list.append(self[name].value)
                else:
                    raise NoParameterError(
                        '{} is not a valid Parameter name'.format(selection))
            return_values = values_list
        return return_values

    def set_values(self, *value_set, **parameter_values):
        '''Set the values of parameters.
        Args:
            parameter_values (dict): Defines the parameters and the values
                to set.
                The key is the name of the parameter and the value is its new
                value.
        Raises:
            NotParameterError: If any key in parameter_values does not
                correspond to a parameter in the set.
        '''
        if value_set:
            if len(value_set) == len(self):
                for parameter_name, new_value in zip(self.keys(), value_set):
                    self[parameter_name].value = new_value
            else:
                msg_template = 'Expected {} values, got {} values.'
                msg = msg_template.format(len(self), len(value_set))
                raise UnMatchedValuesError(msg)
        elif parameter_values:
            for name, value in parameter_values.items():
                if name in self:
                    self[name].value = value
                else:
                    msg = '{} is not contained in the Parameter Set'
                    msg_str = msg.format(name)
                    raise NotParameterError(msg_str)

    def drop(self, *parameter_names: Tuple[str]):
        '''Set a parameter to its uninitialized state.
        Arguments:
            parameter_name {str} -- The name of the parameter
        '''
        for parameter_name in parameter_names:
            if parameter_name in self:
                self[parameter_name].drop_value()
            else:
                msg = '{} is not contained in the Parameter Set'
                msg_str = msg.format(parameter_name)
                raise NotParameterError(msg_str)

    def extract_set(self, set_type: type):
        '''extract a sub-parameter set.
        Arguments:
            set_type {type} -- One or more ParameterSet class(es) or
                                instance(s)
        Returns
            Extracted parameter set instance(s)
            Remainder ParameterSet
                (does not need to match a defined class, but update methods
                that call missing parameters will raise errors)
        '''
        pass

    @classmethod
    def add_parameter(cls, parameter_definitions):
        '''Return new Parameter Set class, by extending the current one with
        additional parameters
           If called from an instance, return an instance of the new class
           rather than the class
        Arguments:
            parameter_definitions {[type]} -- [description]
        '''
        pass

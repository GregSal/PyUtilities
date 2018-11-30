'''Parameter objects with defined validity conditions and defaults.
'''

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import TypeVar, List, Dict, Tuple
import logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
# pylint: disable=invalid-name
ParameterSelection = TypeVar('ParameterSelection',
                             str, List[str], Dict[str, object]
                            )


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


def get_class_name(class_type: type)->str:
    '''parse the full class type string to get the abbreviated class name.
    It expects the class string to be in the form:
    "<class '__module__.ClassName'>"
    '''
    full_class_name = str(class_type)
    name_portion = full_class_name.replace("<class '","").replace("'>","")
    class_name = name_portion.rsplit('.',1)[-1]
    return class_name


class Parameter(ABC):
    '''This is an abstract base class for all of the parameter sub-classes.
    '''
    _type = object
    initial_settings = dict(default=None)
    initial_templates = dict(
        not_valid='{new_value} is an invalid value for {name}.',
        display='{name} parameter of class {cls}\n,'
                '\tCurrent Value is:\t{value}\n'
                '\tDefault value is \t{default}'
        )

    @abstractmethod
    def __init__(self, value=None, name=None, messages=None, **kwds):
        '''Create a new instance of the Parameter object.'''
        super().__init__()
        if name:
            self._name = name
        else:
            self._name = get_class_name(type(self))
        self.initialized = False
        self._value = None
        self.default = None
        self._messages = dict(not_valid='')
        self.initialize_attributes(kwds)
        self.initialize_messages(messages)
        if value is not None:
            self.set_value(value)

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
        message_templates = self.initial_templates.copy()
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
        If not valid, retrun the name if the error message template to use.
        '''
        if isinstance(value, self.value_type):
            return None
        else:
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
            self._value = value
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
    max_length = None
    value_set = set()

    def __init__(self, value=None, name=None, messages=None, **kwds):
        '''Create a new instance of the string parameter.
        '''
        string_messages = dict(
            too_long='{new_value} is longer than the maximum allowable '
                     'length of {max_length}.',
            disp_value_set=(
                '{value} is an invalid value for {name}.' +
                '\tPossible values are:\n\t{value_set_str}')
            )
        if messages:
            messages.update(string_messages)
        else:
            messages = string_messages
        super().__init__(value=value, name=name, messages=messages, **kwds)

    def check_validity(self, value)->bool:
        '''Check that value is a string.
        '''
        error_message = super().check_validity(value)
        if error_message is not None:
            return error_message
        elif self.value_set and value not in self.value_set:
            return 'not_valid'
        elif (self.max_length is not None) and (len(value) > self.max_length):
            return 'too_long'

    def add_item(self, item: str):
        '''Add additional items to the set of possible values.
        Arguments:
            item {str} -- The item to add to the list of valid string values
        '''
        pass

    def drop_item(self, item: str):
        '''Drop an item from the set of possible values.
        Arguments:
            item {str} -- The item to drop from the list of valid string values.
        '''
        pass

    def disp(self)->str:
        '''A template formatted string
        '''
        # TODO include max length and possible values in the display
        return super().disp()

class IntegerP(Parameter):
    '''An Integer Parameter with optional range limit (value_range)
    '''
    _name = 'integer_parameter'
    _type = int
    _range = None

    def __init__(self, **kwds):
        '''Create a new instance of the integer parameter.
        '''
        msg = '{new_value} is longer than the maximum allowable length '
        msg += 'of {max_length}.'
        if 'messages' in kwds:
            kwds['messages'].update({'too_long': msg})
        else:
            kwds['messages'] = dict(too_long=msg)
        super().__init__(**kwds)

    def get_value_range(self):
        '''Determine the range limit for the value.
        '''
        return self._range

    def set_value_range(self,
                        value_set: List[int]=None,
                        min_value: int=0,
                        max_value: int=None,
                        value_step: int=1):
        '''Set the range limits for the value
        Defines a range based on a set of integers or max and min limits.
            value_set (List[int], optional): Defaults to None.
                An itterable of integers defining the range of
                    acceptable values.
            min_value (int, optional): Defaults to 0.
                The minimum valid value.
            max_value (int, optional): Defaults to none.
                The maximum valid value.
            value_step (int, optional): Defaults to 1.
                The the step size for a range of valid values.
        If neither value_set nor max_value are given the range is set to None.
        '''
        if value_set is not None:
            if all(float(n).is_integer() for n in value_set):
                self._range = value_set
            else:
                msg_template = '{new_value} contains a non integer value.'
                msg = self.build_message(msg_template, new_value=value_set)
                raise NotValidError(msg)
        elif max_value is None:
            self._range =  None
        else:
            self._range = range(self.min_value,
                                self.max_value+1,
                                self.value_step)

    range = property(get_value_range, set_value_range)

    def check_validity(self, value)->bool:
        '''Check that value is a an integer in the defined range.
        '''
        error_message = super().check_validity(value)
        if error_message is not None:
            return error_message
        elif self.range is not None:
            if value not in self.range:
                return 'not_valid'
        elif (self.max_length is not None) and (len(value) <= self.max_length):
            return 'too_long'

    def disp(self)->str:
        '''A template formatted string
        '''
        # TODO include value range in the display
        return super().disp()


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
    parameter_definitions = list()
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

    def get_values(self, selection: ParameterSelection)->dict:
        '''Return the values of the requested parameters
        Arguments:
            selection {ParameterSelection} -- can be one of:
                String: The name of a parameter in the parameter set.
                List: A list of parameter names
                Dictionary: Containing at least one key matching a
                    parameter name
        Returns:
            Value of the requested parameter
            Tuple of values for the list of parameter names
            The dictionary passed to get_values where for each key matching a
                parameter name the value is replaced with the parameter value;
                All non matching items remain unchanged
        Raises:
            NoParameterError:
                If the String does not correspond to a parameter,
                If any of the names in the list don't match a parameter name,
                If no dictionary key matches a parameter name.
        '''
        if isinstance(selection, str):
            if selection in self:
                return self[selection].value
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
                return values_dict
        else:
            values_list = list()
            for name in selection:
                if name in self:
                    values_list.append(self[name].value)
                else:
                    raise NoParameterError(
                        '{} is not a valid Parameter name'.format(selection))
            return values_list

    def set_values(self, *value_set, **parameter_values):
        '''Set the values of parameters.
        Args:
            parameter_values (dict): Defines the parameters and the values
                to set.
                The key is the name of teh parameter and the value is its new
                value.
        Raises:
            NotParameterError: If any key in parameter_values does not
                correspond to a paremeter in the set.
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

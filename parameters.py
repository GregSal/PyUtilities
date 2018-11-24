'''Parameter objects with defined validity conditions and defaults.
'''

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import TypeVar, List, Dict
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


def get_class_name(class_type: type)->str:
    '''parse the full class type string to get the abbreviated class name.
    '''
    full_class_name = str(class_type)
    name_portion = full_class_name.rsplit('.', 1)[1]
    class_name = name_portion.rstrip('\'">')
    return class_name


class Parameter(ABC):
    '''This is an abstract base class for all of the parameter sub-classes.
    '''
    _type = object
    initial_settings = dict(default=None)
    initial_templates = dict(
        not_valid='{new_value} is an invalid value for {name}.',
        display='{name} parameter of class {cls_str}\n,'
                '\tCurrent Value is:\t{value_str}'
                '\tDefault value is \t{default}'
        )

    @abstractmethod
    def __init__(self, value=None, name='', messages=None, **kwds):
        '''Create a new instance of the Parameter object.'''
        super().__init__()
        if name:
            self.name = name
        else:
            self.name = get_class_name(type(self))
        self._value = None
        self.default = None
        self._messages = dict(not_valid='')
        self.initialize_attributes(kwds)
        self.update_messages(messages)
        if value is not None:
            self.set_value(value)

    def initialize_attributes(self, kwds):
        '''Add values for all attributes.
        '''
        settings = self.initial_settings.copy()
        settings.update(kwds)
        for attr, value in settings.items():
            self.__setattr__(attr, value)

    def set_attributes(self, **settings):
        '''Update values for the supplied attributes.
        '''
        for attr, value in settings.items():
            self.__setattr__(attr, value)

    def update_messages(self, messages: dict):
        '''Update message templates.
        '''
        message_templates = self.initial_templates.copy()
        if messages:
            message_templates.update(messages)
        self._messages.update(message_templates)

    def build_message(self, message: str, **value_set)->str:
        '''Return a message string using format and a message template.
        if message is a key in self.messages use the corresponding template,
        otherwise treat message as a template.
        '''
        values = self.__dict__
        values.update(value_set)
        msg = self._messages[message]
        msg_str = msg.format(**values)
        return msg_str

    @abstractmethod
    def isvalid(self, value):
        '''Test to see if value is a valid parameter value.
        In this template class all values are valid.
        '''
        return isinstance(value, self._type)

    def get_value(self):
        '''Return the sat value of the parameter.
        If no value is defined return the default value.
        '''
        if self._value is None:
            if self.default is None:
                return None
            return self._type(self.default)
        return self._type(self._value)

    def set_value(self, value):
        '''Set a new value for parameter.
        '''
        if self.isvalid(value):
            self._value = value
        else:
            msg = self.build_message('not_valid', new_value=value)
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
        disp_tmpl = self._messages['display']
        attrs = self.__dict__.copy()
        attrs['value_str'] = self.__str__()
        attrs['cls_str'] = get_class_name(type(self))
        disp_str = disp_tmpl.format(**attrs)
        return disp_str

    def __eq__(self, value):
        '''Test to see if self is set to "value".
        Equality is only based on value not on other attributes.
        '''
        if self.isvalid(value):
            return self.get_value() == value
        return False

    def reset_value(self):
        '''Set parameter to it's default value.'''
        self._value = self.default

    def set_default(self, value=None):
        '''set the default value of Parameter to the supplied "value".
        if no value is supplied set the default to the current value of the
        parameter.
        '''
        if value is None:
            self.default = self._value
        elif self.isvalid(value):
            self.default = value
        else:
            msg = self.build_message('not_valid', new_value=value)
            raise NotValidError(msg)

    def is_initialized(self):
        '''Test whether a value has been explicitly assigned to the parameter
        '''
        return self._value is not None


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
                self[parameter_name].set_attributes(attribute_def)
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
            elif parameter.is_initialized:
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

    def set_values(self, parameter_values: dict):
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
        for name, value in parameter_values.items():
            if name in self:
                self[name].value = value
            else:
                msg = '{} is not contained in the Parameter Set'
                msg_str = msg.format(name)
                raise NotParameterError(msg_str)

    def drop(self, parameter_name: str):
        '''Set a parameter to its uninitialized state.
        Arguments:
            parameter_name {str} -- The name of the parameter
        '''
        # TODO allow drop to accept a tuple of parameter names.
        if parameter_name in self:
            self[parameter_name].reset_value()
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

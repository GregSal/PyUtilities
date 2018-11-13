'''Parameter objects with defined validity conditions and defaults.
'''

from abc import ABC, abstractmethod
import logging
LOGGER = logging.getLogger(__name__)

class ParameterError(Exception):
    '''Base Exception for Parameters
    '''
    pass


class NotValidError(ParameterError):
    '''Base Exception for invalid parameter value
    '''
    pass


class Parameter(ABC):
    '''This is an abstract base class for all of the parameter sub-classes.
    '''
    _type = object
    initial_settings = dict(default=None)
    initial_templates = dict(
        not_valid='{new_value} is an invalid value for {name}.',
        display='{name} parameter of type {_type}\n\t Default value is {default}'
        )

    @abstractmethod
    def __init__(self, value=None, name='', messages=None, **kwds):
        '''Create a new instance of the Parameter object.'''
        super().__init__(**kwds)
        if name:
            self.name = name
        else:
            self.name = str(self.__class__)
        self._type = self.__class__._type
        self._value = None
        self.default = None
        self._messages = dict(not_valid=None)
        self.set_attributes(kwds)
        self.update_messages(messages)
        if value is not None:
            self.set_value(value)

    def set_attributes(self, kwds):
        '''Add values for all attributes.
        '''
        settings = self.initial_settings.copy()
        settings.update(kwds)
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

    def __copy__(self):
        '''Duplicate the parameter including all relevant attributes
        '''
        raise NotImplementedError

    def __repr__(self)->str:
        '''A representative string.
        '''
        raise NotImplementedError

    def __str__(self)->str:
        '''A string version of the value
        '''
        return str(self.get_value())

    def _disp(self)->str:
        '''A template formatted string
        '''
        return str(self.get_value())

    def __eq__(self, value):
        '''Test to see if self is set to "value".
        Equality is only based on value not on other aattributes.
        '''
        if self.isvalid(value):
            return self.get_value() == value
        return False

    def reset_value(self):
        '''Set parameter to it's default value.'''
        self._value = self.default

    def set_default(self, value=None):
        '''set the default value of Parameter to the supplied "value".
        if no value is supplied set the default to the current value of the parameter.
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

class ParameterInfo(dict):
    '''Contains the information required to define a parameter in a
        parameter set.
    The required information for each parameter is:
        name (str): Name of parameter
            Must be unique to that parameter set and any sub-sets
        parameter_class (type): The Parameter SubClass type
        required (bool): - optional Is the parameter. Default is True
        on_changed (method): - optional Method of ParameterSet or SubClass to
            run when the parameter is changed. Default is None.
    '''
    def __init__(self, **kwds):
        self.name = kwds['name']
        if issubclass(kwds['parameter_class'], Parameter):
            return super().__init__(kwds)

class ParameterSet(dict):
    '''This is the base class for parameter sets.
    The required information for each parameter is:
        name (str): Name of parameter
            Must be unique to that parameter set and any sub-sets
        class (type): The Parameter SubClass type
        required (bool): - optional Is the parameter. Default is True
        on_changed (method): - optional Method of ParameterSet or SubClass to
            run when the parameter is changed. Default is None.
    '''

    def __init__(self, **kwds):
        '''Create a new instance of the Parameter object.'''

        super().__init__(**kwds)
        if name:
            self.name = name
        else:
            self.name = str(self.__class__)
        self._type = self.__class__._type
        self._value = None
        self.default = None
        self._messages = dict(not_valid=None)
        self.set_attributes(kwds)
        self.update_messages(messages)
        if value is not None:
            self.set_value(value)

    def set_attributes(self, kwds):
        '''Add values for all attributes.
        '''
        settings = self.initial_settings.copy()
        settings.update(kwds)
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

    def __copy__(self):
        '''Duplicate the parameter including all relevant attributes
        '''
        raise NotImplementedError

    def __repr__(self)->str:
        '''A representative string.
        '''
        raise NotImplementedError

    def __str__(self)->str:
        '''A string version of the value
        '''
        return str(self.get_value())

    def _disp(self)->str:
        '''A template formatted string
        '''
        return str(self.get_value())

    def __eq__(self, value):
        '''Test to see if self is set to "value".
        Equality is only based on value not on other aattributes.
        '''
        if self.isvalid(value):
            return self.get_value() == value
        return False

    def reset_value(self):
        '''Set parameter to it's default value.'''
        self._value = self.default

    def set_default(self, value=None):
        '''set the default value of Parameter to the supplied "value".
        if no value is supplied set the default to the current value of the parameter.
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
